from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Field, SQLModel, create_engine, Session, select, delete # <<< ДОБАВЛЕН 'delete' ЗДЕСЬ
from datetime import datetime, timezone
import requests # Для HTTP-запросов к внешним API
from fastapi.middleware.cors import CORSMiddleware

# Конфигурация базы данных
DATABASE_URL = "postgresql://user:password@db:5432/real_estate_db"
engine = create_engine(DATABASE_URL, echo=True) # echo=True выводит SQL-запросы в консоль

# URL для "фейкового" AVM API. В реальном проекте здесь будет URL внешнего сервиса.
# Пока это просто заглушка, которая имитирует внешний вызов.
FAKE_AVM_API_URL = "https://jsonplaceholder.typicode.com/posts/1" # Не реальный AVM, просто пример

# Определение модели данных для оценки недвижимости
# Эта модель описывает, как данные будут храниться в базе данных PostgreSQL
class PropertyEstimate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    address: str = Field(index=True)
    estimated_value: float
    currency: str
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
# Сначала ищет в локальной БД, затем "обращается" к внешнему API, если не найдено
@app.get("/estimate", response_model=PropertyEstimate)
def get_or_create_estimate(address: str, session: Session = Depends(get_session)):
    # 1. Поиск оценки в локальной базе данных
    estimate = session.exec(select(PropertyEstimate).where(PropertyEstimate.address == address)).first()
    if estimate:
        print(f"Estimate for {address} found in DB.")
        return estimate

    # 2. Если оценка не найдена в локальной БД, "обращаемся" к внешнему AVM API
    print(f"Estimate for {address} not found in DB. Calling external AVM API...")
    try:
        # Здесь будет реальная логика вызова внешнего AVM API, например:
        # response = requests.get(f"https://api.externalavm.com/estimate?address={address}&api_key=YOUR_KEY")
        # response.raise_for_status() # Вызовет исключение для ошибок HTTP (4xx или 5xx)
        # avm_data = response.json()
        # avm_estimated_value = avm_data.get("value")
        # avm_currency = avm_data.get("currency", "USD")

        # Имитируем ответ от AVM API для демонстрации:
        if "Main St" in address:
            avm_estimated_value = 520000.0
            avm_currency = "USD"
        elif "Elm St" in address:
            avm_estimated_value = 350000.0
            avm_currency = "USD"
        else:
            # Если адрес не может быть оценен "внешним" API
            raise HTTPException(status_code=404, detail=f"Estimate not found by external AVM for address: {address}")

        # 3. Создание новой записи в нашей БД на основе данных от AVM API
        new_estimate = PropertyEstimate(
            address=address,
            estimated_value=avm_estimated_value,
            currency=avm_currency
        )
        session.add(new_estimate)
        session.commit()
        session.refresh(new_estimate) # Обновляем объект, чтобы получить ID из БД
        print(f"New estimate for {address} saved to DB.")
        return new_estimate

    except requests.exceptions.RequestException as e:
        # Обработка ошибок при подключении к внешнему API
        raise HTTPException(status_code=500, detail=f"Error connecting to external AVM API: {e}")
    except Exception as e:
        # Обработка любых других неожиданных ошибок
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")