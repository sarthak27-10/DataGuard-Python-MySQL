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
            SELECT order_id, order_date
            FROM orders
            ORDER BY order_id
            LIMIT 50
        """)
    ).fetchall()

    for order in orders:

        order_id = order[0]
        order_date = order[1]

        product = connection.execute(
            text("""
                SELECT product_id
                FROM order_items
                WHERE order_id = :order_id
                LIMIT 1
            """),
            {"order_id": order_id}
        ).fetchone()

        if product is None:
            continue

        product_id = product[0]

        return_date = fake.date_time_between(
            start_date=order_date,
            end_date="now"
        )

        refund_amount = round(
            fake.pyfloat(
                min_value=100,
                max_value=5000,
                right_digits=2
            ),
            2
        )

        return_reason = fake.random_element([
            "Damaged product",
            "Wrong product",
            "Product not as expected",
            "Customer changed mind"
        ])

        connection.execute(
            text("""
                INSERT INTO returns
                (order_id, product_id, return_reason, return_date, refund_amount)
                VALUES
                (:order_id, :product_id, :return_reason, :return_date, :refund_amount)
            """),
            {
                "order_id": order_id,
                "product_id": product_id,
                "return_reason": return_reason,
                "return_date": return_date,
                "refund_amount": refund_amount
            }
        )

print("Returns inserted successfully!")