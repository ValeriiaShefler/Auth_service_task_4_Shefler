# Auth Service ShV

Микросервис для аутентификации и авторизации пользователей с использованием JWT-токенов

## О сервисе

Auth Service обеспечивает:  

    - Регистрацию и аутентификацию пользователей  
    - Выдачу JWT access и refresh токенов  
    - Обновление токенов  
    - Управление профилем пользователя  
    - Историю входов  
    - Безопасный выход из системы  

## Технологии

 Компонент | Технология | Назначение |
|-----------|------------|------------|
| API | FastAPI | Веб-фреймворк |
| JWT | python-jose | Создание и валидация токенов |
| Хеширование | bcrypt | Хеширование паролей |
| База данных | PostgreSQL 15 | Хранение пользователей и истории |
| Кэш | Redis 7 | Черный список токенов |
| Контейнеризация | Docker & Docker Compose | Окружение |

## Запуск

1. Клонируйте репозиторий себе на компьютер и перейдите в соответсвующую папку:  

    git clone https://github.com/ValeriiaShefler/Auth_service_task_4_Shefler  

2. Скопируйте пример конфигурации из .env.example в .env (измените параметры при необходимости):  

    cp .env.example .env  

3. Сгенерируйте JWT ключ и вставьте его в .env файл:

    python -c "import secrets; print(secrets.token_urlsafe(32))"
    SECRET_KEY=скопированный_сгенерированный_ключ_здесь  

4. Запустите с использованием docker-compose:

    docker-compose up --build  

5. В браузере откройте страницу http://localhost:8000/docs и теперь вы можете работать с запросами (альтернативно используйте curl-запросы):  

     Метод | Эндпоинт | Описание |
    |-----------|------------|------------|
    | POST | /auth/register | Регистрация пользователя |
    | POST | /auth/login | Вход в систему |
    | POST | auth/refresh | Обновление токенов |
    | GET | /user/me | Информация о пользователе |
    | PUT | /user/update | Обновление данных |
    | GET | /user/history | История входов |
    | POST | /auth/logout | ыход из системы |  

6. Альтернативный сценарий тестирования curl-запросами:  

    -- регистрация --  
        curl -X POST http://localhost:8000/auth/register \
            -H "Content-Type: application/json" \
            -d '{"email":"user@example.com","password":"123456"}'

    -- вход --  
        curl -X POST http://localhost:8000/auth/login \
            -H "Content-Type: application/json" \
            -d '{"email":"user@example.com","password":"123456"}' \
            -c cookies.txt

    -- получение информации о пользователе --  
        curl -X GET http://localhost:8000/user/me -b cookies.txt

    -- обновление токенов --  
        curl -X POST http://localhost:8000/auth/refresh \
            -H "Content-Type: application/json" \
            -d '{"refresh_token":"ваш_refresh_token"}'

    -- история входов --  
        curl -X GET http://localhost:8000/user/history -b cookies.txt  

    -- обновление данных --
        curl -X PUT http://localhost:8000/user/update \
            -H "Content-Type: application/json" \
            -d '{"email":"new@example.com"}' \
            -b cookies.txt

    -- выход из системы --  
        curl -X POST http://localhost:8000/auth/logout -b cookies.txt  

7. Завершить работу приложения можно командами docker-compose down (с созранением данных) и docker-compose down -v (с удалением данных)  

## Токены

Access токен  

    - Время жизни: 15 минут  
    - Назначение: Доступ к защищенным ресурсам  
    - Хранение: HttpOnly cookie (автоматически)  

Refresh токен  

    - Время жизни: 7 дней  
    - Назначение: Обновление access токена  
    - Передача: Только в теле запроса /refresh  

## Docker окружение  
 
| Контейнер | Образ | Порты | Назначение |
|-----------|------------|------------|------------|
| auth_db | postgres:15-alpine | 5432 | PostgreSQL база данных |
| auth_redis | redis:7-alpine | 6379 | Redis для черного списка |
 auth_app | custom | 8000 | FastAPI приложение |  

## Переменные окружения

    # PostgreSQL
    DB_HOST=db
    DB_PORT=5432
    DB_USER=postgres
    DB_PASSWORD=postgres
    DB_NAME=auth_db

    # Redis
    REDIS_HOST=redis
    REDIS_PORT=6379
    REDIS_DB=0

    # JWT (обязательно сгенерируйте свой ключ!)
    SECRET_KEY=your-generated-secret-key-here
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=15
    REFRESH_TOKEN_EXPIRE_DAYS=7  



