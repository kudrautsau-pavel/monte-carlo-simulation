"""
Data generator for Monte Carlo simulation.
Generates expert estimates and historical data for web development tasks.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import yaml


class DataGenerator:
    """Generates expert estimates and historical data for project tasks."""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
    
    def generate_expert_estimates(self) -> pd.DataFrame:
        """Generate expert estimates for all project tasks."""
        tasks = []
        task_id = 1
        
        for category, details in self.config['task_categories'].items():
            for i in range(details['count']):
                # Base effort in hours (expert estimate)
                base_effort = np.random.uniform(4, 40)  # 4-40 hours per task
                
                # Apply complexity weight
                complexity_factor = details['complexity_weight']
                optimistic = base_effort * 0.7  # Best case
                most_likely = base_effort * complexity_factor  # Most likely
                pessimistic = base_effort * complexity_factor * 1.8  # Worst case
                
                tasks.append({
                    'task_id': task_id,
                    'category': category,
                    'task_name': f"{category.title()}_Task_{i+1}",
                    'optimistic_hours': round(optimistic, 1),
                    'most_likely_hours': round(most_likely, 1),
                    'pessimistic_hours': round(pessimistic, 1),
                    'complexity_weight': complexity_factor
                })
                task_id += 1
        
        return pd.DataFrame(tasks)
    
    def generate_historical_data(self) -> pd.DataFrame:
        """Generate historical project data for calibration."""
        historical_projects = []
        project_count = self.config['historical_data']['project_count']
        variance_factor = self.config['historical_data']['variance_factor']
        optimism_bias = self.config['historical_data']['optimism_bias']
        
        for i in range(project_count):
            # Simulate historical project outcomes
            for category, details in self.config['task_categories'].items():
                task_count = details['count']
                
                for j in range(task_count):
                    # Generate actual completion time vs estimate
                    estimated = np.random.uniform(8, 35)
                    
                    # Apply optimism bias and variance
                    actual = estimated * optimism_bias * np.random.normal(1.0, variance_factor)
                    actual = max(actual, estimated * 0.5)  # Minimum 50% of estimate
                    
                    historical_projects.append({
                        'project_id': i + 1,
                        'category': category,
                        'estimated_hours': round(estimated, 1),
                        'actual_hours': round(actual, 1),
                        'variance_ratio': round(actual / estimated, 2)
                    })
        
        return pd.DataFrame(historical_projects)
    
    def calculate_category_statistics(self, historical_data: pd.DataFrame) -> Dict:
        """Calculate statistical parameters for each category from historical data."""
        stats = {}
        
        for category in historical_data['category'].unique():
            category_data = historical_data[historical_data['category'] == category]
            variance_ratios = category_data['variance_ratio']
            
            stats[category] = {
                'mean_variance': variance_ratios.mean(),
                'std_variance': variance_ratios.std(),
                'completion_rate': len(category_data) / len(category_data),  # Simplified
                'typical_multiplier': variance_ratios.median()
            }
        
        return stats
    
    def save_generated_data(self, expert_estimates: pd.DataFrame, 
                           historical_data: pd.DataFrame, 
                           category_stats: Dict, output_dir: str):
        """Save generated data to CSV files."""
        expert_estimates.to_csv(f"{output_dir}/expert_estimates.csv", index=False)
        historical_data.to_csv(f"{output_dir}/historical_data.csv", index=False)
        
        # Convert numpy types to native Python types for YAML serialization
        yaml_safe_stats = {}
        for category, stats in category_stats.items():
            yaml_safe_stats[category] = {
                'mean_variance': float(stats['mean_variance']),
                'std_variance': float(stats['std_variance']),
                'completion_rate': float(stats['completion_rate']),
                'typical_multiplier': float(stats['typical_multiplier'])
            }
        
        # Save category statistics as YAML
        with open(f"{output_dir}/category_statistics.yaml", 'w') as file:
            yaml.dump(yaml_safe_stats, file, default_flow_style=False)
        
        print(f"Generated data saved to {output_dir}/")
        print(f"Expert estimates: {len(expert_estimates)} tasks")
        print(f"Historical data: {len(historical_data)} records")