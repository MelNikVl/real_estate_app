from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from datetime import datetime
import random
from sqlmodel import Field, SQLModel, create_engine, Session # Убедитесь, что все импорты есть
import os
import json
import httpx # Для выполнения HTTP-запросов из бэкенда

# Конфигурация базы данных
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@db:5432/real_estate_db")
engine = create_engine(DATABASE_URL)

# Функция для создания таблиц (без изменений)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI(root_path="/api")

# Добавьте этот блок для CORS (если уже есть, убедитесь, что он такой)
origins = [
    "http://localhost",       # Для локальной разработки фронтенда
    "http://localhost:80",    # Для локальной разработки фронтенда (порт 80)
    "http://localhost:3000",  # Для локальной разработки фронтенда (порт 3000, если используете react dev server напрямую)
    "http://52.23.160.127",   # Ваш актуальный публичный IP EC2 инстанса
    "http://backend",         # Имя Docker сервиса frontend, как он видит backend внутри Docker Compose сети
    "http://backend:80",      # Если frontend будет явно указывать порт, хотя обычно хватает просто имени сервиса
    "http://backend:8000",    # На всякий случай, если внутренний запрос будет с портом
    "http://real-estate-app.pro",   # Ваш домен (HTTP)
    "https://real-estate-app.pro"   # Ваш домен (HTTPS)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
        headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"}
    )

# Определяем модель для таблицы PropertyEstimate (если уже есть, убедитесь, что она такая)
class PropertyEstimate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    address: str = Field(index=True)
    estimated_value: float
    currency: str
    property_type: str | None = None
    bedrooms: int | None = None
    bathrooms: float | None = None
    square_footage: int | None = None
    lot_size: int | None = None
    year_built: int | None = None
    last_sale_date: str | None = None
    sale_history_json: str | None = None # Храним историю продаж как JSON-строку
    created_at: str | None = None # Время создания оценки

# Событие запуска приложения: создание таблиц
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# ВРЕМЕННЫЙ маршрут для ручного создания таблиц (удалите после инициализации!)
@app.post("/init-db")
def init_db():
    create_db_and_tables()
    return {"status": "ok", "message": "Database tables created."}

# Маршрут для получения оценки недвижимости (может быть улучшен для реальных данных)
@app.get("/estimate")
async def get_property_estimate(address: str):
    # Здесь могла бы быть логика для реальной оценки
    # Пока что генерируем случайные данные
    estimated_value = round(random.uniform(300000, 1000000), 2)
    currency = "USD"

    # Добавляем больше "случайных" данных для демонстрации
    property_type = random.choice(["House", "Apartment", "Condo"])
    bedrooms = random.randint(2, 5)
    bathrooms = random.choice([1.0, 1.5, 2.0, 2.5, 3.0])
    square_footage = random.randint(1200, 3500)
    lot_size = random.randint(5000, 15000)
    year_built = random.randint(1950, 2020)
    
    # Пример случайной истории продаж
    sale_history = {}
    num_sales = random.randint(0, 3)
    for i in range(num_sales):
        sale_date = datetime.now().year - random.randint(1, 10)
        sale_price = round(estimated_value * random.uniform(0.8, 1.2), 2)
        sale_history[f"sale_{i}"] = {"event": "Sale", "date": f"{sale_date}-01-01", "price": sale_price}

    last_sale_date = None
    if sale_history:
        # Для простоты возьмем первую продажу как последнюю
        last_sale_date = list(sale_history.values())[0]["date"]

    response_data = {
        "address": address,
        "estimated_value": estimated_value,
        "currency": currency,
        "property_type": property_type,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "square_footage": square_footage,
        "lot_size": lot_size,
        "year_built": year_built,
        "last_sale_date": last_sale_date,
        "sale_history_json": json.dumps(sale_history), # Преобразуем в JSON-строку
        "created_at": datetime.now().isoformat()
    }

    # Сохраняем оценку в базу данных
    with Session(engine) as session:
        db_estimate = PropertyEstimate(
            address=response_data["address"],
            estimated_value=response_data["estimated_value"],
            currency=response_data["currency"],
            property_type=response_data["property_type"],
            bedrooms=response_data["bedrooms"],
            bathrooms=response_data["bathrooms"],
            square_footage=response_data["square_footage"],
            lot_size=response_data["lot_size"],
            year_built=response_data["year_built"],
            last_sale_date=response_data["last_sale_date"],
            sale_history_json=response_data["sale_history_json"],
            created_at=response_data["created_at"]
        )
        session.add(db_estimate)
        session.commit()
        session.refresh(db_estimate) # Обновляем объект, чтобы получить id

    return response_data


# НОВЫЙ МАРШРУТ: Прокси для Google Places Autocomplete API
@app.get("/google-autocomplete")
async def google_autocomplete_proxy(input: str):
    google_api_key = os.environ.get("GOOGLE_API_KEY") # Получаем ключ из переменной окружения
    if not google_api_key:
        raise HTTPException(status_code=500, detail="Google API Key is not configured on the backend.")

    # Ограничиваем подсказки только США
    components = "country:us"
    async with httpx.AsyncClient() as client:
        google_places_url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={input}&types=address&components={components}&key={google_api_key}"
        try:
            response = await client.get(google_places_url)
            response.raise_for_status() # Вызывает исключение для статусов 4xx/5xx
            # Возвращаем полный ответ Google API для диагностики
            return JSONResponse(
                status_code=response.status_code,
                content=response.json(),
                headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"}
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"An error occurred while requesting Google Places API: {exc}")
        except httpx.HTTPStatusError as exc:
            # Возвращаем подробный ответ Google API при ошибке
            return JSONResponse(
                status_code=exc.response.status_code,
                content={
                    "error": "Google Places API returned an error",
                    "status_code": exc.response.status_code,
                    "text": exc.response.text,
                    "json": exc.response.json() if exc.response.headers.get('content-type', '').startswith('application/json') else None
                },
                headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"}
            )

