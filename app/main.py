from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, user
from app.redis_client import redis_client
import logging

#создание таблиц в БД
Base.metadata.create_all(bind=engine)

# создание fastapi приложения
app = FastAPI(
    title="Auth Service ShV",
    description="Authentication and Authorization Service with JWT by SHefler",
    version="1.0.0"
)

# настройка CORS middleware для обращения к API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(user.router)

#проверка подключения Redis при запуске
@app.on_event("startup")
async def startup_event():
    try:
        redis_client.ping()
        logging.info("Successfully connected to Redis")
    except Exception as e:
        logging.error(f"Failed to connect to Redis: {e}")

#закрытие соединения с Redis
@app.on_event("shutdown")
async def shutdown_event():
    redis_client.close()

#проверка работы сервиса
@app.get("/health")
async def health_check():
    try:
        redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "redis": "disconnected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)