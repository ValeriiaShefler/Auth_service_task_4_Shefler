from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

#модели базы данных, в моем случае модель для пользователя и для истории его входов

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # зависимость один ко многим с историей входов
    login_histories = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")


class LoginHistory(Base):
    __tablename__ = "login_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_agent = Column(String(500), nullable=True)
    datetime = Column(DateTime(timezone=True), server_default=func.now())
    
    # зависимость многие к одному с пользователем
    user = relationship("User", back_populates="login_histories")
    
    #индекс для поиска ситории по пользователю и дате
    __table_args__ = (
        Index('ix_login_histories_user_id_datetime', 'user_id', 'datetime'),
    )