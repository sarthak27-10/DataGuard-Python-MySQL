import os
from faker import Faker
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()
fake = Faker()

url = URL.create(
    "mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME")
)

engine = create_engine(url, pool_pre_ping=True)

categories = [
    "Electronics",
    "Clothing",
    "Home",
    "Beauty",
    "Sports"
]

with engine.begin() as connection:
    for _ in range(100):
        price = round(fake.pyfloat(min_value=100, max_value=50000, right_digits=2), 2)
        cost_price = round(price * fake.pyfloat(min_value=0.50, max_value=0.85), 2)

        connection.execute(
            text("""
                INSERT INTO products
                (product_name, category, price, cost_price, stock, created_at)
                VALUES
                (:product_name, :category, :price, :cost_price, :stock, :created_at)
            """),
            {
                "product_name": fake.catch_phrase(),
                "category": fake.random_element(categories),
                "price": price,
                "cost_price": cost_price,
                "stock": fake.random_int(min=0, max=500),
                "created_at": fake.date_time_between(start_date="-730d", end_date="now")
            }
        )

print("100 products inserted successfully!")
