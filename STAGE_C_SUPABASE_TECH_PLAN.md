# Snappit Backend — Технический план этапа C (Paddle Webhook + Fulfillment) c Railway

## 1. Объем этапа C

Цель этапа C: сделать надежный backend-слой, который:

1. Принимает webhook от Paddle.
2. Гарантирует идемпотентность и устойчивость к retries/out-of-order.
3. Создает лицензию и код активации после `transaction.completed`.
4. Обрабатывает refund через `adjustment.updated`.
5. Отправляет email с кодом активации.
6. Дает API для активации/деактивации устройств (лимит 2).

## 2. Технические решения (фиксируем до начала работ)

1. **Backend:** NestJS (текущий `snappit-backend`).
2. **БД:** Railway Postgres (один источник истины).
3. **Очередь:** DB queue/outbox в Postgres на Railway (без Redis на MVP этапа C).
4. **ORM:** Prisma (быстрый старт + миграции + транзакции).
5. **Email provider:** Resend (или Postmark, интерфейс абстрагируется).
6. **Webhook verification:** Paddle SDK + `PADDLE_WEBHOOK_SECRET`.
7. **Хранение кода активации:** только hash (HMAC-SHA256 с `LICENSE_CODE_PEPPER`), plaintext отправляется только в email.

## 3. Что делаем внутри `snappit-backend`

## 3.1 Базовая инфраструктура проекта

1. Добавить модули:
   - `ConfigModule` (валидация env через zod/joi).
   - `PrismaModule`.
   - `PaddleWebhookModule`.
   - `FulfillmentWorkerModule`.
   - `LicensesModule`.
   - `EmailModule`.
   - `HealthModule`.

2. Добавить зависимости:
   - `@prisma/client`, `prisma`
   - `paddle-node-sdk` (или официальный актуальный SDK)
   - `@nestjs/schedule` (воркер polling outbox)
   - `resend` (или SDK выбранного провайдера)
   - `class-validator`, `class-transformer`
   - `helmet`, `@nestjs/throttler`, `pino`/`nestjs-pino`

3. Настроить `main.ts`:
   - raw body для `/api/paddle/webhook` (критично для подписи).
   - global validation pipe.
   - rate limit на публичные endpoints лицензирования.
   - request-id middleware для трассировки.

## 3.2 Схема данных (Railway Postgres)

Создать Prisma schema + SQL-миграции для таблиц:

1. `licenses`
   - `id uuid pk`
   - `activation_code_hash text unique not null`
   - `activation_code_last4 text not null`
   - `email text not null`
   - `status text not null check (status in ('active','revoked','refunded'))`
   - `max_devices int not null default 2`
   - `paddle_transaction_id text unique not null`
   - `paddle_customer_id text`
   - `last_event_occurred_at timestamptz`
   - `created_at`, `updated_at`

2. `license_activations`
   - `id uuid pk`
   - `license_id uuid fk -> licenses(id)`
   - `device_id_hash text not null`
   - `device_name text`
   - `platform text`
   - `app_version text`
   - `activated_at timestamptz not null`
   - `deactivated_at timestamptz null`
   - partial unique index: `(license_id, device_id_hash) where deactivated_at is null`

3. `webhook_events`
   - `id uuid pk`
   - `event_id text unique not null`
   - `notification_id text`
   - `event_type text not null`
   - `occurred_at timestamptz not null`
   - `status text not null check (status in ('pending','processing','processed','failed','ignored'))`
   - `payload jsonb not null`
   - `attempts int not null default 0`
   - `next_retry_at timestamptz`
   - `error_message text`
   - `processed_at timestamptz`
   - `created_at`, `updated_at`

4. `email_jobs`
   - `id uuid pk`
   - `template text not null`
   - `to_email text not null`
   - `payload jsonb not null`
   - `status text not null check (status in ('pending','processing','sent','failed'))`
   - `attempts int not null default 0`
   - `next_retry_at timestamptz`
   - `error_message text`
   - `sent_at timestamptz`
   - `created_at`, `updated_at`

5. `audit_logs`
   - `id uuid pk`
   - `action text not null`
   - `license_id uuid null`
   - `metadata jsonb not null`
   - `created_at timestamptz not null`

## 3.3 Webhook ingestion (`POST /api/paddle/webhook`)

1. Принять raw body + заголовок `Paddle-Signature`.
2. Верифицировать подпись через `PADDLE_WEBHOOK_SECRET`.
3. Извлечь `event_id`, `notification_id`, `event_type`, `occurred_at`.
4. Upsert в `webhook_events` (unique `event_id`).
5. **Всегда быстро вернуть `200`** (после успешной валидации и записи pending-события).
6. Ошибки валидации подписи -> `400`.

Принцип: endpoint ничего "тяжелого" не делает, только ingestion.

## 3.4 Фоновая обработка (fulfillment worker)

1. Воркер (каждые 5–10 секунд) берет `webhook_events.status='pending'` с `FOR UPDATE SKIP LOCKED`.
2. Обрабатывает типы:
   - `transaction.completed`
   - `adjustment.updated`
3. Логика `transaction.completed`:
   - проверить, что в line items есть нужный `price_id` (`PADDLE_PRICE_ID_FULL_LICENSE`).
   - если лицензия с `paddle_transaction_id` уже есть -> idempotent skip.
   - иначе:
     - сгенерировать activation code (`SNP-XXXX-XXXX-XXXX`).
     - вычислить `activation_code_hash`.
     - создать `licenses` со статусом `active`, `max_devices=2`.
     - создать `email_jobs` на отправку кода.
4. Логика `adjustment.updated`:
   - если `action=refund` и `status=approved`, найти лицензию по transaction/related id.
   - если событие свежее (`occurred_at >= last_event_occurred_at`) -> перевести в `refunded` или `revoked`.
   - активные устройства пометить `deactivated_at=now()`.
   - поставить email job о refund/revoke (опционально в этапе C, но желательно).
5. Retry policy:
   - exponential backoff (например 1m, 5m, 15m, 1h, 6h).
   - после N попыток -> `failed` + alert.

## 3.5 Email worker

1. Отдельный воркер читает `email_jobs.pending`.
2. Отправляет transactional email (template `activation-code`).
3. Фиксирует `sent`/`failed`, retries по backoff.
4. Идемпотентность: для "activation-code" использовать уникальный `message_key` (например `license_id + template`).

## 3.6 API лицензирования для `snappit-app`

Реализовать endpoints:

1. `POST /v1/licenses/activate`
   - input: `activationCode`, `deviceId`, `deviceName`, `platform`, `appVersion`
   - шаги:
     - hash(code) -> lookup лицензии
     - проверить `status='active'`
     - в транзакции:
       - если устройство уже активировано -> success idempotent
       - иначе count active devices
       - если `< max_devices` -> insert activation
       - иначе 409 `DEVICE_LIMIT_REACHED`
   - output: `licenseStatus`, `activeDevices`, `maxDevices`

2. `POST /v1/licenses/deactivate-device`
   - input: `activationCode`, `deviceId`
   - пометить `deactivated_at` для конкретного active устройства
   - output: актуальный список устройств

3. `GET /v1/licenses/devices`
   - input: `activationCode`
   - output: активные устройства

4. `POST /v1/licenses/validate` (рекомендуется в этом же этапе)
   - input: `activationCode`, `deviceId`
   - output: `active|revoked|refunded`, `graceUntil` (если вводится grace-policy)

## 3.7 Безопасность и эксплуатация

1. Rate limit на `/v1/licenses/*`.
2. Нормализованный error model (без утечек внутренних данных).
3. Логи:
   - `request_id`
   - `event_id`
   - `license_id`
4. Sentry/аналог для exception tracking.
5. Health checks:
   - `/health/live`
   - `/health/ready` (DB + email provider ping optional).

## 3.8 Тестирование в backend

1. Unit tests:
   - signature verification
   - activation code hashing
   - idempotent activation
   - refund status transitions

2. Integration tests:
   - webhook ingestion -> pending event
   - worker transaction.completed -> license + email_job
   - duplicate webhook event_id -> no duplicate
   - out-of-order `occurred_at` handling
   - device limit (1/2 ok, 3rd denied)

3. E2E (sandbox):
   - реальный Paddle sandbox webhook до staging URL.

## 4. Что нужно настроить снаружи проекта

## 4.1 Railway (Postgres + окружения)

1. Создать окружения `sandbox` и `live` (в одном Railway проекте или в двух отдельных проектах).
2. Поднять Postgres-сервис в каждом окружении.
3. Получить/настроить переменные:
   - `DATABASE_URL` (Prisma runtime + worker)
   - `DIRECT_URL` (опционально, отдельный direct URL для Prisma migrations)
4. Включить бэкапы/снапшоты для live и проверить restore-процедуру.
5. Настроить алерты и мониторинг БД (CPU, RAM, connections, storage).

## 4.2 Paddle

1. Создать sandbox/live продукты и цены.
2. Настроить webhook destinations:
   - sandbox: `https://api-sandbox.snappit.app/api/paddle/webhook`
   - live: `https://api.snappit.app/api/paddle/webhook`
3. Сохранить секреты:
   - `PADDLE_API_KEY`
   - `PADDLE_WEBHOOK_SECRET`
   - `PADDLE_PRICE_ID_FULL_LICENSE`
4. Проверить retry поведение и подпись на тестовом webhook.

## 4.3 Email provider (Resend/Postmark)

1. Подключить домен `mail.snappit.app` + SPF/DKIM/DMARC.
2. Создать API key:
   - `EMAIL_PROVIDER_API_KEY`
   - `EMAIL_FROM=Snappit <license@snappit.app>`
3. Подготовить шаблон письма активации и шаблон уведомления о refund/revoke.

## 4.4 Deploy/infra

1. Деплоить backend в Railway:
   - web service для API/webhook
   - worker process для обработки `webhook_events` и `email_jobs`
2. Настроить:
   - HTTPS
   - autoscaling (минимум 2 инстанса для live)
   - zero-downtime deploy
3. Привязать домены:
   - sandbox: `api-sandbox.snappit.app`
   - live: `api.snappit.app`
4. Пробросить переменные окружения по средам.
5. Открыть доступ Paddle к webhook endpoint (без auth, но с обязательной signature verification).

## 5. Переменные окружения (минимум)

```env
NODE_ENV=development
PORT=3000

DATABASE_URL=
DIRECT_URL=

PADDLE_ENV=sandbox
PADDLE_API_KEY=
PADDLE_WEBHOOK_SECRET=
PADDLE_PRICE_ID_FULL_LICENSE=

LICENSE_CODE_PEPPER=
DEVICE_ID_PEPPER=

EMAIL_PROVIDER=resend
EMAIL_PROVIDER_API_KEY=
EMAIL_FROM=Snappit <license@snappit.app>

APP_BASE_URL=https://api-sandbox.snappit.app
LANDING_BASE_URL=https://sandbox.snappit.app
```

## 6. Порядок реализации (рекомендуемый)

1. Завести Railway Postgres и миграции Prisma.
2. Реализовать webhook ingestion + signature verification.
3. Реализовать fulfillment worker и генерацию лицензии.
4. Подключить email jobs + email worker.
5. Реализовать API `/v1/licenses/*`.
6. Закрыть тесты (unit + integration + sandbox e2e).
7. Подключить мониторинг/алерты.

## 7. Definition of Done для этапа C

1. Webhook `transaction.completed` создает лицензию ровно один раз при любом количестве retries.
2. Пользователь получает email с activation code.
3. API активации ограничивает 2 устройства и поддерживает идемпотентность.
4. Refund (`adjustment.updated: approved`) переводит лицензию в `refunded/revoked`.
5. Все критичные сценарии покрыты тестами и прогнаны на Paddle sandbox.
