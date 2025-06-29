from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Field, SQLModel, create_engine, Session, select, delete
from datetime import datetime, timezone
import requests # Для HTTP-запросов к внешним API
from fastapi.middleware.cors import CORSMiddleware
import os # Для работы с переменными окружения

# Конфигурация базы данных
DATABASE_URL = "postgresql://user:password@db:5432/real_estate_db"
engine = create_engine(DATABASE_URL, echo=True) # echo=True выводит SQL-запросы в консоль

# --- НАЧАЛО ИЗМЕНЕНИЙ ---

# Ваш API-ключ для RentCast.
# В реальном приложении рекомендуется хранить его в переменных окружения.
# Для этого можно использовать переменную окружения RENTCAST_API_KEY.
# os.environ.get("RENTCAST_API_KEY") попытается получить значение из переменной окружения.
# Если переменная не установлена, будет использован ваш предоставленный ключ.
RENTCAST_API_KEY = os.environ.get("RENTCAST_API_KEY", "626518b38b5b473fab9c57151578e37f")
# Базовый URL для RentCast API
RENTCAST_BASE_URL = "https://api.rentcast.io/v1"

# --- КОНЕЦ ИЗМЕНЕНИЙ ---


# Определение модели данных для оценки недвижимости
# Эта модель описывает, как данные будут храниться в базе данных PostgreSQL
class PropertyEstimate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    address: str = Field(index=True)
    estimated_value: Optional[float] # Сделано Optional, так как оценка может отсутствовать
    currency: Optional[str] = "USD" # Валюта может быть опциональной, по умолчанию USD
    # Добавляем новые поля для хранения базовых характеристик и истории продаж
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None # Ванные могут быть 1.5, 2.5
    square_footage: Optional[int] = None
    lot_size: Optional[int] = None
    year_built: Optional[int] = None
    last_sale_date: Optional[str] = None # Для хранения даты последней продажи
    sale_history_json: Optional[str] = None # Для хранения истории продаж в виде JSON-строки

    created_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Функция для создания таблиц в базе данных
# Вызывается при запуске приложения, чтобы убедиться, что таблицы существуют
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Вспомогательная функция для получения сессии базы данных
# Используется как зависимость в эндпоинтах FastAPI
def get_session():
    with Session(engine) as session:
        yield session

# Инициализация FastAPI приложения
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000", # Разрешаем запросы с React-приложения
    # Если ваш фронтенд будет на другом домене/порту, добавьте его сюда
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Разрешенные домены
    allow_credentials=True, # Разрешить куки/авторизационные заголовки
    allow_methods=["*"], # Разрешить все HTTP-методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"], # Разрешить все заголовки в запросах
)

# Обработчик события "startup" (запуск приложения)
# Вызываем функцию создания таблиц при старте
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Базовый эндпоинт
@app.get("/")
async def read_root():
    return {"message": "Welcome to Real Estate Valuation API MVP!"}

# Эндпоинт для проверки работоспособности
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Эндпоинт для создания новой записи об оценке недвижимости
# Принимает данные в формате PropertyEstimate и сохраняет их в БД
# Этот эндпоинт теперь не будет использоваться напрямую для создания оценки,
# так как /estimate будет делать это автоматически. Оставим для общности.
@app.post("/estimates/", response_model=PropertyEstimate)
def create_estimate(estimate: PropertyEstimate, session: Session = Depends(get_session)):
    session.add(estimate)
    session.commit()
    session.refresh(estimate) # Обновляем объект, чтобы получить ID, сгенерированный БД
    return estimate

# Эндпоинт для получения всех сохраненных оценок
@app.get("/estimates/", response_model=List[PropertyEstimate])
def get_all_estimates(session: Session = Depends(get_session)):
    estimates = session.exec(select(PropertyEstimate)).all()
    return estimates

# НОВЫЙ ЭНДПОИНТ: Очистка всех оценок (ТОЛЬКО ДЛЯ РАЗРАБОТКИ!)
@app.delete("/clear-estimates/")
def clear_all_estimates(session: Session = Depends(get_session)):
    # Удаляем все записи из таблицы PropertyEstimate
    session.exec(delete(PropertyEstimate))
    session.commit()
    return {"message": "All estimates cleared successfully (DEVELOPMENT ONLY!)"}

# Основной эндпоинт для получения или создания оценки по адресу
# Сначала ищет в локальной БД, затем обращается к внешнему RentCast API, если не найдено
@app.get("/estimate", response_model=PropertyEstimate)
def get_or_create_estimate(address: str, session: Session = Depends(get_session)):
    # 1. Поиск оценки в локальной базе данных
    estimate = session.exec(select(PropertyEstimate).where(PropertyEstimate.address == address)).first()
    if estimate:
        print(f"Estimate for {address} found in DB.")
        return estimate

    # 2. Если оценка не найдена в локальной БД, обращаемся к RentCast API
    print(f"Estimate for {address} not found in DB. Calling RentCast API...")
    try:
        # Заголовки для запроса к RentCast API, включая API-ключ
        headers = {
            "Accept": "application/json",
            "X-Api-Key": RENTCAST_API_KEY
        }

        # Формируем URL для запроса к эндпоинту /properties с параметром address
        # Документация RentCast указывает, что /properties может принимать 'address'
        # для получения данных по конкретному объекту.
        rentcast_url = f"{RENTCAST_BASE_URL}/properties?address={address}"

        response = requests.get(rentcast_url, headers=headers)
        response.raise_for_status() # Вызовет исключение для ошибок HTTP (4xx или 5xx)

        rentcast_data = response.json()

        # RentCast /properties возвращает массив объектов. Для запроса по конкретному адресу
        # ожидаем, что будет один (или ноль) результатов. Берем первый элемент.
        if not rentcast_data:
            raise HTTPException(status_code=404, detail=f"No property data found for address: {address}")

        property_data = rentcast_data[0] # Берем первый найденный объект недвижимости

        # Извлекаем необходимые поля из ответа RentCast
        # 'lastSalePrice' будет использоваться как 'estimated_value'
        avm_estimated_value = property_data.get("lastSalePrice")
        avm_currency = "USD" # RentCast возвращает цены в USD

        # Базовые характеристики объекта
        property_type = property_data.get("propertyType")
        bedrooms = property_data.get("bedrooms")
        bathrooms = property_data.get("bathrooms")
        square_footage = property_data.get("squareFootage")
        lot_size = property_data.get("lotSize")
        year_built = property_data.get("yearBuilt")
        last_sale_date = property_data.get("lastSaleDate")

        # История продаж объекта
        sale_history_raw = property_data.get("history", {})
        # Преобразуем историю продаж в JSON-строку для хранения в БД
        import json
        sale_history_json = json.dumps(sale_history_raw)


        # 3. Создание новой записи в нашей БД на основе данных от RentCast API
        new_estimate = PropertyEstimate(
            address=address,
            estimated_value=avm_estimated_value,
            currency=avm_currency,
            property_type=property_type,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_footage=square_footage,
            lot_size=lot_size,
            year_built=year_built,
            last_sale_date=last_sale_date,
            sale_history_json=sale_history_json # Сохраняем историю продаж
        )
        session.add(new_estimate)
        session.commit()
        session.refresh(new_estimate) # Обновляем объект, чтобы получить ID из БД
        print(f"New estimate for {address} saved to DB.")
        return new_estimate

    except requests.exceptions.RequestException as e:
        # Обработка ошибок при подключении к внешнему API
        print(f"Error connecting to RentCast API: {e}")
        raise HTTPException(status_code=500, detail=f"Error connecting to RentCast API: {e}")
    except Exception as e:
        # Обработка любых других неожиданных ошибок
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# Запуск Flask-приложения
# Эту часть нужно оставить, как есть, если ваш Dockerfile запускает uvicorn main:app
# if __name__ == "__main__":
#     # Запускаем приложение в режиме отладки (debug=True).
#     # В продакшене debug=False и используется продакшн-сервер (например, Gunicorn, uWSGI).
#     # host='0.0.0.0' делает сервер доступным извне, если вы развертываете его.
#     app.run(debug=True, host='0.0.0.0', port=5000)
