import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

class ModelEvaluator:
    def __init__(self):
        self.results = {}
    
    def evaluate_sales_model(self, y_true, y_pred, model_name="Sales Prediction"):
        """Evaluate sales prediction model"""
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        
        # Calculate accuracy percentage (1 - normalized RMSE)
        mean_sales = np.mean(y_true)
        accuracy_percentage = max(0, (1 - (rmse / mean_sales)) * 100)
        
        results = {
            'model': model_name,
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'accuracy_percentage': accuracy_percentage,
            'mean_actual': mean_sales,
            'mean_predicted': np.mean(y_pred)
        }
        
        self.results[model_name] = results
        return results
    
    def plot_learning_curve(self, train_sizes, train_scores, test_scores, model_name):
        """Plot learning curve to show model saturation"""
        plt.figure(figsize=(10, 6))
        
        train_scores_mean = np.mean(train_scores, axis=1)
        train_scores_std = np.std(train_scores, axis=1)
        test_scores_mean = np.mean(test_scores, axis=1)
        test_scores_std = np.std(test_scores, axis=1)
        
        plt.grid()
        plt.fill_between(train_sizes, train_scores_mean - train_scores_std,
                         train_scores_mean + train_scores_std, alpha=0.1, color="r")
        plt.fill_between(train_sizes, test_scores_mean - test_scores_std,
                         test_scores_mean + test_scores_std, alpha=0.1, color="g")
        plt.plot(train_sizes, train_scores_mean, 'o-', color="r", label="Training score")
        plt.plot(train_sizes, test_scores_mean, 'o-', color="g", label="Cross-validation score")
        
        plt.xlabel("Training examples")
        plt.ylabel("Score")
        plt.legend(loc="best")
        plt.title(f"Learning Curve - {model_name}")
        
        return plt
    
    def generate_report(self):
        """Generate comprehensive evaluation report"""
        if not self.results:
            return "No evaluation results available."
        
        report = "=== MODEL EVALUATION REPORT ===\n\n"
        
        for model_name, results in self.results.items():
            report += f"Model: {results['model']}\n"
            report += f"Mean Absolute Error: ${results['mae']:.2f}\n"
            report += f"Root Mean Square Error: ${results['rmse']:.2f}\n"
            report += f"Accuracy: {results['accuracy_percentage']:.1f}%\n"
            report += f"Mean Actual Sales: ${results['mean_actual']:.2f}\n"
            report += f"Mean Predicted Sales: ${results['mean_predicted']:.2f}\n"
            report += "-" * 50 + "\n"
        
        return report
    
    def find_saturation_point(self, data_sizes, accuracies, threshold=2.0):
        """Find the data size where model performance saturates"""
        if len(accuracies) < 2:
            return data_sizes[-1] if data_sizes else 0
        
        for i in range(1, len(accuracies)):
            improvement = accuracies[i] - accuracies[i-1]
            if improvement < threshold:
                return data_sizes[i-1]
        
        return data_sizes[-1]