from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost/ecommerce_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Processing')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref='order_items')

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product', backref='in_carts')

# Sample product data
sample_products = [
    {
        'name': 'Organic Olive Oil',
        'price': 24.99,
        'description': 'Premium quality extra virgin olive oil from Mediterranean olives.',
        'image': 'olive-oil.jpg'
    },
    {
        'name': 'Artisan Coffee Blend',
        'price': 14.95,
        'description': 'Rich, aromatic coffee blend with notes of chocolate and nuts.',
        'image': 'coffee.jpg'
    },
    {
        'name': 'Handcrafted Soap Set',
        'price': 19.99,
        'description': 'Natural olive oil based soaps with essential oils.',
        'image': 'soap-set.jpg'
    },
    {
        'name': 'Rustic Bread Basket',
        'price': 32.50,
        'description': 'Handwoven bread basket perfect for your kitchen.',
        'image': 'bread-basket.jpg'
    },
    {
        'name': 'Ceramic Dinner Set',
        'price': 89.99,
        'description': 'Earthenware dinner set with olive branch pattern.',
        'image': 'dinner-set.jpg'
    },
    {
        'name': 'Olive Wood Cutting Board',
        'price': 39.95,
        'description': 'Beautiful and durable olive wood cutting board.',
        'image': 'cutting-board.jpg'
    },
    {
        'name': 'Herbal Tea Collection',
        'price': 22.99,
        'description': 'Assortment of organic herbal teas in reusable tin.',
        'image': 'tea-collection.jpg'
    },
    {
        'name': 'Handmade Throw Blanket',
        'price': 45.00,
        'description': 'Cozy throw blanket in olive and brown tones.',
        'image': 'throw-blanket.jpg'
    },
    {
        'name': 'Aromatic Candle Set',
        'price': 28.75,
        'description': 'Soy candles with scents of sandalwood and olive blossom.',
        'image': 'candle-set.jpg'
    },
    {
        'name': 'Bamboo Serving Tray',
        'price': 37.50,
        'description': 'Eco-friendly bamboo serving tray with handles.',
        'image': 'serving-tray.jpg'
    }
]

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables and add sample products
def initialize_database():
    with app.app_context():
        db.create_all()
        # Add sample products if they don't exist
        if Product.query.count() == 0:
            for product_data in sample_products:
                product = Product(**product_data)
                db.session.add(product)
            db.session.commit()
        print("Database initialized successfully!")

# Initialize the database when the app starts
initialize_database()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/store')
def store():
    products = Product.query.all()
    return render_template('store.html', products=products)

@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if product is already in cart
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product_id)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Item added to cart!', 'success')
    return redirect(url_for('store'))

@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total = 0
    cart_products = []
    
    for item in cart_items:
        product_total = item.product.price * item.quantity
        cart_products.append({
            'id': item.product.id,
            'name': item.product.name,
            'price': item.product.price,
            'quantity': item.quantity,
            'total': product_total,
            'image': item.product.image
        })
        total += product_total
    
    return render_template('cart.html', cart_items=cart_products, total=total)

@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart!', 'info')
    
    return redirect(url_for('cart'))

@app.route('/confirm_order')
@login_required
def confirm_order():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('store'))
    
    # Create order
    total = sum(item.product.price * item.quantity for item in cart_items)
    order = Order(user_id=current_user.id, total_amount=total)
    db.session.add(order)
    db.session.flush()  # Get the order ID
    
    # Add order items
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price
        )
        db.session.add(order_item)
    
    # Clear cart
    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    flash(f'Order #{order.id} confirmed successfully!', 'success')
    return redirect(url_for('view_orders'))

@app.route('/orders')
@login_required
def view_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, email=email, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)