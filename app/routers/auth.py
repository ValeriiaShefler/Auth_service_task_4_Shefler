from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import User, LoginHistory
from app.schemas import UserRegister, UserLogin, TokenRefresh, TokenResponse, MessageResponse
from app.auth import (
    verify_password, get_password_hash, 
    create_access_token, create_refresh_token, decode_token
)
from app.redis_client import token_blacklist

router = APIRouter(prefix="/auth", tags=["Authentication"])


#aункция для установки cookies для автоматической подставноки в запросы
def set_token_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax"
    )

#очистка куки с токенами при выходе из системы
def clear_token_cookies(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


#функция для получения пользователя из cookie для использования в эндпоинтах
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

#регистрация нового пользователя
@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Данный email уже используется"
        )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return MessageResponse(message="Пользователь зарегистрирован")

#вход в систему, возвращает access и refresh токены и устанавливает cookies
@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверная почта или пароль"
        )
    
    #создаем токены
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token, jti = create_refresh_token(data={"sub": str(user.id)})
    
    # сохраняем refresh токен в Redis (задаем так странно, ведь он должен жить 7 дней, а задавать надо в секундах)
    expires_in = 7 * 24 * 60 * 60
    token_blacklist.add_active_refresh_token(user.id, jti, expires_in)
    
    #записываем историю входа
    user_agent = request.headers.get("user-agent", "Unknown")
    login_history = LoginHistory(
        user_id=user.id,
        user_agent=user_agent
    )
    db.add(login_history)
    db.commit()
    
    #устанавливаем cookies
    set_token_cookies(response, access_token, refresh_token)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    #Обновление access токена (принимает refresh токен ТОЛЬКО из тела запроса (игнорирует cookies)
    
    #валидируем refresh токен
    payload = decode_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный refresh токен"
        )
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный тип токена"
        )
    
    jti = payload.get("jti")
    user_id = payload.get("sub")
    
    if not user_id or not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверная структура токена"
        )
    
    #проверяем активность токена в Redis
    if not token_blacklist.is_refresh_token_active(int(user_id), jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh токен был отозван"
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    #создаем новые токены
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token, new_jti = create_refresh_token(data={"sub": str(user.id)})
    
    #удаляем старый refresh токен
    token_blacklist.add_to_blacklist(jti, 7 * 24 * 60 * 60)
    
    #сохраняем новый refresh токен
    expires_in = 7 * 24 * 60 * 60
    token_blacklist.add_active_refresh_token(user.id, new_jti, expires_in)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )

#выход из системы с удалением токена из списка действительных
@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    user = get_user_from_cookies(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизирован"
        )
    
    #добавляем access токен в черный список
    access_token = request.cookies.get("access_token")
    if access_token:
        payload = decode_token(access_token)
        if payload:
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                expires_in = max(exp - int(datetime.utcnow().timestamp()), 1)
                token_blacklist.add_to_blacklist(jti, expires_in)
    
    #удаляем все refresh токены пользователя
    token_blacklist.remove_user_refresh_tokens(user.id)
    
    #очищаем cookies
    clear_token_cookies(response)
    
    return MessageResponse(message="Вы вышли из системы")