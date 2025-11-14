from flask import Flask, render_template
from config import Config

# Import your routes
from routes.auth_routes import auth_bp
from routes.customer_routes import customer_bp
from routes.restaurant_routes import restaurant_bp
from routes.admin_routes import admin_bp
from routes.order_routes import order_bp
from routes.gdpr_routes import gdpr_bp
from routes.ai_routes import ai_bp
from routes.security_routes import security_bp

# Import database utils
from utils.database import init_db

# Import AI for training on startup
from ai.villain_ai import VillainAI
from ai.data_collection import VillainDataset


def register_blueprints(app):
    """Helper to register all blueprints in one place."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(restaurant_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(gdpr_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(security_bp)


def create_app(config_class=Config):
    """Flask application factory used by Gunicorn and tests."""
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)
    flask_app.secret_key = config_class.SECRET_KEY  # Needed for sessions and flash

    # Initialize database (test connection)

    init_db()

    # Initialize and train AI model on startup
    try:
        print("Initializing AI model...")
        villain_ai = VillainAI()
        dataset = VillainDataset()
        
        # Try to collect real data, fallback to sample data
        sales_data, interactions, menu_data = dataset.collect_real_data()
        if sales_data is None or sales_data.empty:
            print("No real data found, generating sample data for training...")
            sales_data, interactions, menu_data = dataset.generate_sample_data()
        
        # Train model if not already trained
        if not villain_ai.is_trained and sales_data is not None and not sales_data.empty:
            print("Training AI model...")
            mae, rmse, feature_importance = villain_ai.train_sales_predictor(sales_data)
            if mae is not None:
                print(f"AI model trained successfully! MAE: {mae:.2f}, RMSE: {rmse:.2f}")
            else:
                print("AI model training failed, will retry on first use")
        elif villain_ai.is_trained:
            print("AI model already trained and loaded from disk")
    except Exception as e:
        print(f"Error initializing AI model: {e}")
        print("AI model will be trained on first use")

    # Register Blueprints
    register_blueprints(flask_app)

    # Home route
    @flask_app.route('/')
    def index():
        try:
            return render_template('index.html')
        except Exception as e:
            print(f"Error rendering index: {e}")
            return f"Error: {str(e)}", 500

    return flask_app


# Default app instance for local development
app = create_app()


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
