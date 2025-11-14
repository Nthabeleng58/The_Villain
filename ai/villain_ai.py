# ai/villain_ai.py

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, learning_curve
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder, StandardScaler
import plotly.express as px
from datetime import datetime, timedelta
import pickle
import os
from ai.model_evaluation import ModelEvaluator
from utils.database import get_db_connection
from config import Config

class VillainAI:
    """AI module for sales predictions and recommendations"""

    def __init__(self):
        self.sales_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_evaluator = ModelEvaluator()
        self.model_path = Config.AI_MODEL_PATH
        self._load_model()

    # ---------------------------
    # DATA PREPARATION
    # ---------------------------
    def prepare_sales_features(self, df):
        """Prepare features for sales prediction"""
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_holiday_season'] = df['month'].isin([11, 12]).astype(int)

        # Encode categorical variables
        le_cuisine = LabelEncoder()
        df['cuisine_encoded'] = le_cuisine.fit_transform(df['cuisine_type'])
        return df

    # ---------------------------
    # TRAINING
    # ---------------------------
    def train_sales_predictor(self, sales_data):
        """Train the sales prediction model"""
        try:
            df = self.prepare_sales_features(sales_data)
            feature_cols = [
                'restaurant_id', 'day_of_week', 'month', 'is_weekend',
                'is_holiday_season', 'cuisine_encoded'
            ]
            X = df[feature_cols]
            y = df['total_sales']

            valid_indices = X.notna().all(axis=1)
            X = X[valid_indices]
            y = y[valid_indices]

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            self.sales_model = RandomForestRegressor(
                n_estimators=100, max_depth=10, random_state=42
            )
            self.sales_model.fit(X_train_scaled, y_train)

            y_pred = self.sales_model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            feature_importance = dict(zip(feature_cols, self.sales_model.feature_importances_))

            self.is_trained = True
            
            # Save model to disk
            self._save_model()

            return mae, rmse, feature_importance

        except Exception as e:
            print(f"Error training model: {e}")
            return None, None, None
    
    def _save_model(self):
        """Save trained model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            model_data = {
                'model': self.sales_model,
                'scaler': self.scaler,
                'is_trained': self.is_trained
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            print(f"Model saved to {self.model_path}")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def _load_model(self):
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.sales_model = model_data['model']
                    self.scaler = model_data['scaler']
                    self.is_trained = model_data.get('is_trained', False)
                print(f"Model loaded from {self.model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.is_trained = False

    # ---------------------------
    # FUTURE SALES PREDICTION
    # ---------------------------
    def predict_future_sales(self, restaurant_id, days=7):
        """Predict sales for the next N days"""
        if not self.is_trained or self.sales_model is None:
            return []

        try:
            predictions = []
            today = datetime.now()

            # Get restaurant info
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM restaurants WHERE id = %s", (restaurant_id,))
                restaurant = cursor.fetchone()
                cursor.close()
                conn.close()
            else:
                restaurant = {'cuisine_type': 'Burger'}

            le_cuisine = LabelEncoder()
            le_cuisine.fit([restaurant['cuisine_type']])
            cuisine_encoded = le_cuisine.transform([restaurant['cuisine_type']])[0]

            for i in range(days):
                date = today + timedelta(days=i+1)
                features = pd.DataFrame([{
                    'restaurant_id': restaurant_id,
                    'day_of_week': date.weekday(),
                    'month': date.month,
                    'is_weekend': int(date.weekday() >= 5),
                    'is_holiday_season': int(date.month in [11, 12]),
                    'cuisine_encoded': cuisine_encoded
                }])
                scaled_features = self.scaler.transform(features)
                predicted_sales = self.sales_model.predict(scaled_features)[0]
                predictions.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'day_name': date.strftime('%A'),
                    'predicted_sales': max(0, round(predicted_sales, 2)),
                    'restaurant_id': restaurant_id
                })

            return predictions

        except Exception as e:
            print(f"Prediction error: {e}")
            return []

    # ---------------------------
    # POPULAR ITEM RECOMMENDATIONS
    # ---------------------------
    def get_popular_recommendations(self, user_id=None, top_n=5):
        """Return top N popular menu items"""
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT mi.name, mi.category, mi.price, COUNT(oi.id) as order_count
                    FROM menu_items mi
                    JOIN order_items oi ON mi.id = oi.menu_item_id
                    JOIN orders o ON oi.order_id = o.id
                    WHERE o.status='delivered'
                    GROUP BY mi.id
                    ORDER BY order_count DESC
                    LIMIT ?
                """, (top_n,))
                items = cursor.fetchall()
                cursor.close()
                conn.close()
                if items:
                    return items
            # Fallback to synthetic recommendations
            sample_items = []
            for idx in range(top_n):
                sample_items.append({
                    'name': f'Villain Special #{idx + 1}',
                    'category': np.random.choice(['Main', 'Combo', 'Dessert']),
                    'price': round(np.random.uniform(8, 22), 2),
                    'order_count': np.random.randint(10, 80)
                })
            return sample_items
        except Exception as e:
            print(f"Recommendation error: {e}")
            return []

    # ---------------------------
    # DASHBOARDS & REPORTS
    # ---------------------------
    def generate_ai_dashboard(self, sales_data):
        """Create Plotly charts for AI dashboard."""
        if sales_data is None or sales_data.empty:
            return px.line(), px.bar(), px.imshow([[0]])

        df = sales_data.copy()
        df['date'] = pd.to_datetime(df['date'])

        trend = (
            df.groupby('date')['total_sales']
            .sum()
            .reset_index()
        )
        trend_chart = px.line(
            trend,
            x='date',
            y='total_sales',
            title='Daily Revenue Trend',
            template='plotly_dark'
        )

        cuisine = (
            df.groupby('cuisine_type')['total_sales']
            .sum()
            .reset_index()
            .sort_values('total_sales', ascending=False)
        )
        cuisine_chart = px.bar(
            cuisine,
            x='cuisine_type',
            y='total_sales',
            title='Cuisine Performance',
            color='total_sales',
            template='plotly_dark'
        )

        heatmap_df = df.copy()
        heatmap_df['day_of_week_name'] = heatmap_df['date'].dt.day_name()
        heatmap = (
            heatmap_df
            .groupby(['day_of_week_name', 'month'])['total_sales']
            .sum()
            .reset_index()
            .pivot(index='day_of_week_name', columns='month', values='total_sales')
            .fillna(0)
        )
        dow_chart = px.imshow(
            heatmap.values,
            x=[f"Month {col}" for col in heatmap.columns],
            y=heatmap.index,
            title='Sales Heatmap: Day vs Month',
            color_continuous_scale='Viridis'
        )
        dow_chart.update_layout(template='plotly_dark')

        return trend_chart, cuisine_chart, dow_chart

    def analyze_model_accuracy(self, sales_data):
        """Return accuracy, error metrics, and saturation levels."""
        baseline = {
            'mae': None,
            'rmse': None,
            'accuracy': None,
            'samples_used': 0,
            'saturation_point': None,
            'train_sizes': [],
            'validation_rmse': []
        }

        if sales_data is None or sales_data.empty:
            return baseline

        df = self.prepare_sales_features(sales_data)
        feature_cols = [
            'restaurant_id', 'day_of_week', 'month', 'is_weekend',
            'is_holiday_season', 'cuisine_encoded'
        ]
        X = df[feature_cols]
        y = df['total_sales']

        if X.empty or y.empty:
            return baseline

        X_scaled = self.scaler.fit_transform(X)

        if not self.is_trained:
            self.train_sales_predictor(sales_data)

        if len(df) < 30:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_scaled, y)
            y_pred = model.predict(X_scaled)
            mae = mean_absolute_error(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))
            mean_sales = max(y.mean(), 1)
            accuracy = max(0.0, 1 - (rmse / mean_sales))
            self.model_evaluator.evaluate_sales_model(y, y_pred, model_name="Villain Sales RF (small)")
            return {
                'mae': float(mae),
                'rmse': float(rmse),
                'accuracy': float(accuracy),
                'samples_used': int(len(df)),
                'saturation_point': len(df),
                'train_sizes': [len(df)],
                'validation_rmse': [float(rmse)]
            }

        model = RandomForestRegressor(n_estimators=150, random_state=42, max_depth=12)
        train_sizes, train_scores, test_scores = learning_curve(
            model,
            X_scaled,
            y,
            cv=3,
            train_sizes=np.linspace(0.2, 1.0, 5),
            scoring='neg_mean_squared_error'
        )

        model.fit(X_scaled, y)
        y_pred = model.predict(X_scaled)
        mae = mean_absolute_error(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        mean_sales = max(y.mean(), 1)
        accuracy = max(0.0, 1 - (rmse / mean_sales))

        # Determine saturation point where improvement < 2%
        val_rmse = np.sqrt(-test_scores)
        accuracy_curve = 1 - (val_rmse / mean_sales)
        saturation_point = int(train_sizes[-1])
        for idx in range(1, len(accuracy_curve)):
            improvement = (accuracy_curve[idx] - accuracy_curve[idx-1]) * 100
            if improvement < 2.0:
                saturation_point = int(train_sizes[idx])
                break

        self.model_evaluator.evaluate_sales_model(y, y_pred, model_name="Villain Sales RF")

        return {
            'mae': float(mae),
            'rmse': float(rmse),
            'accuracy': float(accuracy),
            'samples_used': int(len(df)),
            'saturation_point': saturation_point,
            'train_sizes': train_sizes.tolist(),
            'validation_rmse': val_rmse.tolist()
        }

# ---------------------------
# HELPER FUNCTION FOR IMPORT
# ---------------------------
def get_ai_recommendations(user_id, top_n=3):
    ai = VillainAI()
    return ai.get_popular_recommendations(user_id, top_n)
