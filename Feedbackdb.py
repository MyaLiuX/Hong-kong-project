from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

db = SQLAlchemy()

class Feedback(db.Model):
    __tablename__ = 'feedbacks'

    id: Mapped[int] = mapped_column(primary_key=True)
    point: Mapped[str] = mapped_column(nullable=False)
    dimension: Mapped[str] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)