# app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# SQLite database configuration (no PostgreSQL needed)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'customers.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
print(f"Using SQLite database at: {os.path.join(basedir, 'customers.db')}")

db = SQLAlchemy(app)

# Customer model
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active')
    total_orders = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0.0)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'status': self.status,
            'totalOrders': self.total_orders,
            'totalSpent': self.total_spent,
            'joinDate': self.join_date.isoformat()
        }

# Routes
@app.route('/api/customers', methods=['GET'])
def get_customers():
    try:
        customers = Customer.query.all()
        return jsonify([customer.to_dict() for customer in customers])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers', methods=['POST'])
def create_customer():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('email'):
            return jsonify({'error': 'Name and email are required'}), 400
        
        # Check if email already exists
        existing_customer = Customer.query.filter_by(email=data['email']).first()
        if existing_customer:
            return jsonify({'error': 'Email already exists'}), 400
        
        customer = Customer(
            name=data['name'],
            email=data['email'],
            status=data.get('status', 'active'),
            total_orders=data.get('totalOrders', 0),
            total_spent=data.get('totalSpent', 0.0)
        )
        db.session.add(customer)
        db.session.commit()
        return jsonify(customer.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    try:
        customer = Customer.query.get_or_404(customer_id)
        data = request.get_json()
        
        customer.name = data.get('name', customer.name)
        customer.email = data.get('email', customer.email)
        customer.status = data.get('status', customer.status)
        customer.total_orders = data.get('totalOrders', customer.total_orders)
        customer.total_spent = data.get('totalSpent', customer.total_spent)
        
        db.session.commit()
        return jsonify(customer.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    try:
        customer = Customer.query.get_or_404(customer_id)
        db.session.delete(customer)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        total_customers = Customer.query.count()
        active_customers = Customer.query.filter_by(status='active').count()
        total_revenue = db.session.query(db.func.sum(Customer.total_spent)).scalar() or 0
        total_orders = db.session.query(db.func.sum(Customer.total_orders)).scalar() or 0
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return jsonify({
            'totalCustomers': total_customers,
            'activeCustomers': active_customers,
            'totalRevenue': float(total_revenue),
            'avgOrderValue': float(avg_order_value)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'API is running'})

if __name__ == '__main__':
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Add sample data if table is empty
        if Customer.query.count() == 0:
            sample_customers = [
                Customer(name='John Doe', email='john@example.com', status='active', total_orders=15, total_spent=2850.50),
                Customer(name='Jane Smith', email='jane@example.com', status='active', total_orders=8, total_spent=1250.00),
                Customer(name='Bob Johnson', email='bob@example.com', status='inactive', total_orders=3, total_spent=450.75),
                Customer(name='Alice Brown', email='alice@example.com', status='active', total_orders=22, total_spent=4200.25),
                Customer(name='Charlie Wilson', email='charlie@example.com', status='pending', total_orders=0, total_spent=0.00)
            ]
            for customer in sample_customers:
                db.session.add(customer)
            db.session.commit()
            print("Sample data added to database")
    
    print("Starting Flask server...")
    print("API will be available at: http://localhost:5000")
    app.run(debug=True, port=5000)