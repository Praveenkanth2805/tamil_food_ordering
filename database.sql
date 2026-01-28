-- Food Ordering System - Tamil Nadu Style
DROP DATABASE IF EXISTS tamil_food_ordering;
CREATE DATABASE tamil_food_ordering;
USE tamil_food_ordering;

-- Users table (for all portal users)
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    user_type ENUM('customer', 'seller', 'delivery') NOT NULL,
    address TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    profile_image VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sellers table (additional seller info)
CREATE TABLE sellers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    restaurant_name VARCHAR(200) NOT NULL,
    restaurant_address TEXT NOT NULL,
    restaurant_phone VARCHAR(15),
    gst_number VARCHAR(50),
    license_number VARCHAR(100),
    restaurant_image VARCHAR(255),
    rating DECIMAL(3,2) DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Food Categories
CREATE TABLE categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    image VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);

-- Food Items
CREATE TABLE food_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    seller_id INT NOT NULL,
    category_id INT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    discount_price DECIMAL(10,2),
    image VARCHAR(255),
    is_vegetarian BOOLEAN DEFAULT TRUE,
    spice_level ENUM('mild', 'medium', 'hot', 'extra_hot') DEFAULT 'medium',
    is_available BOOLEAN DEFAULT TRUE,
    preparation_time INT, -- in minutes
    rating DECIMAL(3,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- Orders
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INT NOT NULL,
    seller_id INT NOT NULL,
    delivery_agent_id INT,
    total_amount DECIMAL(10,2) NOT NULL,
    delivery_charge DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    final_amount DECIMAL(10,2) NOT NULL,
    delivery_address TEXT NOT NULL,
    delivery_latitude DECIMAL(10, 8),
    delivery_longitude DECIMAL(11, 8),
    payment_method ENUM('cash_on_delivery', 'online_payment') DEFAULT 'cash_on_delivery',
    payment_status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    order_status ENUM('pending', 'confirmed', 'preparing', 'ready', 'picked_up', 'on_the_way', 'delivered', 'cancelled') DEFAULT 'pending',
    special_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE,
    FOREIGN KEY (delivery_agent_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Order Items
CREATE TABLE order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    food_item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    price DECIMAL(10,2) NOT NULL,
    discount_price DECIMAL(10,2),
    special_instructions TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE CASCADE
);

-- Order Tracking
CREATE TABLE order_tracking (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    status ENUM('pending', 'confirmed', 'preparing', 'ready', 'picked_up', 'on_the_way', 'delivered', 'cancelled') NOT NULL,
    notes TEXT,
    location_latitude DECIMAL(10, 8),
    location_longitude DECIMAL(11, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Delivery Agent Availability
CREATE TABLE delivery_agent_availability (
    id INT PRIMARY KEY AUTO_INCREMENT,
    delivery_agent_id INT UNIQUE NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    current_latitude DECIMAL(10, 8),
    current_longitude DECIMAL(11, 8),
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (delivery_agent_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Cart
CREATE TABLE cart (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    food_item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE CASCADE,
    UNIQUE KEY unique_cart_item (customer_id, food_item_id)
);

-- Reviews and Ratings
CREATE TABLE reviews (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    customer_id INT NOT NULL,
    food_item_id INT,
    seller_id INT,
    delivery_agent_id INT,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    review_type ENUM('food', 'seller', 'delivery'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE SET NULL,
    FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE SET NULL,
    FOREIGN KEY (delivery_agent_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Insert Tamil Nadu specific categories
INSERT INTO categories (name, description) VALUES
('சைவ உணவுகள் (Vegetarian)', 'பாரம்பரிய தமிழக சைவ உணவுகள்'),
('அசைவ உணவுகள் (Non-Vegetarian)', 'சுவையான அசைவ உணவுகள்'),
('சிற்றுண்டி (Snacks)', 'தினசரி சிற்றுண்டி வகைகள்'),
('இடியாப்பம் & தோசை', 'தமிழ்நாட்டு பிரபல இடியாப்பம் மற்றும் தோசை'),
('பிரியாணி & இரைச்சல்', 'சுவையான பிரியாணி மற்றும் இரைச்சல் வகைகள்'),
('குளிர்பானங்கள் (Beverages)', 'பாரம்பரிய குளிர்பானங்கள்'),
('இனிப்புகள் (Sweets)', 'தமிழ்நாட்டு இனிப்பு வகைகள்');

-- Create indexes for better performance
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_seller ON orders(seller_id);
CREATE INDEX idx_orders_delivery ON orders(delivery_agent_id);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_food_seller ON food_items(seller_id);
CREATE INDEX idx_order_tracking_order ON order_tracking(order_id);
CREATE INDEX idx_cart_customer ON cart(customer_id);