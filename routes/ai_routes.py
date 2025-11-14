from flask import Blueprint, render_template, jsonify
from ai.villain_ai import VillainAI
from ai.data_collection import VillainDataset
from utils.security import admin_required, restaurant_owner_required
from utils.database import get_db_connection

ai_bp = Blueprint('ai', __name__)
villain_ai = VillainAI()
dataset = VillainDataset()

@ai_bp.route('/analytics')
@admin_required
def analytics_dashboard():
    """Main AI analytics dashboard for admins"""
    sales_data, interactions, menu_data = dataset.collect_real_data()
    if sales_data is None:
        sales_data, interactions, menu_data = dataset.generate_sample_data()
    
    # Train model if not trained
    if not villain_ai.is_trained and sales_data is not None:
        villain_ai.train_sales_predictor(sales_data)
    
    # Generate charts
    trend_chart, cuisine_chart, dow_chart = villain_ai.generate_ai_dashboard(sales_data)
    
    # Get popular recommendations
    popular_items = villain_ai.get_popular_recommendations(top_n=10)
    
    # Model accuracy analysis
    accuracy_analysis = villain_ai.analyze_model_accuracy(sales_data)
    
    return render_template('admin/ai_dashboard.html',
                         trend_chart=trend_chart.to_html(full_html=False, include_plotlyjs='cdn'),
                         cuisine_chart=cuisine_chart.to_html(full_html=False, include_plotlyjs=False),
                         dow_chart=dow_chart.to_html(full_html=False, include_plotlyjs=False),
                         popular_items=popular_items,
                         accuracy_analysis=accuracy_analysis)

@ai_bp.route('/restaurant/<int:restaurant_id>/predictions')
@restaurant_owner_required
def restaurant_predictions(restaurant_id):
    """Sales predictions for specific restaurant"""
    if not villain_ai.is_trained:
        fallback_sales, _, _ = dataset.generate_sample_data()
        villain_ai.train_sales_predictor(fallback_sales)

    predictions = villain_ai.predict_future_sales(restaurant_id, days=7)
    popular_items = villain_ai.get_popular_recommendations(top_n=5)

    weekly_total = round(sum(item['predicted_sales'] for item in predictions), 2) if predictions else 0
    daily_avg = round(weekly_total / len(predictions), 2) if predictions else 0

    restaurant = None
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, cuisine_type FROM restaurants WHERE id = %s", (restaurant_id,))
        restaurant = cursor.fetchone()
        cursor.close()
        conn.close()

    return render_template('restaurant/predictions.html',
                         predictions=predictions,
                         popular_items=popular_items,
                         weekly_total=weekly_total,
                         daily_avg=daily_avg,
                         restaurant=restaurant,
                         restaurant_id=restaurant_id)

@ai_bp.route('/api/sales-predictions/<int:restaurant_id>')
def api_sales_predictions(restaurant_id):
    """API endpoint for sales predictions"""
    if not villain_ai.is_trained:
        fallback_sales, _, _ = dataset.generate_sample_data()
        villain_ai.train_sales_predictor(fallback_sales)

    predictions = villain_ai.predict_future_sales(restaurant_id, days=7)
    return jsonify({'predictions': predictions})

@ai_bp.route('/api/model-metrics')
@admin_required
def api_model_metrics():
    """API endpoint for model accuracy and saturation"""
    sales_data, interactions, menu_data = dataset.collect_real_data()
    if sales_data is None:
        sales_data, interactions, menu_data = dataset.generate_sample_data()
    
    accuracy_analysis = villain_ai.analyze_model_accuracy(sales_data)
    
    return jsonify(accuracy_analysis)