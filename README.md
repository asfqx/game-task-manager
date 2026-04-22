# Game Task Manager

Game Task Manager - таск-менеджер с командной работой и элементами геймификации. В системе можно создавать проекты и команды, назначать задачи, переводить их по статусам, начислять XP за выполненную работу и отслеживать прогресс участников по уровням. Доступна страница с аналитикой по выполненным и невыполненным задачам

## Возможности

- Регистрация, вход, подтверждение email и восстановление пароля.
- Проекты, команды, тимлиды, участники и приглашения в команды.
- Жизненный цикл задач: бэклог, в работе, на проверке, выполнено.
- Исполнители, дедлайны, XP за задачи и комментарии при возврате на доработку.
- Автоматическое начисление XP после подтверждения задачи.
- Профиль сотрудника с аватаром, командами, выполненными задачами, уровнем и шкалой опыта.
- Уведомления и realtime-поток уведомлений.
- Отчет владельца проекта по задачам: оставшиеся задачи, выполненные задачи, исполнитель, дедлайн, команда и диаграмма активности.
- Логи начисления XP и системные action logs для администраторов.
- Демо-рабочее пространство при старте приложения.

## Стек

**Frontend**

- React 18
- TypeScript
- Vite
- CSS без UI-фреймворка

**Backend**

- Python 3.13
- FastAPI
- SQLAlchemy async
- Alembic
- Pydantic Settings
- JWT-auth
- Redis
- MinIO/S3 для аватаров
- MailHog/SMTP для писем
- Prometheus FastAPI Instrumentator

**Инфраструктура**

- PostgreSQL 15
- Redis 7
- MinIO
- MailHog
- Docker Compose для локальных сервисов

## Структура проекта

```text
.
├── backend/
│   ├── docker-compose.yml        # локальная инфраструктура: Postgres, Redis, MinIO, MailHog
│   ├── Dockerfile
│   └── src/
│       ├── app/                  # FastAPI-приложение
│       ├── alembic/              # миграции БД
│       ├── pyproject.toml
│       └── uv.lock
├── frontend/
│   ├── src/                      # React-приложение
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── .env.example
└── README.md
```

## Быстрый старт

### 1. Требования

- Docker и Docker Compose
- Node.js 20+
- Python 3.13+
- uv

### 2. Настройте переменные окружения

Создайте файл `backend/.env` на основе `.env.example` и заполните значения.

Пример для локального запуска:

```env
APP_HOST=localhost
APP_PORT=8000

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=task_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

HASH_SECRET_KEY=fghb37483n27453rhe8v758
ACCESS_TOKEN_EXPIRE_MINUTES=324572
REFRESH_TOKEN_EXPIRE_DAYS=341876

CACHE_ADAPTER=redis
CACHE_ADAPTER_HOST=localhost
CACHE_ADAPTER_PORT=6379

SMTP_MAIL_USERNAME=
SMTP_MAIL_PASSWORD=
SMTP_MAIL_FROM=task-manager@example.com
SMTP_MAIL_PORT=1025
SMTP_MAIL_HOST=localhost
SMTP_MAIL_STARTTLS=False
SMTP_MAIL_SSL_TLS=False
SMTP_DEBUG=True

S3_PROVIDER=minio
S3_URL=localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
```

### 3. Поднимите инфраструктуру

```powershell
cd backend
docker compose up -d
```

Будут запущены:

- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- MinIO API: `localhost:9000`
- MinIO Console: `localhost:9001`
- MailHog UI: `localhost:8025`

### 4. Запустите backend

```powershell
cd backend/src
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host localhost --port 8000
```

Backend будет доступен на `http://localhost:8000`.

API frontend ожидает backend по адресу `http://localhost:8000/api/v1`. Если нужен другой адрес, задайте `VITE_API_BASE_URL` для frontend.

### 5. Запустите frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend будет доступен на `http://localhost:5173`.

## Демо-данные

При старте backend подготавливает базовые уровни, создает S3-buckets и заполняет демо-рабочее пространство.

Администратор:

```text
email: root@example.com
username: rootadmin
password: strongpass123
```

Демо-пользователи:

```text
teamlead1@example.com / teamlead1_pass
alicework@example.com / alicework_pass
bobworker@example.com / bobworker_pass
charlie8@example.com / charlie8_pass
```

В демо-пространстве создаются проект `Demo Project`, команда `Core Team` и несколько стартовых задач.

## Основные роли

- **Администратор** - имеет доступ к управлению всеми сущностями и системным логам.
- **Владелец проекта** - создает команды, смотрит отчет по проекту, управляет задачами и участниками.
- **Тимлид** - управляет задачами и составом своей команды.
- **Участник** - принимает задачи, отправляет их на проверку, получает XP и может покидать команду.

## Полезные команды

Frontend:

```powershell
cd frontend
npm run dev
npm run build
npm run preview
```

Backend:

```powershell
cd backend/src
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host localhost --port 8000
```

Инфраструктура:

```powershell
cd backend
docker compose up -d
docker compose down
```

## API-модули

Основные группы endpoint-ов:

- `/api/v1/auth` - регистрация, вход, refresh, подтверждение email, сброс пароля.
- `/api/v1/users` - текущий пользователь, профили, директория пользователей, avatar upload URL.
- `/api/v1/projects` - проекты и выход из проекта.
- `/api/v1/teams` - команды, участники, выход из команды.
- `/api/v1/tasks` - задачи и переходы по статусам.
- `/api/v1/invitations` - приглашения в команды.
- `/api/v1/notifications` - уведомления и SSE stream.
- `/api/v1/lvls` - уровни XP.
- `/api/v1/system-logging` - логи XP и действия пользователей.

## Сборка

Frontend можно собрать отдельно:

```powershell
cd frontend
npm run build
```

Для backend есть Dockerfile на базе `nvidia/cuda:13.0.2-base-ubuntu24.04` с установкой зависимостей через `uv`.

## Примечания для разработки

- Миграции находятся в `backend/src/alembic/versions`.
- Настройки backend читаются из `backend/.env` или `backend/src/.env`.
- Frontend по умолчанию использует `http://localhost:8000/api/v1`.
- MailHog удобно использовать для проверки писем подтверждения и восстановления пароля.
- MinIO используется для загрузки и отображения аватаров.
