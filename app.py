from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_mysqldb import MySQL
import os
import datetime
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import math
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

mysql = MySQL(app)

# Helper Functions
def generate_order_number():
    return 'ORD' + ''.join(random.choices(string.digits, k=8)) + datetime.datetime.now().strftime('%m%d')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login first', 'danger')
                return redirect(url_for('login'))
            if session.get('user_type') not in roles:
                flash('Access denied', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = str(int(datetime.datetime.now().timestamp())) + '_' + filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        return 'uploads/' + unique_filename
    return None

def calculate_distance(lat1, lon1, lat2, lon2):
    # Simple distance calculation (Haversine formula simplified)
    # In production, use proper geolocation library
    return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s AND is_active = TRUE", (username,))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            session['full_name'] = user['full_name']
            
            if user['user_type'] == 'customer':
                return redirect(url_for('customer_dashboard'))
            elif user['user_type'] == 'seller':
                return redirect(url_for('seller_dashboard'))
            elif user['user_type'] == 'delivery':
                return redirect(url_for('delivery_dashboard'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        phone = request.form['phone']
        full_name = request.form['full_name']
        user_type = request.form['user_type']
        address = request.form.get('address', '')
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO users (username, password, email, phone, full_name, user_type, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (username, password, email, phone, full_name, user_type, address))
            
            user_id = cur.lastrowid
            
            if user_type == 'seller':
                restaurant_name = request.form['restaurant_name']
                restaurant_address = request.form['restaurant_address']
                restaurant_phone = request.form['restaurant_phone']
                
                cur.execute("""
                    INSERT INTO sellers (user_id, restaurant_name, restaurant_address, restaurant_phone)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, restaurant_name, restaurant_address, restaurant_phone))
            
            mysql.connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash('Registration failed. Username or email might already exist.', 'danger')
        finally:
            cur.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# Customer Routes
@app.route('/customer/dashboard')
@login_required
@role_required(['customer'])
def customer_dashboard():
    cur = mysql.connection.cursor()
    
    # Get active orders
    cur.execute("""
        SELECT o.*, s.restaurant_name 
        FROM orders o 
        JOIN sellers s ON o.seller_id = s.id 
        WHERE o.customer_id = %s 
        ORDER BY o.created_at DESC LIMIT 5
    """, (session['user_id'],))
    recent_orders = cur.fetchall()
    
    # Get top restaurants
    cur.execute("""
        SELECT s.*, AVG(r.rating) as avg_rating
        FROM sellers s
        LEFT JOIN reviews r ON s.id = r.seller_id
        WHERE s.is_verified = TRUE
        GROUP BY s.id
        ORDER BY avg_rating DESC LIMIT 6
    """)
    restaurants = cur.fetchall()
    
    # Get categories
    cur.execute("SELECT * FROM categories WHERE is_active = TRUE")
    categories = cur.fetchall()
    
    cur.close()
    
    return render_template('customer/dashboard.html', 
                         recent_orders=recent_orders,
                         restaurants=restaurants,
                         categories=categories)

@app.route('/customer/restaurants')
@login_required
@role_required(['customer'])
def customer_restaurants():
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', '')
    
    cur = mysql.connection.cursor()
    
    query = """
        SELECT s.*, AVG(r.rating) as avg_rating, COUNT(DISTINCT fi.id) as menu_items
        FROM sellers s
        LEFT JOIN reviews r ON s.id = r.seller_id
        LEFT JOIN food_items fi ON s.id = fi.seller_id AND fi.is_available = TRUE
        WHERE s.is_verified = TRUE
    """
    params = []
    
    if search:
        query += " AND (s.restaurant_name LIKE %s OR s.restaurant_address LIKE %s)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    if category_id:
        query += " AND fi.category_id = %s"
        params.append(category_id)
    
    query += " GROUP BY s.id ORDER BY avg_rating DESC"
    
    cur.execute(query, params)
    restaurants = cur.fetchall()
    
    cur.execute("SELECT * FROM categories WHERE is_active = TRUE")
    categories = cur.fetchall()
    
    cur.close()
    
    return render_template('customer/restaurants.html',
                         restaurants=restaurants,
                         categories=categories,
                         search=search,
                         selected_category=category_id)

@app.route('/customer/menu/<int:seller_id>')
@login_required
@role_required(['customer'])
def customer_menu(seller_id):
    category_id = request.args.get('category_id', '')
    vegetarian = request.args.get('vegetarian', '')
    
    cur = mysql.connection.cursor()
    
    # Get restaurant info
    cur.execute("SELECT * FROM sellers WHERE id = %s", (seller_id,))
    restaurant = cur.fetchone()
    
    # Get menu items
    query = "SELECT * FROM food_items WHERE seller_id = %s AND is_available = TRUE"
    params = [seller_id]
    
    if category_id:
        query += " AND category_id = %s"
        params.append(category_id)
    
    if vegetarian == 'veg':
        query += " AND is_vegetarian = TRUE"
    elif vegetarian == 'nonveg':
        query += " AND is_vegetarian = FALSE"
    
    query += " ORDER BY name"
    
    cur.execute(query, params)
    menu_items = cur.fetchall()
    
    # Get categories for this restaurant
    cur.execute("""
        SELECT DISTINCT c.* 
        FROM categories c
        JOIN food_items fi ON c.id = fi.category_id
        WHERE fi.seller_id = %s AND fi.is_available = TRUE
        ORDER BY c.name
    """, (seller_id,))
    categories = cur.fetchall()
    
    # Get cart items
    cur.execute("""
        SELECT c.food_item_id, c.quantity, fi.name, fi.price
        FROM cart c
        JOIN food_items fi ON c.food_item_id = fi.id
        WHERE c.customer_id = %s AND fi.seller_id = %s
    """, (session['user_id'], seller_id))
    cart_items = cur.fetchall()
    
    cur.close()
    
    return render_template('customer/menu.html',
                         restaurant=restaurant,
                         menu_items=menu_items,
                         categories=categories,
                         cart_items=cart_items,
                         selected_category=category_id,
                         selected_vegetarian=vegetarian)

@app.route('/customer/add_to_cart', methods=['POST'])
@login_required
@role_required(['customer'])
def add_to_cart():
    food_item_id = request.form['food_item_id']
    quantity = int(request.form['quantity'])
    
    cur = mysql.connection.cursor()
    
    # Check if item already in cart
    cur.execute("SELECT * FROM cart WHERE customer_id = %s AND food_item_id = %s",
                (session['user_id'], food_item_id))
    existing_item = cur.fetchone()
    
    if existing_item:
        new_quantity = existing_item['quantity'] + quantity
        cur.execute("UPDATE cart SET quantity = %s WHERE id = %s",
                    (new_quantity, existing_item['id']))
    else:
        cur.execute("INSERT INTO cart (customer_id, food_item_id, quantity) VALUES (%s, %s, %s)",
                    (session['user_id'], food_item_id, quantity))
    
    mysql.connection.commit()
    cur.close()
    
    flash('Item added to cart successfully', 'success')
    return redirect(request.referrer)

@app.route('/customer/cart')
@login_required
@role_required(['customer'])
def view_cart():
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT c.*, fi.name, fi.price, fi.discount_price, fi.image, 
               s.restaurant_name, s.id as seller_id
        FROM cart c
        JOIN food_items fi ON c.food_item_id = fi.id
        JOIN sellers s ON fi.seller_id = s.id
        WHERE c.customer_id = %s
        ORDER BY s.restaurant_name
    """, (session['user_id'],))
    cart_items = cur.fetchall()
    
    # Group by seller
    cart_by_seller = {}
    total_amount = 0
    
    for item in cart_items:
        seller_id = item['seller_id']
        if seller_id not in cart_by_seller:
            cart_by_seller[seller_id] = {
                'restaurant_name': item['restaurant_name'],
                'items': [],
                'subtotal': 0
            }
        
        price = item['discount_price'] or item['price']
        item_total = price * item['quantity']
        
        cart_by_seller[seller_id]['items'].append(item)
        cart_by_seller[seller_id]['subtotal'] += item_total
        total_amount += item_total
    
    cur.close()
    
    return render_template('customer/cart.html',
                         cart_by_seller=cart_by_seller,
                         total_amount=total_amount)

@app.route('/customer/update_cart', methods=['POST'])
@login_required
@role_required(['customer'])
def update_cart():
    cart_id = request.form['cart_id']
    quantity = int(request.form['quantity'])
    
    cur = mysql.connection.cursor()
    
    if quantity > 0:
        cur.execute("UPDATE cart SET quantity = %s WHERE id = %s AND customer_id = %s",
                    (quantity, cart_id, session['user_id']))
    else:
        cur.execute("DELETE FROM cart WHERE id = %s AND customer_id = %s",
                    (cart_id, session['user_id']))
    
    mysql.connection.commit()
    cur.close()
    
    flash('Cart updated successfully', 'success')
    return redirect(url_for('view_cart'))

@app.route('/customer/checkout', methods=['POST'])
@login_required
@role_required(['customer'])
def checkout():
    delivery_address = request.form['delivery_address']
    payment_method = request.form['payment_method']
    special_instructions = request.form.get('special_instructions', '')
    
    cur = mysql.connection.cursor()
    
    # Get cart items grouped by seller
    cur.execute("""
        SELECT fi.seller_id, SUM(c.quantity) as total_items,
               SUM((fi.discount_price OR fi.price) * c.quantity) as subtotal
        FROM cart c
        JOIN food_items fi ON c.food_item_id = fi.id
        WHERE c.customer_id = %s
        GROUP BY fi.seller_id
    """, (session['user_id'],))
    seller_groups = cur.fetchall()
    
    for group in seller_groups:
        seller_id = group['seller_id']
        subtotal = float(group['subtotal'])
        
        # Calculate delivery charge (example: ₹30 per order)
        delivery_charge = 30.00
        tax_amount = subtotal * 0.05  # 5% tax
        final_amount = subtotal + delivery_charge + tax_amount
        
        # Create order
        order_number = generate_order_number()
        cur.execute("""
            INSERT INTO orders (order_number, customer_id, seller_id, total_amount,
                              delivery_charge, tax_amount, final_amount, delivery_address,
                              payment_method, special_instructions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (order_number, session['user_id'], seller_id, subtotal,
              delivery_charge, tax_amount, final_amount, delivery_address,
              payment_method, special_instructions))
        
        order_id = cur.lastrowid
        
        # Add order tracking
        cur.execute("""
            INSERT INTO order_tracking (order_id, status, notes)
            VALUES (%s, 'pending', 'Order placed successfully')
        """, (order_id,))
        
        # Move cart items to order items
        cur.execute("""
            INSERT INTO order_items (order_id, food_item_id, quantity, price, discount_price)
            SELECT %s, c.food_item_id, c.quantity, fi.price, fi.discount_price
            FROM cart c
            JOIN food_items fi ON c.food_item_id = fi.id
            WHERE c.customer_id = %s AND fi.seller_id = %s
        """, (order_id, session['user_id'], seller_id))
        
        # Clear cart for this seller
        cur.execute("""
            DELETE c FROM cart c
            JOIN food_items fi ON c.food_item_id = fi.id
            WHERE c.customer_id = %s AND fi.seller_id = %s
        """, (session['user_id'], seller_id))
    
    mysql.connection.commit()
    cur.close()
    
    flash('Order placed successfully!', 'success')
    return redirect(url_for('customer_orders'))

@app.route('/customer/orders')
@login_required
@role_required(['customer'])
def customer_orders():
    status_filter = request.args.get('status', '')
    
    cur = mysql.connection.cursor()
    
    query = """
        SELECT o.*, s.restaurant_name, 
               u.full_name as delivery_agent_name,
               (SELECT status FROM order_tracking 
                WHERE order_id = o.id 
                ORDER BY created_at DESC LIMIT 1) as current_status
        FROM orders o
        JOIN sellers s ON o.seller_id = s.id
        LEFT JOIN users u ON o.delivery_agent_id = u.id
        WHERE o.customer_id = %s
    """
    params = [session['user_id']]
    
    if status_filter:
        query += " AND o.order_status = %s"
        params.append(status_filter)
    
    query += " ORDER BY o.created_at DESC"
    
    cur.execute(query, params)
    orders = cur.fetchall()
    
    cur.close()
    
    return render_template('customer/orders.html', orders=orders, status_filter=status_filter)

@app.route('/customer/order/<int:order_id>')
@login_required
@role_required(['customer'])
def customer_order_detail(order_id):
    cur = mysql.connection.cursor()
    
    # Get order details
    cur.execute("""
        SELECT o.*, s.restaurant_name, s.restaurant_phone,
               u.full_name as delivery_agent_name, u.phone as delivery_agent_phone
        FROM orders o
        JOIN sellers s ON o.seller_id = s.id
        LEFT JOIN users u ON o.delivery_agent_id = u.id
        WHERE o.id = %s AND o.customer_id = %s
    """, (order_id, session['user_id']))
    order = cur.fetchone()
    
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('customer_orders'))
    
    # Get order items
    cur.execute("""
        SELECT oi.*, fi.name, fi.image
        FROM order_items oi
        JOIN food_items fi ON oi.food_item_id = fi.id
        WHERE oi.order_id = %s
    """, (order_id,))
    items = cur.fetchall()
    
    # Get tracking history
    cur.execute("""
        SELECT * FROM order_tracking
        WHERE order_id = %s
        ORDER BY created_at DESC
    """, (order_id,))
    tracking = cur.fetchall()
    
    cur.close()
    
    return render_template('customer/order_detail.html',
                         order=order,
                         items=items,
                         tracking=tracking)

# Seller Routes
@app.route('/seller/dashboard')
@login_required
@role_required(['seller'])
def seller_dashboard():
    cur = mysql.connection.cursor()
    
    # Get seller info
    cur.execute("SELECT * FROM sellers WHERE user_id = %s", (session['user_id'],))
    seller = cur.fetchone()
    
    # Get today's stats
    today = datetime.date.today()
    cur.execute("""
        SELECT 
            COUNT(*) as total_orders,
            SUM(final_amount) as total_revenue,
            AVG(final_amount) as avg_order_value
        FROM orders 
        WHERE seller_id = %s AND DATE(created_at) = %s
    """, (seller['id'], today))
    today_stats = cur.fetchone()
    
    # Get recent orders
    cur.execute("""
        SELECT o.*, u.full_name as customer_name,
               (SELECT status FROM order_tracking 
                WHERE order_id = o.id 
                ORDER BY created_at DESC LIMIT 1) as current_status
        FROM orders o
        JOIN users u ON o.customer_id = u.id
        WHERE o.seller_id = %s
        ORDER BY o.created_at DESC
        LIMIT 10
    """, (seller['id'],))
    recent_orders = cur.fetchall()
    
    # Get popular items
    cur.execute("""
        SELECT fi.name, COUNT(oi.id) as order_count, SUM(oi.quantity) as total_quantity
        FROM order_items oi
        JOIN food_items fi ON oi.food_item_id = fi.id
        WHERE fi.seller_id = %s
        GROUP BY fi.id
        ORDER BY total_quantity DESC
        LIMIT 5
    """, (seller['id'],))
    popular_items = cur.fetchall()
    
    cur.close()
    
    return render_template('seller/dashboard.html',
                         seller=seller,
                         today_stats=today_stats,
                         recent_orders=recent_orders,
                         popular_items=popular_items)

@app.route('/seller/orders')
@login_required
@role_required(['seller'])
def seller_orders():
    status_filter = request.args.get('status', '')
    
    cur = mysql.connection.cursor()
    
    # Get seller info
    cur.execute("SELECT * FROM sellers WHERE user_id = %s", (session['user_id'],))
    seller = cur.fetchone()
    
    query = """
        SELECT o.*, u.full_name as customer_name, u.phone as customer_phone,
               (SELECT status FROM order_tracking 
                WHERE order_id = o.id 
                ORDER BY created_at DESC LIMIT 1) as current_status
        FROM orders o
        JOIN users u ON o.customer_id = u.id
        WHERE o.seller_id = %s
    """
    params = [seller['id']]
    
    if status_filter:
        query += " AND o.order_status = %s"
        params.append(status_filter)
    
    query += " ORDER BY o.created_at DESC"
    
    cur.execute(query, params)
    orders = cur.fetchall()
    
    cur.close()
    
    return render_template('seller/orders.html',
                         orders=orders,
                         status_filter=status_filter,
                         seller=seller)

@app.route('/seller/order/<int:order_id>')
@login_required
@role_required(['seller'])
def seller_order_detail(order_id):
    cur = mysql.connection.cursor()
    
    # Get seller info
    cur.execute("SELECT * FROM sellers WHERE user_id = %s", (session['user_id'],))
    seller = cur.fetchone()
    
    # Get order details
    cur.execute("""
        SELECT o.*, u.full_name as customer_name, u.phone as customer_phone,
               u.address as customer_address,
               da.full_name as delivery_agent_name, da.phone as delivery_agent_phone
        FROM orders o
        JOIN users u ON o.customer_id = u.id
        LEFT JOIN users da ON o.delivery_agent_id = da.id
        WHERE o.id = %s AND o.seller_id = %s
    """, (order_id, seller['id']))
    order = cur.fetchone()
    
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('seller_orders'))
    
    # Get order items
    cur.execute("""
        SELECT oi.*, fi.name, fi.image
        FROM order_items oi
        JOIN food_items fi ON oi.food_item_id = fi.id
        WHERE oi.order_id = %s
    """, (order_id,))
    items = cur.fetchall()
    
    # Get tracking history
    cur.execute("""
        SELECT * FROM order_tracking
        WHERE order_id = %s
        ORDER BY created_at ASC
    """, (order_id,))
    tracking = cur.fetchall()
    
    # Get available delivery agents
    cur.execute("""
        SELECT u.*, da.current_latitude, da.current_longitude
        FROM users u
        JOIN delivery_agent_availability da ON u.id = da.delivery_agent_id
        WHERE u.user_type = 'delivery' AND da.is_available = TRUE
    """)
    delivery_agents = cur.fetchall()
    
    cur.close()
    
    return render_template('seller/order_detail.html',
                         order=order,
                         items=items,
                         tracking=tracking,
                         delivery_agents=delivery_agents,
                         seller=seller)

@app.route('/seller/update_order_status', methods=['POST'])
@login_required
@role_required(['seller'])
def update_order_status():
    order_id = request.form['order_id']
    status = request.form['status']
    notes = request.form.get('notes', '')
    
    cur = mysql.connection.cursor()
    
    # Verify seller owns this order
    cur.execute("SELECT seller_id FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
    
    cur.execute("SELECT id FROM sellers WHERE user_id = %s", (session['user_id'],))
    seller = cur.fetchone()
    
    if order['seller_id'] != seller['id']:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('seller_orders'))
    
    # Update order status
    cur.execute("UPDATE orders SET order_status = %s WHERE id = %s",
                (status, order_id))
    
    # Add tracking entry
    cur.execute("""
        INSERT INTO order_tracking (order_id, status, notes)
        VALUES (%s, %s, %s)
    """, (order_id, status, notes))
    
    mysql.connection.commit()
    cur.close()
    
    flash('Order status updated successfully', 'success')
    return redirect(request.referrer)

@app.route('/seller/assign_delivery_agent', methods=['POST'])
@login_required
@role_required(['seller'])
def assign_delivery_agent():
    order_id = request.form['order_id']
    delivery_agent_id = request.form['delivery_agent_id']
    
    cur = mysql.connection.cursor()
    
    # Verify seller owns this order
    cur.execute("SELECT seller_id FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
    
    cur.execute("SELECT id FROM sellers WHERE user_id = %s", (session['user_id'],))
    seller = cur.fetchone()
    
    if order['seller_id'] != seller['id']:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('seller_orders'))
    
    # Update order with delivery agent
    cur.execute("""
        UPDATE orders 
        SET delivery_agent_id = %s, order_status = 'ready'
        WHERE id = %s
    """, (delivery_agent_id, order_id))
    
    # Update delivery agent availability
    cur.execute("""
        UPDATE delivery_agent_availability 
        SET is_available = FALSE 
        WHERE delivery_agent_id = %s
    """, (delivery_agent_id,))
    
    # Add tracking entry
    cur.execute("""
        INSERT INTO order_tracking (order_id, status, notes)
        VALUES (%s, 'ready', 'Order ready for pickup. Delivery agent assigned.')
    """, (order_id,))
    
    mysql.connection.commit()
    cur.close()
    
    flash('Delivery agent assigned successfully', 'success')
    return redirect(request.referrer)

@app.route('/seller/menu')
@login_required
@role_required(['seller'])
def seller_menu():
    cur = mysql.connection.cursor()
    
    # Get seller info
    cur.execute("SELECT * FROM sellers WHERE user_id = %s", (session['user_id'],))
    seller = cur.fetchone()
    
    # Get menu items
    cur.execute("""
        SELECT fi.*, c.name as category_name
        FROM food_items fi
        LEFT JOIN categories c ON fi.category_id = c.id
        WHERE fi.seller_id = %s
        ORDER BY fi.is_available DESC, fi.name
    """, (seller['id'],))
    menu_items = cur.fetchall()
    
    # Get categories
    cur.execute("SELECT * FROM categories WHERE is_active = TRUE")
    categories = cur.fetchall()
    
    cur.close()
    
    return render_template('seller/menu.html',
                         menu_items=menu_items,
                         categories=categories,
                         seller=seller)

@app.route('/seller/add_menu_item', methods=['POST'])
@login_required
@role_required(['seller'])
def add_menu_item():
    name = request.form['name']
    description = request.form['description']
    price = float(request.form['price'])
    discount_price = float(request.form['discount_price']) if request.form.get('discount_price') else None
    category_id = request.form['category_id'] if request.form.get('category_id') else None
    is_vegetarian = 'is_vegetarian' in request.form
    spice_level = request.form['spice_level']
    preparation_time = int(request.form['preparation_time'])
    
    cur = mysql.connection.cursor()
    
    # Get seller info
    cur.execute("SELECT * FROM sellers WHERE user_id = %s", (session['user_id'],))
    seller = cur.fetchone()
    
    # Handle image upload
    image_path = None
    if 'image' in request.files:
        image_file = request.files['image']
        image_path = save_image(image_file)
    
    cur.execute("""
        INSERT INTO food_items (seller_id, category_id, name, description, price, 
                               discount_price, image, is_vegetarian, spice_level, 
                               preparation_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (seller['id'], category_id, name, description, price, discount_price,
          image_path, is_vegetarian, spice_level, preparation_time))
    
    mysql.connection.commit()
    cur.close()
    
    flash('Menu item added successfully', 'success')
    return redirect(url_for('seller_menu'))

@app.route('/seller/update_menu_item', methods=['POST'])
@login_required
@role_required(['seller'])
def update_menu_item():
    item_id = request.form['item_id']
    name = request.form['name']
    description = request.form['description']
    price = float(request.form['price'])
    discount_price = float(request.form['discount_price']) if request.form.get('discount_price') else None
    category_id = request.form['category_id'] if request.form.get('category_id') else None
    is_vegetarian = 'is_vegetarian' in request.form
    spice_level = request.form['spice_level']
    preparation_time = int(request.form['preparation_time'])
    is_available = 'is_available' in request.form
    
    cur = mysql.connection.cursor()
    
    # Verify seller owns this item
    cur.execute("SELECT seller_id FROM food_items WHERE id = %s", (item_id,))
    item = cur.fetchone()
    
    cur.execute("SELECT id FROM sellers WHERE user_id = %s", (session['user_id'],))
    seller = cur.fetchone()
    
    if item['seller_id'] != seller['id']:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('seller_menu'))
    
    # Handle image upload
    image_path = None
    if 'image' in request.files:
        image_file = request.files['image']
        if image_file.filename:
            image_path = save_image(image_file)
    
    update_query = """
        UPDATE food_items 
        SET name = %s, description = %s, price = %s, discount_price = %s,
            category_id = %s, is_vegetarian = %s, spice_level = %s,
            preparation_time = %s, is_available = %s
    """
    params = [name, description, price, discount_price, category_id,
              is_vegetarian, spice_level, preparation_time, is_available]
    
    if image_path:
        update_query += ", image = %s"
        params.append(image_path)
    
    update_query += " WHERE id = %s"
    params.append(item_id)
    
    cur.execute(update_query, params)
    
    mysql.connection.commit()
    cur.close()
    
    flash('Menu item updated successfully', 'success')
    return redirect(url_for('seller_menu'))

@app.route('/seller/analytics')
@login_required
@role_required(['seller'])
def seller_analytics():
    period = request.args.get('period', 'week')  # day, week, month, year
    chart_type = request.args.get('chart', 'revenue')  # revenue, orders, items
    
    cur = mysql.connection.cursor()
    
    # Get seller info
    cur.execute("SELECT * FROM sellers WHERE user_id = %s", (session['user_id'],))
    seller = cur.fetchone()
    
    # Calculate date range based on period
    end_date = datetime.date.today()
    if period == 'day':
        start_date = end_date
    elif period == 'week':
        start_date = end_date - datetime.timedelta(days=7)
    elif period == 'month':
        start_date = end_date - datetime.timedelta(days=30)
    else:  # year
        start_date = end_date - datetime.timedelta(days=365)
    
    # Get sales data
    cur.execute("""
        SELECT DATE(created_at) as date, 
               COUNT(*) as order_count,
               SUM(final_amount) as total_revenue,
               AVG(final_amount) as avg_order_value
        FROM orders
        WHERE seller_id = %s AND created_at >= %s AND created_at <= %s
        GROUP BY DATE(created_at)
        ORDER BY date
    """, (seller['id'], start_date, end_date))
    sales_data = cur.fetchall()
    
    # Get top selling items
    cur.execute("""
        SELECT fi.name, SUM(oi.quantity) as total_quantity, 
               SUM(oi.quantity * oi.price) as total_revenue
        FROM order_items oi
        JOIN food_items fi ON oi.food_item_id = fi.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.seller_id = %s AND o.created_at >= %s AND o.created_at <= %s
        GROUP BY fi.id
        ORDER BY total_quantity DESC
        LIMIT 10
    """, (seller['id'], start_date, end_date))
    top_items = cur.fetchall()
    
    # Get order status distribution
    cur.execute("""
        SELECT order_status, COUNT(*) as count
        FROM orders
        WHERE seller_id = %s AND created_at >= %s AND created_at <= %s
        GROUP BY order_status
    """, (seller['id'], start_date, end_date))
    status_distribution = cur.fetchall()
    
    cur.close()
    
    return render_template('seller/analytics.html',
                         sales_data=sales_data,
                         top_items=top_items,
                         status_distribution=status_distribution,
                         period=period,
                         chart_type=chart_type,
                         seller=seller)

# Delivery Agent Routes
@app.route('/delivery/dashboard')
@login_required
@role_required(['delivery'])
def delivery_dashboard():
    cur = mysql.connection.cursor()
    
    # Get assigned orders
    cur.execute("""
        SELECT o.*, s.restaurant_name, s.restaurant_address,
               u.full_name as customer_name, u.address as customer_address,
               (SELECT status FROM order_tracking 
                WHERE order_id = o.id 
                ORDER BY created_at DESC LIMIT 1) as current_status
        FROM orders o
        JOIN sellers s ON o.seller_id = s.id
        JOIN users u ON o.customer_id = u.id
        WHERE o.delivery_agent_id = %s 
        AND o.order_status NOT IN ('delivered', 'cancelled')
        ORDER BY o.created_at DESC
    """, (session['user_id'],))
    active_orders = cur.fetchall()
    
    # Get delivery stats
    today = datetime.date.today()
    cur.execute("""
        SELECT 
            COUNT(*) as total_deliveries,
            SUM(final_amount) as total_value,
            AVG(TIMESTAMPDIFF(MINUTE, created_at, updated_at)) as avg_delivery_time
        FROM orders 
        WHERE delivery_agent_id = %s 
        AND DATE(created_at) = %s
        AND order_status = 'delivered'
    """, (session['user_id'], today))
    today_stats = cur.fetchone()
    
    # Update availability
    cur.execute("""
        INSERT INTO delivery_agent_availability (delivery_agent_id, is_available)
        VALUES (%s, TRUE)
        ON DUPLICATE KEY UPDATE last_active = CURRENT_TIMESTAMP
    """, (session['user_id'],))
    
    mysql.connection.commit()
    cur.close()
    
    return render_template('delivery/dashboard.html',
                         active_orders=active_orders,
                         today_stats=today_stats)

@app.route('/delivery/orders')
@login_required
@role_required(['delivery'])
def delivery_orders():
    status_filter = request.args.get('status', '')
    
    cur = mysql.connection.cursor()
    
    query = """
        SELECT o.*, s.restaurant_name, s.restaurant_address,
               u.full_name as customer_name, u.address as customer_address,
               (SELECT status FROM order_tracking 
                WHERE order_id = o.id 
                ORDER BY created_at DESC LIMIT 1) as current_status
        FROM orders o
        JOIN sellers s ON o.seller_id = s.id
        JOIN users u ON o.customer_id = u.id
        WHERE o.delivery_agent_id = %s
    """
    params = [session['user_id']]
    
    if status_filter:
        query += " AND o.order_status = %s"
        params.append(status_filter)
    
    query += " ORDER BY o.created_at DESC"
    
    cur.execute(query, params)
    orders = cur.fetchall()
    
    cur.close()
    
    return render_template('delivery/orders.html',
                         orders=orders,
                         status_filter=status_filter)

@app.route('/delivery/order/<int:order_id>')
@login_required
@role_required(['delivery'])
def delivery_order_detail(order_id):
    cur = mysql.connection.cursor()
    
    # Get order details
    cur.execute("""
        SELECT o.*, s.restaurant_name, s.restaurant_address, s.restaurant_phone,
               u.full_name as customer_name, u.phone as customer_phone,
               u.address as customer_address
        FROM orders o
        JOIN sellers s ON o.seller_id = s.id
        JOIN users u ON o.customer_id = u.id
        WHERE o.id = %s AND o.delivery_agent_id = %s
    """, (order_id, session['user_id']))
    order = cur.fetchone()
    
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('delivery_orders'))
    
    # Get order items
    cur.execute("""
        SELECT oi.*, fi.name
        FROM order_items oi
        JOIN food_items fi ON oi.food_item_id = fi.id
        WHERE oi.order_id = %s
    """, (order_id,))
    items = cur.fetchall()
    
    # Get tracking history
    cur.execute("""
        SELECT * FROM order_tracking
        WHERE order_id = %s
        ORDER BY created_at ASC
    """, (order_id,))
    tracking = cur.fetchall()
    
    cur.close()
    
    return render_template('delivery/order_detail.html',
                         order=order,
                         items=items,
                         tracking=tracking)

@app.route('/delivery/update_order_status', methods=['POST'])
@login_required
@role_required(['delivery'])
def delivery_update_order_status():
    order_id = request.form['order_id']
    status = request.form['status']
    notes = request.form.get('notes', '')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    
    cur = mysql.connection.cursor()
    
    # Verify delivery agent is assigned to this order
    cur.execute("SELECT delivery_agent_id FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
    
    if order['delivery_agent_id'] != session['user_id']:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('delivery_orders'))
    
    # Update order status
    cur.execute("UPDATE orders SET order_status = %s WHERE id = %s",
                (status, order_id))
    
    # Add tracking entry
    cur.execute("""
        INSERT INTO order_tracking (order_id, status, notes, location_latitude, location_longitude)
        VALUES (%s, %s, %s, %s, %s)
    """, (order_id, status, notes, latitude, longitude))
    
    # If delivered, make agent available again
    if status == 'delivered':
        cur.execute("""
            UPDATE delivery_agent_availability 
            SET is_available = TRUE 
            WHERE delivery_agent_id = %s
        """, (session['user_id'],))
    
    mysql.connection.commit()
    cur.close()
    
    flash('Order status updated successfully', 'success')
    return redirect(request.referrer)

@app.route('/delivery/update_availability', methods=['POST'])
@login_required
@role_required(['delivery'])
def update_availability():
    is_available = 'is_available' in request.form
    
    cur = mysql.connection.cursor()
    
    cur.execute("""
        UPDATE delivery_agent_availability 
        SET is_available = %s, last_active = CURRENT_TIMESTAMP
        WHERE delivery_agent_id = %s
    """, (is_available, session['user_id']))
    
    mysql.connection.commit()
    cur.close()
    
    status = "available" if is_available else "unavailable"
    flash(f'You are now {status}', 'success')
    return redirect(url_for('delivery_dashboard'))

@app.route('/delivery/history')
@login_required
@role_required(['delivery'])
def delivery_history():
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT o.*, s.restaurant_name, u.full_name as customer_name,
               TIMESTAMPDIFF(MINUTE, o.created_at, o.updated_at) as delivery_time
        FROM orders o
        JOIN sellers s ON o.seller_id = s.id
        JOIN users u ON o.customer_id = u.id
        WHERE o.delivery_agent_id = %s 
        AND o.order_status = 'delivered'
        ORDER BY o.updated_at DESC
        LIMIT 50
    """, (session['user_id'],))
    delivery_history = cur.fetchall()
    
    cur.close()
    
    return render_template('delivery/history.html',
                         delivery_history=delivery_history)

# Static file serving
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/cart_count')
@login_required
def get_cart_count():
    if session.get('user_type') != 'customer':
        return {'count': 0}
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as count FROM cart WHERE customer_id = %s", (session['user_id'],))
    result = cur.fetchone()
    cur.close()
    
    return {'count': result['count'] if result else 0}

@app.route('/api/order_stats')
@login_required
@role_required(['seller'])
def get_order_stats():
    period = request.args.get('period', 'today')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM sellers WHERE user_id = %s", (session['user_id'],))
    seller = cur.fetchone()
    
    if period == 'today':
        cur.execute("""
            SELECT COUNT(*) as orders, SUM(final_amount) as revenue
            FROM orders 
            WHERE seller_id = %s AND DATE(created_at) = CURDATE()
        """, (seller['id'],))
    elif period == 'week':
        cur.execute("""
            SELECT COUNT(*) as orders, SUM(final_amount) as revenue
            FROM orders 
            WHERE seller_id = %s AND created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """, (seller['id'],))
    elif period == 'month':
        cur.execute("""
            SELECT COUNT(*) as orders, SUM(final_amount) as revenue
            FROM orders 
            WHERE seller_id = %s AND created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """, (seller['id'],))
    
    stats = cur.fetchone()
    cur.close()
    
    return {
        'orders': stats['orders'] or 0,
        'revenue': float(stats['revenue'] or 0)
    }
# Add these routes for seller and delivery features

@app.route('/seller/update_restaurant', methods=['POST'])
@login_required
@role_required(['seller'])
def update_restaurant():
    restaurant_name = request.form['restaurant_name']
    restaurant_phone = request.form['restaurant_phone']
    restaurant_address = request.form['restaurant_address']
    
    cur = mysql.connection.cursor()
    
    # Get seller ID
    cur.execute("SELECT id FROM sellers WHERE user_id = %s", (session['user_id'],))
    seller = cur.fetchone()
    
    cur.execute("""
        UPDATE sellers 
        SET restaurant_name = %s, restaurant_phone = %s, restaurant_address = %s 
        WHERE id = %s
    """, (restaurant_name, restaurant_phone, restaurant_address, seller['id']))
    
    mysql.connection.commit()
    cur.close()
    
    flash('Restaurant information updated successfully', 'success')
    return redirect(url_for('seller_dashboard'))

@app.route('/seller/delete_menu_item', methods=['POST'])
@login_required
@role_required(['seller'])
def delete_menu_item():
    item_id = request.form['item_id']
    
    cur = mysql.connection.cursor()
    
    # Verify seller owns this item
    cur.execute("SELECT seller_id FROM food_items WHERE id = %s", (item_id,))
    item = cur.fetchone()
    
    cur.execute("SELECT id FROM sellers WHERE user_id = %s", (session['user_id'],))
    seller = cur.fetchone()
    
    if item and item['seller_id'] == seller['id']:
        cur.execute("DELETE FROM food_items WHERE id = %s", (item_id,))
        mysql.connection.commit()
        flash('Menu item deleted successfully', 'success')
    else:
        flash('Unauthorized action or item not found', 'danger')
    
    cur.close()
    return redirect(url_for('seller_menu'))

@app.route('/delivery/earnings')
@login_required
@role_required(['delivery'])
def delivery_earnings():
    cur = mysql.connection.cursor()
    
    # Get current month earnings
    cur.execute("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as deliveries,
            SUM(final_amount) as total_value,
            SUM(final_amount * 0.15) as earnings  # 15% commission
        FROM orders 
        WHERE delivery_agent_id = %s 
            AND order_status = 'delivered'
            AND MONTH(created_at) = MONTH(CURDATE())
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """, (session['user_id'],))
    
    earnings_data = cur.fetchall()
    
    # Get total earnings
    cur.execute("""
        SELECT 
            COUNT(*) as total_deliveries,
            SUM(final_amount) as total_value,
            SUM(final_amount * 0.15) as total_earnings
        FROM orders 
        WHERE delivery_agent_id = %s 
            AND order_status = 'delivered'
    """, (session['user_id'],))
    
    totals = cur.fetchone()
    
    cur.close()
    
    # For now, we'll just redirect to history
    # You can create a separate earnings.html template if needed
    return redirect(url_for('delivery_history'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)