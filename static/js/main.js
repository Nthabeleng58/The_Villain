// Main JavaScript functionality for The Villain Food-App

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize cart functionality
    initializeCart();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize any charts if present
    initializeCharts();
}

// Cart Management
function initializeCart() {
    let cart = JSON.parse(localStorage.getItem('villainCart')) || [];
    updateCartCount();
    
    // Cart count in navigation
    function updateCartCount() {
        const cartCount = document.querySelector('.cart-count');
        if (cartCount) {
            const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
            cartCount.textContent = totalItems;
        }
    }
    
    // Add to cart function (can be called from menu pages)
    window.addToCart = function(menuItemId, name, price, image) {
        const existingItem = cart.find(item => item.id === menuItemId);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cart.push({
                id: menuItemId,
                name: name,
                price: price,
                image: image,
                quantity: 1
            });
        }
        
        localStorage.setItem('villainCart', JSON.stringify(cart));
        updateCartCount();
        
        // Show notification
        showNotification(`${name} added to cart!`, 'success');
    };
    
    // Remove from cart
    window.removeFromCart = function(menuItemId) {
        cart = cart.filter(item => item.id !== menuItemId);
        localStorage.setItem('villainCart', JSON.stringify(cart));
        updateCartCount();
        showNotification('Item removed from cart', 'info');
        
        // Refresh cart display if on cart page
        if (window.location.pathname.includes('/cart')) {
            displayCartItems();
        }
    };
    
    // Update quantity
    window.updateQuantity = function(menuItemId, change) {
        const item = cart.find(item => item.id === menuItemId);
        if (item) {
            item.quantity += change;
            if (item.quantity <= 0) {
                removeFromCart(menuItemId);
                return;
            }
            localStorage.setItem('villainCart', JSON.stringify(cart));
            updateCartCount();
            displayCartItems();
        }
    };
    
    // Display cart items on cart page
    window.displayCartItems = function() {
        const cartItemsContainer = document.getElementById('cart-items');
        const cartTotalElement = document.getElementById('cart-total');
        
        if (cartItemsContainer && cartTotalElement) {
            if (cart.length === 0) {
                cartItemsContainer.innerHTML = '<p class="empty-cart">Your cart is empty</p>';
                cartTotalElement.textContent = '0.00';
                return;
            }
            
            let total = 0;
            let itemsHTML = '';
            
            cart.forEach(item => {
                const itemTotal = item.price * item.quantity;
                total += itemTotal;
                
                itemsHTML += `
                    <div class="cart-item">
                        <img src="${item.image || '/images/placeholder-food.jpg'}" alt="${item.name}">
                        <div class="item-details">
                            <h4>${item.name}</h4>
                            <p>$${item.price.toFixed(2)}</p>
                        </div>
                        <div class="quantity-controls">
                            <button onclick="updateQuantity(${item.id}, -1)">-</button>
                            <span>${item.quantity}</span>
                            <button onclick="updateQuantity(${item.id}, 1)">+</button>
                        </div>
                        <div class="item-total">
                            $${itemTotal.toFixed(2)}
                        </div>
                        <button class="remove-btn" onclick="removeFromCart(${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
            });
            
            cartItemsContainer.innerHTML = itemsHTML;
            cartTotalElement.textContent = total.toFixed(2);
        }
    };
}

// Search functionality
function initializeSearch() {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            filterRestaurants(searchTerm);
        });
    }
}

function filterRestaurants(searchTerm = '') {
    const restaurantCards = document.querySelectorAll('.restaurant-card');
    const term = searchTerm.toLowerCase();

    restaurantCards.forEach(card => {
        const nameEl = card.querySelector('.restaurant-name');
        const cuisineEl = card.querySelector('.restaurant-cuisine');
        const name = nameEl ? nameEl.textContent.toLowerCase() : (card.dataset.name || '').toLowerCase();
        const cuisine = cuisineEl ? cuisineEl.textContent.toLowerCase() : (card.dataset.cuisine || '').toLowerCase();
        const matches = !term || name.includes(term) || cuisine.includes(term);
        card.style.display = matches ? 'block' : 'none';
    });
}

// Form validations
function initializeFormValidations() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            showFormError(input, 'This field is required');
            isValid = false;
        } else {
            clearFormError(input);
        }
        
        // Email validation
        if (input.type === 'email' && input.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(input.value)) {
                showFormError(input, 'Please enter a valid email address');
                isValid = false;
            }
        }
        
        // Password confirmation
        if (input.name === 'confirm_password' && input.value) {
            const password = form.querySelector('input[name="password"]');
            if (password && password.value !== input.value) {
                showFormError(input, 'Passwords do not match');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

function showFormError(input, message) {
    clearFormError(input);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'form-error';
    errorDiv.textContent = message;
    errorDiv.style.color = '#FF4757';
    errorDiv.style.fontSize = '0.8rem';
    errorDiv.style.marginTop = '0.25rem';
    
    input.style.borderColor = '#FF4757';
    input.parentNode.appendChild(errorDiv);
}

function clearFormError(input) {
    const existingError = input.parentNode.querySelector('.form-error');
    if (existingError) {
        existingError.remove();
    }
    input.style.borderColor = '';
}

// Notification system
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notif => notif.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">&times;</button>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        z-index: 1001;
        display: flex;
        align-items: center;
        gap: 1rem;
        min-width: 300px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
    `;
    
    if (type === 'success') {
        notification.style.background = '#4CAF50';
    } else if (type === 'error') {
        notification.style.background = '#FF4757';
    } else {
        notification.style.background = '#8B5FBF';
    }
    
    notification.querySelector('button').style.cssText = `
        background: none;
        border: none;
        color: white;
        font-size: 1.2rem;
        cursor: pointer;
        padding: 0;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Chart initialization
function initializeCharts() {
    // This would initialize any Plotly charts if needed
    // Charts are primarily handled server-side with Plotly
}

// Blockchain verification
window.verifyBlockchain = async function() {
    try {
        const response = await fetch('/admin/blockchain/verify');
        const data = await response.json();
        
        const statusElement = document.getElementById('blockchain-status');
        if (statusElement) {
            statusElement.innerHTML = `
                <div class="blockchain-status ${data.integrity_verified ? 'blockchain-valid' : 'blockchain-invalid'}">
                    <h3>Blockchain Integrity: ${data.integrity_verified ? 'VALID' : 'COMPROMISED'}</h3>
                    <p>${data.message}</p>
                    ${data.blockchain_length ? `<p>Blockchain Length: ${data.blockchain_length} blocks</p>` : ''}
                </div>
            `;
        }
    } catch (error) {
        console.error('Blockchain verification failed:', error);
        showNotification('Blockchain verification failed', 'error');
    }
};

// AI predictions
window.loadSalesPredictions = async function(restaurantId) {
    try {
        const response = await fetch(`/ai/api/sales-predictions/${restaurantId}`);
        const data = await response.json();
        
        const predictionsContainer = document.getElementById('sales-predictions');
        if (predictionsContainer && data.predictions) {
            let html = '<h3>7-Day Sales Predictions</h3>';
            data.predictions.forEach(prediction => {
                html += `
                    <div class="prediction-item">
                        <span>${prediction.date} (${prediction.day_name})</span>
                        <span>$${prediction.predicted_sales.toFixed(2)}</span>
                    </div>
                `;
            });
            predictionsContainer.innerHTML = html;
        }
    } catch (error) {
        console.error('Failed to load predictions:', error);
    }
};

// Utility functions
window.formatCurrency = function(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
};

window.formatDate = function(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
};

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .cart-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        border-bottom: 1px solid #444;
    }
    
    .cart-item img {
        width: 60px;
        height: 60px;
        object-fit: cover;
        border-radius: 8px;
    }
    
    .quantity-controls {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .quantity-controls button {
        background: var(--primary-purple);
        color: white;
        border: none;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        cursor: pointer;
    }
    
    .remove-btn {
        background: none;
        border: none;
        color: #FF4757;
        cursor: pointer;
        font-size: 1.2rem;
    }
    
    .empty-cart {
        text-align: center;
        color: var(--text-gray);
        padding: 2rem;
    }
    
    .prediction-item {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #444;
    }
`;
document.head.appendChild(style);