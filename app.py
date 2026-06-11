from flask import Flask, request, jsonify
import mysql.connector
from config import Config
import hashlib
app = Flask(__name__)
app.config.from_object(Config)

# DB connection function
def get_db():
    conn = mysql.connector.connect(
        host     = app.config['MYSQL_HOST'],
        user     = app.config['MYSQL_USER'],
        password = app.config['MYSQL_PASSWORD'],
        database = app.config['MYSQL_DATABASE']
    )
    return conn

# Test route
@app.route('/')
def index():
    return jsonify({'message': 'Ecommerce API is running!'})

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, created_at, role) VALUES (%s, %s, %s, NOW(), %s)",
            (data['name'], data['email'], hash_password(data['password']), data.get('role', 'user'))
        )
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

        
@app.route('/auth/login' , methods = ['POST']) 
def login():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM users WHERE email = %s AND password = %s",
            (data['email'], hash_password(data['password']))
        )
        user = cursor.fetchone()
        if user:
            return jsonify({'message': 'Login successful', 'user_id': user['user_id'], 'role': user['role']}), 200
        return jsonify({'error': 'Invalid credentials'}), 401
    finally:
        cursor.close()
        conn.close()


@app.route('/products/', methods=['GET'])
def get_products():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.product_id, p.name, p.price, p.stock_qty,
                   c.cat_name AS category
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
        """)
        return jsonify(cursor.fetchall()), 200
    finally:
        cursor.close()
        conn.close()


@app.route('/products/add', methods=['POST'])
def add_product():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO products
               (seller_id, category_id, name, description, price, stock_qty, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
            (data['seller_id'], data['category_id'], data['name'],
             data['description'], data['price'], data['stock_qty'])
        )
        conn.commit()
        return jsonify({'message': 'Product added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route('/orders/place', methods=['POST'])
def place_order():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.callproc('place_order', [
            data['user_id'],
            data['product_id'],
            data['quantity'],
            data['method']
        ])
        conn.commit()
        return jsonify({'message': 'Order placed successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route('/orders/history/<int:user_id>', methods=['GET'])
def order_history(user_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM user_order_history WHERE user_id = %s",
            (user_id,)
        )
        return jsonify(cursor.fetchall()), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/reviews/add', methods=['POST'])
def add_review():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO reviews (product_id, user_id, rating, comment, created_at)
               VALUES (%s, %s, %s, %s, NOW())""",
            (data['product_id'], data['user_id'], data['rating'], data['comment'])
        )
        conn.commit()
        return jsonify({'message': 'Review added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/reviews/<int:product_id>', methods=['GET'])
def get_reviews(product_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM product_rating WHERE product_id = %s",
            (product_id,)
        )
        return jsonify(cursor.fetchone()), 200
    finally:
        cursor.close()
        conn.close()

        
if __name__ == '__main__':
    app.run(debug=True)