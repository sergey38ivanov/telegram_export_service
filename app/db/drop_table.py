from sqlalchemy import create_engine, MetaData, Table

# Підключення до бази
DATABASE_URL = "sqlite:///./telegram_export.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Створюємо об’єкт MetaData
metadata = MetaData()

redirect_links = Table('redirect_links', metadata, autoload_with=engine)
redirect_links.drop(engine)
print("Таблиця redirect_links успішно видалена")

# domains = Table('domains', metadata, autoload_with=engine)
# domains.drop(engine)
# print("Таблиця domains успішно видалена")

export_records = Table('export_records', metadata, autoload_with=engine)
export_records.drop(engine)
print("Таблиця export_records успішно видалена")

sessions = Table('sessions', metadata, autoload_with=engine)
sessions.drop(engine)
print("Таблиця sessions успішно видалена")
