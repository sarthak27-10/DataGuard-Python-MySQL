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

    customers = connection.execute(
        text("SELECT customer_id FROM customers")
    ).fetchall()

    for _ in range(200):

        customer_id = fake.random_element(customers)[0]

        order_date = fake.date_time_between(
            start_date="-730d",
            end_date="now"
        )

        order_status = fake.random_element([
            "completed",
            "completed",
            "completed",
            "cancelled",
            "pending"
        ])

        total_amount = round(
            fake.pyfloat(
                min_value=500,
                max_value=50000,
                right_digits=2
            ),
            2
        )

        connection.execute(
            text("""
                INSERT INTO orders
                (customer_id, order_date, order_status, total_amount)
                VALUES
                (:customer_id, :order_date, :order_status, :total_amount)
            """),
            {
                "customer_id": customer_id,
                "order_date": order_date,
                "order_status": order_status,
                "total_amount": total_amount
            }
        )

print("200 orders inserted successfully!")