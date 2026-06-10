CREATE DATABASE ecom;
USE ecom;

CREATE TABLE categories(
category_id INT AUTO_INCREMENT PRIMARY KEY,
cat_name VARCHAR(50),
parent_id INT DEFAULT NULL,

FOREIGN KEY (parent_id) REFERENCES categories(category_id));

CREATE TABLE users(
user_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
name VARCHAR(50),
email VARCHAR(50),
password VARCHAR(250),
created_at TIMESTAMP,
role ENUM("user" , "admin" , "seller")NOT NULL
);

CREATE TABLE products(
product_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
seller_id INT,
category_id INT,
name VARCHAR(50),
description TEXT,
price DECIMAL(10,2),
stock_qty INT,
created_at TIMESTAMP,

FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE,
FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE

);

CREATE TABLE reviews(
review_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
product_id INT,
user_id INT,
rating TINYINT,
comment TEXT,
created_at TIMESTAMP,

FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE);

CREATE TABLE cart_items(
cart_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
product_id INT,
user_id INT,
qty INT,

FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE);

CREATE TABLE orders(
order_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
user_id INT,
total_amount DECIMAL(10,2),
status ENUM("ordered" , "shipped" , "delivered"  , "cancelled")NOT NULL,
ordered_at TIMESTAMP,

FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE);


CREATE TABLE order_items(
item_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
order_id INT,
product_id INT,
unit_price DECIMAL(10,2),
quantity INT,

FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE);

CREATE TABLE payments(
payment_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
order_id INT,
method ENUM("cash" , "card" , "upi")NOT NULL,
status ENUM("processing" , "failed" , "done")NOT NULL,
amount DECIMAL(10,2),
paid_at TIMESTAMP,

FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE);

	DELIMITER //
	CREATE TRIGGER after_trigger_item_insert
	AFTER INSERT ON order_items
	FOR EACH ROW 
	BEGIN
		UPDATE PRODUCTS
		SET stock_qty = stock_qty - NEW.quantity
		WHERE product_id = NEW.product_id;
	END//
	DELIMITER ;
    
    DELIMITER $$
    CREATE TRIGGER after_payment_update
    AFTER UPDATE ON payments
    FOR EACH ROW
    BEGIN
		IF NEW.status = "failed" THEN
			UPDATE ORDERS
			SET status = 'cancelled'
			WHERE order_id = NEW.order_id;
		END IF;
	END$$
    DELIMITER ;
    
    DELIMITER $$
CREATE PROCEDURE place_order(
    IN p_user_id    INT,
    IN p_product_id INT,
    IN p_quantity   INT,
    IN p_method     ENUM('cash', 'card', 'upi')
)
BEGIN
    DECLARE v_price       DECIMAL(10,2);
    DECLARE v_stock       INT;
    DECLARE v_order_id    INT;
    DECLARE v_total       DECIMAL(10,2);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Order failed, transaction rolled back';
    END;

    START TRANSACTION;

    -- Check stock
    SELECT price, stock_qty INTO v_price, v_stock
    FROM products WHERE product_id = p_product_id FOR UPDATE;

    IF v_stock < p_quantity THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient stock';
    END IF;

    SET v_total = v_price * p_quantity;

    -- Create order
    INSERT INTO orders (user_id, total_amount, status, ordered_at)
    VALUES (p_user_id, v_total, 'ordered', NOW());

    SET v_order_id = LAST_INSERT_ID();

    -- Add order item (triggers stock reduction automatically)
    INSERT INTO order_items (order_id, product_id, unit_price, quantity)
    VALUES (v_order_id, p_product_id, v_price, p_quantity);

    -- Create payment record
    INSERT INTO payments (order_id, method, status, amount, paid_at)
    VALUES (v_order_id, p_method, 'processing', v_total, NOW());

    COMMIT;
END$$
DELIMITER ;
    

CREATE VIEW product_rating AS
SELECT
	p.product_id,
	p.name AS product_name,
    COUNT(r.review_id) AS TOTAL_REVIEWS,
    ROUND(AVG(r.rating),1) AS avg_rating
FROM products p
LEFT JOIN reviews r on p.product_id = r.product_id
GROUP BY p.product_id , p.name;

CREATE VIEW user_order_history AS
SELECT
    u.user_id,
    u.name AS customer_name,
    o.order_id,
    o.status AS order_status,
    o.total_amount,
    o.ordered_at,
    p.status AS payment_status,
    p.method AS payment_method
FROM users u
JOIN orders o    ON u.user_id  = o.user_id
JOIN payments p  ON o.order_id = p.order_id
ORDER BY o.ordered_at DESC;

CREATE INDEX idx_products_category  ON products(category_id);
CREATE INDEX idx_orders_user        ON orders(user_id);
CREATE INDEX idx_reviews_product    ON reviews(product_id);
CREATE INDEX idx_order_items_order  ON order_items(order_id);
CREATE INDEX idx_payments_order     ON payments(order_id);

