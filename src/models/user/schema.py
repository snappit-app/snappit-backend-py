from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base


class User(Base):
 __tablename__: str = "users"
 id: Mapped[int] = mapped_column(primary_key=True)
 email: Mapped[str] = mapped_column(String(255), unique=True)
 first_name: Mapped[str] = mapped_column(String(100))
 second_name: Mapped[str] = mapped_column(String(100))
 third_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
