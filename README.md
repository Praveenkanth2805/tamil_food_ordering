# 🍛 Tamil Nadu Food Ordering System

A comprehensive food ordering website specifically designed for Tamil Nadu cuisine with three portals: Customer, Seller (Restaurant), and Delivery Agent.

## 🚀 Project Overview

This is a **Flask-based web application** for ordering authentic Tamil Nadu food. The system features three distinct user portals with role-based access control, real-time order tracking, and a responsive UI.

> **Note:** This project was developed with assistance from AI (Claude/DeepSeek) for code generation, debugging, and optimization.

## ✨ Features

### 👨‍🍳 **Customer Portal**
- Browse Tamil Nadu restaurants and menus
- Add items to cart and checkout
- Real-time order tracking
- View order history
- Filter by categories (Vegetarian/Non-vegetarian, spice levels)
- Tamil cuisine specific categories

### 🏪 **Seller/Restaurant Portal**
- Menu management (add/edit/delete items)
- Process and track customer orders
- Assign delivery agents based on location
- View sales analytics and charts
- Update order status
- Restaurant profile management

### 🛵 **Delivery Agent Portal**
- View assigned orders
- Update delivery status (picked up, on the way, delivered)
- Live location tracking
- Update availability status
- View delivery history and earnings
- Contact customers/restaurants

### 🎯 **System Features**
- User authentication and role-based access
- Real-time order tracking with status updates
- Responsive design (mobile-friendly)
- Tamil Nadu cuisine focus with Tamil interface elements
- MySQL database with proper relationships
- File upload for food images
- Analytics and reporting for sellers

## 🛠️ **Technology Stack**

### **Backend**
- **Python Flask** - Web framework
- **MySQL** - Database
- **Flask-MySQLdb** - MySQL integration
- **Werkzeug** - Security and file handling

### **Frontend**
- **HTML5** - Templates with Jinja2
- **CSS3** - Custom styling with responsive design
- **JavaScript** - Interactive features
- **Bootstrap 5** - UI components
- **Font Awesome** - Icons
- **Chart.js** - Analytics charts

### **Database**
- MySQL with proper normalization
- User roles: Customer, Seller, Delivery
- Order tracking system
- Cart management
- Reviews and ratings

## 📦 **Installation**

### **Prerequisites**
- Python 3.8+
- MySQL Server
- pip (Python package manager)

### **Step 1: Clone and Setup**
```bash
git clone <repository-url>
cd tamil_food_ordering
```

### **Step 2: Install Dependencies**
```bash
pip install flask flask-mysqldb werkzeug
```

### **Step 3: Database Setup**
1. Start MySQL server
2. Create database user (if needed)
3. Import database schema:
```bash
mysql -u root -p < database.sql
```

### **Step 4: Configuration**
Edit `config.py` with your MySQL credentials:
```python
MYSQL_HOST = 'localhost'
MYSQL_USER = 'your_username'
MYSQL_PASSWORD = 'your_password'
MYSQL_DB = 'tamil_food_ordering'
SECRET_KEY = 'your-secret-key-change-in-production'
```

### **Step 5: Run the Application**
```bash
python app.py
```

### **Step 6: Access the Application**
Open browser and navigate to:
```
http://localhost:5000
```

## 📁 **Project Structure**

```
tamil_food_ordering/
│
├── app.py                    # Main Flask application
├── config.py                # Configuration file
├── database.sql            # MySQL database schema
│
├── static/
│   ├── css/
│   │   └── style.css      # Main stylesheet
│   ├── js/
│   │   └── script.js      # JavaScript functions
│   ├── images/            # Store images
│   └── uploads/           # Uploaded files
│
└── templates/
    ├── base.html          # Base template
    ├── index.html         # Home page
    ├── login.html         # Login page
    ├── register.html      # Registration page
    │
    ├── customer/          # Customer portal
    │   ├── dashboard.html
    │   ├── restaurants.html
    │   ├── menu.html
    │   ├── cart.html
    │   ├── orders.html
    │   └── order_detail.html
    │
    ├── seller/           # Seller/restaurant portal
    │   ├── dashboard.html
    │   ├── orders.html
    │   ├── order_detail.html
    │   ├── menu.html
    │   └── analytics.html
    │
    └── delivery/         # Delivery agent portal
        ├── dashboard.html
        ├── orders.html
        ├── order_detail.html
        └── history.html
```

## 🗄️ **Database Schema**

Key tables:
- `users` - All user accounts (customer, seller, delivery)
- `sellers` - Restaurant information
- `food_items` - Menu items with Tamil cuisine attributes
- `orders` - Order management
- `order_tracking` - Real-time status updates
- `cart` - Shopping cart
- `categories` - Tamil food categories

## 👥 **User Roles**

### **1. Customer**
- Can browse restaurants and menus
- Add items to cart and place orders
- Track order status in real-time
- View order history

### **2. Seller (Restaurant Owner)**
- Manage restaurant menu
- Process incoming orders
- Assign delivery agents
- View sales analytics
- Update order status

### **3. Delivery Agent**
- Accept assigned orders
- Update delivery status
- Share live location
- Mark orders as delivered
- View delivery history

## 🔐 **Authentication Flow**

1. **Registration**: Users register with specific role
2. **Login**: Role-based dashboard access
3. **Session Management**: Secure session handling
4. **Role-Based Access**: Each portal accessible only to authorized users

## 🎨 **UI/UX Features**

- **Responsive Design**: Works on mobile and desktop
- **Tamil Theme**: Colors and styling inspired by Tamil Nadu culture
- **Intuitive Navigation**: Easy-to-use interface for all user types
- **Real-time Updates**: Order tracking with visual progress
- **Analytics Dashboard**: Charts and graphs for sellers

## 🔧 **API Endpoints**

### **Authentication**
- `GET/POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - User logout

### **Customer**
- `GET /customer/dashboard` - Customer dashboard
- `GET /customer/restaurants` - Browse restaurants
- `GET /customer/menu/<seller_id>` - View restaurant menu
- `GET /customer/cart` - Shopping cart
- `POST /customer/checkout` - Place order

### **Seller**
- `GET /seller/dashboard` - Seller dashboard
- `GET /seller/orders` - View orders
- `POST /seller/update_order_status` - Update order status
- `POST /seller/assign_delivery_agent` - Assign delivery agent

### **Delivery**
- `GET /delivery/dashboard` - Delivery dashboard
- `POST /delivery/update_order_status` - Update delivery status
- `POST /delivery/update_availability` - Update availability

## 🚨 **Error Handling**

- Form validation and error messages
- Database constraint handling
- File upload validation
- Role-based access control
- Session timeout handling

## 📱 **Responsive Design**

- Mobile-first approach
- Bootstrap 5 grid system
- Flexible images and media
- Touch-friendly interfaces
- Cross-browser compatibility

## 🔒 **Security Features**

- Password hashing with Werkzeug
- SQL injection prevention
- XSS protection
- File upload validation
- Session security
- Role-based authorization

## 🚀 **Deployment Notes**

### **Production Recommendations**
1. Change `SECRET_KEY` in production
2. Use environment variables for credentials
3. Implement HTTPS
4. Add rate limiting
5. Set up proper logging
6. Use production WSGI server (Gunicorn)
7. Configure MySQL for production
8. Set up backup system

### **Scaling Considerations**
- Implement caching (Redis)
- Add CDN for static files
- Database connection pooling
- Load balancing for multiple instances
- Queue system for orders

## 🤖 **AI-Assisted Development**

This project was developed with **AI assistance** for:
- **Code Generation**: Flask routes, HTML templates, JavaScript functions
- **Debugging**: Error resolution and optimization
- **Database Design**: Schema creation and optimization
- **UI/UX**: Responsive design implementation
- **Documentation**: Code comments and explanations

**AI Tools Used**: Claude/DeepSeek for iterative development and problem-solving

## 📈 **Future Enhancements**

### **Planned Features**
1. **Payment Integration** - Razorpay/Stripe
2. **SMS/Email Notifications**
3. **Push Notifications**
4. **Advanced Search** - Geolocation, cuisine filters
5. **Ratings and Reviews**
6. **Loyalty Program**
7. **Bulk Ordering**
8. **Multi-language Support** (Tamil/English)

### **Technical Improvements**
1. **API Versioning**
2. **WebSocket for real-time updates**
3. **Microservices architecture**
4. **Docker containerization**
5. **CI/CD Pipeline**
6. **Automated Testing**

## 🐛 **Troubleshooting**

### **Common Issues**

1. **MySQL Connection Error**
   - Check MySQL service is running
   - Verify credentials in config.py
   - Ensure database exists

2. **Template Errors**
   - Check Jinja2 syntax
   - Verify template file paths
   - Ensure proper variable passing

3. **File Upload Issues**
   - Check upload folder permissions
   - Verify file size limits
   - Ensure correct MIME types

4. **Session Problems**
   - Clear browser cache
   - Check SECRET_KEY configuration
   - Verify session cookie settings

### **Debug Mode**
Enable debug mode in `app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

## 📚 **Learning Resources**

### **For Developers**
- [Flask Documentation](https://flask.palletsprojects.com/)
- [MySQL Documentation](https://dev.mysql.com/doc/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.0/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)

### **For Users**
- User guides for each portal
- FAQ section
- Video tutorials

## 👥 **Contributing**

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 **Acknowledgements**

- **Tamil Nadu Cuisine** - For culinary inspiration
- **Flask Community** - For excellent documentation
- **Bootstrap Team** - For responsive components
- **AI Assistants** - For development support and guidance

## 📞 **Support**

For support, email: support@tamilfoodordering.com

## 🎯 **Project Status**

**Current Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: January 2024

---

**Enjoy ordering authentic Tamil Nadu food!** 🍛✨