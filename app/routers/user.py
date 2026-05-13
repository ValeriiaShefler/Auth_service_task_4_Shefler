from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, LoginHistory
from app.schemas import UserUpdate, UserResponse, LoginHistoryResponse, MessageResponse
from app.auth import get_password_hash, decode_token
from app.redis_client import token_blacklist

#создаем роутер с префиксом /user, при том все эндпоинты будут доступны по URL: /user/me, /user/update, /user/history
router = APIRouter(prefix="/user", tags=["User"])

# Функция для получения access токена из cookie, используется для упрощения части запросов (кроме рефреша)
def get_user_from_cookies(request: Request, db: Session):
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None
    
    payload = decode_token(access_token)
    if payload is None or payload.get("type") != "access":
        return None
    
    jti = payload.get("jti")
    if jti and token_blacklist.is_blacklisted(jti):
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    return user

#обновление даных пользователя
@router.put("/update", response_model=MessageResponse)
async def update_user(
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_user_from_cookies(request, db)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизирован"
        )
    
    if user_data.email:
        #проверяем, не занят ли новый email
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Данный email уже используется"
            )
        
        current_user.email = user_data.email
    
    if user_data.password:
        current_user.hashed_password = get_password_hash(user_data.password)
    
    db.commit()
    
    return MessageResponse(message="Данные пользователя обновлены")

#получение и вывод информации об истории входов пользователя
@router.get("/history", response_model=List[LoginHistoryResponse])
async def get_login_history(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = 50
):
    current_user = get_user_from_cookies(request, db)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизирован"
        )
    
    history = db.query(LoginHistory).filter(
        LoginHistory.user_id == current_user.id
    ).order_by(LoginHistory.datetime.desc()).limit(limit).all()
    
    return history

#получение инормации о текущем пользователе
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_user_from_cookies(request, db)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизирован"
        )
    
    return current_user