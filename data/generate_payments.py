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

    orders = connection.execute(
        text("""
            SELECT order_id, order_date, total_amount
            FROM orders
        """)
    ).fetchall()

    for order in orders:

        order_id = order[0]
        order_date = order[1]
        total_amount = order[2]

        payment_status = fake.random_element([
            "success",
            "success",
            "success",
            "failed"
        ])

        payment_method = fake.random_element([
            "UPI",
            "Credit Card",
            "Debit Card",
            "Net Banking"
        ])

        amount = total_amount if payment_status == "success" else 0

        connection.execute(
            text("""
                INSERT INTO payments
                (order_id, payment_date, amount, payment_method, payment_status)
                VALUES
                (:order_id, :payment_date, :amount, :payment_method, :payment_status)
            """),
            {
                "order_id": order_id,
                "payment_date": order_date,
                "amount": amount,
                "payment_method": payment_method,
                "payment_status": payment_status
            }
        )

print("Payments inserted successfully!")