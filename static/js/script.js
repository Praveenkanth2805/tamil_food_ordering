// Main JavaScript for Tamil Food Ordering System

$(document).ready(function() {
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Update cart count
    updateCartCount();
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
});

// Update cart count via AJAX
function updateCartCount() {
    $.ajax({
        url: '/api/cart_count',
        method: 'GET',
        success: function(data) {
            if(data.count > 0) {
                $('#cart-count').text(data.count).show();
            } else {
                $('#cart-count').hide();
            }
        }
    });
}

// Add item to cart
function addToCart(foodItemId, quantity) {
    $.ajax({
        url: '/customer/add_to_cart',
        method: 'POST',
        data: {
            food_item_id: foodItemId,
            quantity: quantity || 1
        },
        success: function(response) {
            updateCartCount();
            showNotification('Item added to cart!', 'success');
        },
        error: function() {
            showNotification('Failed to add item to cart', 'danger');
        }
    });
}

// Show notification
function showNotification(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999;">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('body').append(alertHtml);
    
    setTimeout(function() {
        $('.alert').alert('close');
    }, 3000);
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Get current location for delivery tracking
function getCurrentLocation(callback) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                callback({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                });
            },
            function(error) {
                console.error('Error getting location:', error);
                callback(null);
            }
        );
    } else {
        console.error('Geolocation not supported');
        callback(null);
    }
}

// Format price
function formatPrice(price) {
    return '₹' + parseFloat(price).toFixed(2);
}

// Calculate delivery time estimate
function calculateDeliveryTime(distanceInKm) {
    const baseTime = 20; // minutes
    const timePerKm = 2; // minutes per km
    return baseTime + (distanceInKm * timePerKm);
}