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
        text("SELECT order_id FROM orders")
    ).fetchall()

    products = connection.execute(
        text("SELECT product_id, price FROM products")
    ).fetchall()

    for order in orders:

        order_id = order[0]

        item_count = fake.random_int(min=1, max=3)

        for _ in range(item_count):

            product = fake.random_element(products)

            product_id = product[0]
            unit_price = product[1]

            quantity = fake.random_int(min=1, max=5)

            discount = round(
                fake.pyfloat(
                    min_value=0,
                    max_value=500,
                    right_digits=2
                ),
                2
            )

            connection.execute(
                text("""
                    INSERT INTO order_items
                    (order_id, product_id, quantity, unit_price, discount)
                    VALUES
                    (:order_id, :product_id, :quantity, :unit_price, :discount)
                """),
                {
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount": discount
                }
            )

print("Order items inserted successfully!")