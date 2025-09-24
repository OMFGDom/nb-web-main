# create_podcast_table.py
from sqlalchemy import create_engine
from src.models.base import Base
from src.models.podcast import Podcast  # модель таблицы

# строка подключения к Postgres
DATABASE_URL = "postgresql://postgres:admin123@127.0.0.1:5432/nb_db"

def main():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine, tables=[Podcast.__table__])
    print("Таблица Podcast создана (если её не было).")

if __name__ == "__main__":
    main()
