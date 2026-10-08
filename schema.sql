CREATE TABLE customers (
    customer_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(150),
    email VARCHAR(150),
    phone VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(100),
    created_at DATETIME,
    status VARCHAR(30)
);

CREATE TABLE products (
    product_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(150),
    category VARCHAR(100),
    price DECIMAL(12,2),
    cost_price DECIMAL(12,2),
    stock INT,
    created_at DATETIME
);

CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_id BIGINT NOT NULL,
    order_date DATETIME NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,

    CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id)
    REFERENCES customers(customer_id),

    INDEX idx_orders_customer_date
    (customer_id, order_date),

    INDEX idx_orders_date
    (order_date)
);