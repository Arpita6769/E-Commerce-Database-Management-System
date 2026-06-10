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


if __name__ == '__main__':
    app.run(debug=True)