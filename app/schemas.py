from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

#данный файл нужен для валидации запросов

#регистрация нового пользователя
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

#аутентификация пользователя
class UserLogin(BaseModel):
    email: EmailStr
    password: str

#обновление access токена
class TokenRefresh(BaseModel):
    refresh_token: str

# обновление данных пользователя
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=128)

#хема ответа с JWT токенами при успешном входе или обновлении токенов
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

#ответ с историей входов пользователей
class LoginHistoryResponse(BaseModel):
    id: int
    user_agent: Optional[str]
    datetime: datetime
    
    class Config:
        from_attributes = True

#ответ с информацией о пользователе
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    
    class Config:
        from_attributes = True #поддержка SQLAlchemy ORM

#универсальная схема ответа
class MessageResponse(BaseModel):
    message: str