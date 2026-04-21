# 🚀 Запуск проекта

## 1. Клонирование репозитория

```bash
git clone https://github.com/ExtroZ-ui/HomWork3.git
cd HomWork3
```

---

## 2. Создание виртуального окружения

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / MacOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Установка зависимостей

⚠️ Важно: из-за несовместимости `passlib` и `bcrypt 5.x` необходимо зафиксировать версию bcrypt.

```bash
pip install -r requirements.txt
pip uninstall bcrypt -y
pip install bcrypt==4.0.1
```

Проверка версии:

```bash
python -c "import bcrypt; print(bcrypt.__version__)"
```

Ожидаемый результат:

```
4.0.1
```

---

## 4. Запуск Redis (Docker)

```bash
docker run -d --name redis-hw6 -p 6379:6379 redis:7
```

Проверка:

```bash
docker ps
```

---

## 5. Запуск приложения

```bash
python -m uvicorn app.main:app --reload
```

Swagger UI:

```
http://127.0.0.1:8000/docs
```

---

## 6. Тестирование API

### Регистрация пользователя

```json
POST /auth/register
{
  "username": "user1",
  "password": "test123",
  "is_read_only": false
}
```

---

### Авторизация

```json
POST /auth/login
```

➡️ Использовать `X-User-Id` в заголовках

---

### Фоновый импорт CSV

```json
POST /import-csv-background
{
  "csv_path": "students.csv"
}
```

---

### Фоновое удаление студентов

```json
POST /students/delete-background
{
  "student_ids": [1, 2, 3]
}
```

---

## 7. Проверка Redis

Подключение:

```bash
docker exec -it redis-hw6 redis-cli
```

Проверка:

```bash
PING
```

Ответ:

```
PONG
```

Просмотр кеша:

```bash
KEYS *
```

---

## 8. Что реализовано

* ✅ Фоновая задача импорта данных из CSV (BackgroundTasks)
* ✅ Фоновое удаление студентов по списку ID
* ✅ Кеширование GET-запросов через Redis
* ✅ Очистка кеша при изменении данных

---

## 9. Остановка

```bash
docker stop redis-hw6
docker rm redis-hw6
```
