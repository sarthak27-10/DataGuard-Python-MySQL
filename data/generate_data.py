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

with engine.begin() as connection:
    for _ in range(100):
        connection.execute(
            text("""
                INSERT INTO customers
                (full_name, email, phone, city, state, created_at, status)
                VALUES
                (:full_name, :email, :phone, :city, :state, :created_at, :status)
            """),
            {
                "full_name": fake.name(),
                "email": fake.email(),
                "phone": fake.msisdn()[:20],
                "city": fake.city(),
                "state": fake.state(),
                "created_at": fake.date_time_between(start_date="-730d", end_date="now"),
                "status": fake.random_element(["active", "inactive"])
            }
        )

print("100 customers inserted successfully!")
