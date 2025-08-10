"""
Advanced Monte Carlo simulation engine with dynamic critical path analysis.
Implements the comprehensive framework from the specification document.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional
import yaml
import csv
from collections import defaultdict
from pathlib import Path
from task import Task, ProjectNetwork


class MonteCarloSimulator:
    """Advanced Monte Carlo simulator with critical path analysis."""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        self.simulation_runs = self.config['project']['simulation_runs']
        
        # Results storage
        self.results = {
            'durations': [],
            'critical_paths': [],
            'task_criticality': defaultdict(int),
            'task_durations': defaultdict(list),
            'task_statistics': []
        }
        
        self.network = None
        self.tasks = {}
    
    def load_project_data(self, filename: str):
        """Load task data from CSV file with dependencies."""
        tasks = {}
        
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                predecessors = row['Predecessors'].split(';') if row['Predecessors'] else []
                resources = row['Resources'].split(';') if row['Resources'] else []
                
                task = Task(
                    task_id=row['Task_ID'],
                    name=row['Task_Name'],
                    predecessors=predecessors,
                    optimistic=float(row['Optimistic']),
                    most_likely=float(row['Most_Likely']),
                    pessimistic=float(row['Pessimistic']),
                    category=row['Category'],
                    resources=resources
                )
                tasks[row['Task_ID']] = task
        
        self.tasks = tasks
        self.network = ProjectNetwork(tasks)
        return tasks
    
    def load_data(self, data_dir: str):
        """Load expert estimates and historical data (legacy method)."""
        try:
            self.expert_estimates = pd.read_csv(f"{data_dir}/expert_estimates.csv")
            self.historical_data = pd.read_csv(f"{data_dir}/historical_data.csv")
            
            with open(f"{data_dir}/category_statistics.yaml", 'r') as file:
                self.category_stats = yaml.safe_load(file)
        except FileNotFoundError:
            print("Legacy data files not found, using project_tasks.csv instead")
            self.load_project_data(f"{data_dir}/project_tasks.csv")
    
    def pert_distribution(self, optimistic: float, most_likely: float, 
                         pessimistic: float) -> float:
        """
        Generate random sample from PERT (Program Evaluation and Review Technique) distribution.
        PERT uses Beta distribution with parameters derived from three-point estimates.
        """
        # PERT formula: Expected = (O + 4*ML + P) / 6
        # Beta parameters: alpha = 6 * (Expected - O) / (P - O), beta = 6 * (P - Expected) / (P - O)
        
        if pessimistic <= optimistic:
            return most_likely
        
        expected = (optimistic + 4 * most_likely + pessimistic) / 6
        
        # Calculate Beta distribution parameters
        range_val = pessimistic - optimistic
        if range_val == 0:
            return most_likely
        
        alpha = 6 * (expected - optimistic) / range_val
        beta = 6 * (pessimistic - expected) / range_val
        
        # Ensure parameters are positive
        alpha = max(alpha, 0.1)
        beta = max(beta, 0.1)
        
        # Generate Beta sample and scale to range
        beta_sample = np.random.beta(alpha, beta)
        return optimistic + beta_sample * range_val
    
    def apply_historical_calibration(self, task_duration: float, category: str) -> float:
        """Apply historical variance patterns to adjust task duration."""
        if category not in self.category_stats:
            return task_duration
        
        stats = self.category_stats[category]
        
        # Apply variance based on historical patterns
        variance_multiplier = np.random.normal(
            stats['mean_variance'], 
            stats['std_variance']
        )
        
        # Ensure reasonable bounds
        variance_multiplier = np.clip(variance_multiplier, 0.5, 3.0)
        
        return task_duration * variance_multiplier
    
    def run_single_iteration(self) -> Dict:
        """Run one complete simulation iteration with critical path analysis."""
        if not self.network:
            raise ValueError("Network not loaded. Call load_project_data first.")
        
        # Generate random durations for all tasks
        self.network.generate_all_durations()
        
        # Calculate network with these durations
        network_result = self.network.calculate_network()
        
        # Get task statistics
        task_stats = self.network.get_task_statistics()
        
        # Store results
        self.results['durations'].append(network_result['project_duration'])
        self.results['critical_paths'].append(network_result['critical_path'])
        
        # Track criticality frequency
        for task_id in network_result['critical_path']:
            self.results['task_criticality'][task_id] += 1
        
        # Track individual task durations
        for task_id, task in self.tasks.items():
            self.results['task_durations'][task_id].append(task.duration)
        
        return {
            'project_duration': network_result['project_duration'],
            'critical_path': network_result['critical_path'],
            'task_statistics': task_stats
        }
    
    def simulate_single_run(self) -> Dict:
        """Execute a single Monte Carlo simulation run (legacy method)."""
        if hasattr(self, 'expert_estimates'):
            task_durations = []
            category_totals = {}
            
            for _, task in self.expert_estimates.iterrows():
                # Generate duration using PERT distribution
                duration = self.pert_distribution(
                    task['optimistic_hours'],
                    task['most_likely_hours'],
                    task['pessimistic_hours']
                )
                
                # Apply historical calibration
                calibrated_duration = self.apply_historical_calibration(
                    duration, task['category']
                )
                
                task_durations.append({
                    'task_id': task['task_id'],
                    'category': task['category'],
                    'estimated_duration': duration,
                    'calibrated_duration': calibrated_duration
                })
                
                # Track category totals
                if task['category'] not in category_totals:
                    category_totals[task['category']] = 0
                category_totals[task['category']] += calibrated_duration
            
            total_duration = sum([t['calibrated_duration'] for t in task_durations])
            
            return {
                'total_hours': total_duration,
                'total_days': total_duration / 8,  # 8-hour workdays
                'category_totals': category_totals,
                'task_details': task_durations
            }
        else:
            # Use new method
            return self.run_single_iteration()
    
    def run_simulation(self) -> Dict:
        """Run complete Monte Carlo simulation with critical path analysis."""
        if not self.network:
            raise ValueError("Network not loaded. Call load_project_data first.")
        
        print(f"Running {self.simulation_runs:,} Monte Carlo simulations...")
        
        for i in range(self.simulation_runs):
            if (i + 1) % 1000 == 0:
                print(f"Progress: {i + 1:,}/{self.simulation_runs:,}")
            
            self.run_single_iteration()
        
        # Calculate criticality percentages
        for task_id in self.results['task_criticality']:
            self.results['task_criticality'][task_id] = \
                (self.results['task_criticality'][task_id] / self.simulation_runs) * 100
        
        print("Simulation complete!")
        return self.analyze_advanced_results()
    
    def analyze_advanced_results(self) -> Dict:
        """Analyze simulation results with advanced statistics."""
        durations = np.array(self.results['durations'])
        confidence_levels = self.config['project']['confidence_levels']
        
        # Calculate percentiles
        percentiles = {
            'P10': np.percentile(durations, 10),
            'P25': np.percentile(durations, 25),
            'P50': np.percentile(durations, 50),
            'P75': np.percentile(durations, 75),
            'P80': np.percentile(durations, 80),
            'P90': np.percentile(durations, 90),
            'P95': np.percentile(durations, 95),
            'Mean': np.mean(durations),
            'StdDev': np.std(durations)
        }
        
        # Identify critical tasks
        critical_tasks = self.identify_critical_tasks(threshold=50)
        
        # Calculate sensitivity index
        sensitivity = self.calculate_sensitivity_index()
        
        # Generate confidence intervals
        confidence_intervals = {}
        for confidence in confidence_levels:
            alpha = 1 - confidence
            lower = np.percentile(durations, alpha/2 * 100)
            upper = np.percentile(durations, (1 - alpha/2) * 100)
            
            confidence_intervals[f'{confidence:.0%}'] = {
                'lower_bound': lower,
                'upper_bound': upper,
                'range': upper - lower
            }
        
        # Risk analysis
        mean_duration = np.mean(durations)
        risk_analysis = {
            'probability_over_mean': np.mean(durations > mean_duration),
            'probability_over_150_percent': np.mean(durations > mean_duration * 1.5),
            'probability_over_200_percent': np.mean(durations > mean_duration * 2.0),
            'value_at_risk_95': np.percentile(durations, 95),
            'expected_shortfall_95': np.mean(durations[durations >= np.percentile(durations, 95)])
        }
        
        # Category analysis
        category_analysis = self.analyze_categories()
        
        return {
            'project_summary': {
                'total_tasks': len(self.tasks),
                'simulation_runs': self.simulation_runs,
                'mean_duration': mean_duration,
                'std_duration': np.std(durations),
                'min_duration': np.min(durations),
                'max_duration': np.max(durations)
            },
            'percentiles': percentiles,
            'confidence_intervals': confidence_intervals,
            'critical_tasks': critical_tasks,
            'sensitivity_analysis': sensitivity,
            'risk_analysis': risk_analysis,
            'category_analysis': category_analysis,
            'buffer_recommendations': self.calculate_buffer_recommendations(percentiles)
        }
    
    def identify_critical_tasks(self, threshold: float = 50) -> List[Dict]:
        """Identify tasks that are critical >threshold% of the time."""
        critical_tasks = []
        for task_id, criticality in self.results['task_criticality'].items():
            if criticality > threshold:
                task = self.tasks[task_id]
                critical_tasks.append({
                    'task_id': task_id,
                    'task_name': task.name,
                    'category': task.category,
                    'criticality_percentage': criticality,
                    'mean_duration': task.mean,
                    'std_duration': task.std_dev
                })
        
        return sorted(critical_tasks, 
                     key=lambda x: x['criticality_percentage'], 
                     reverse=True)
    
    def calculate_sensitivity_index(self) -> List[Dict]:
        """Calculate sensitivity index for each task."""
        durations = np.array(self.results['durations'])
        sensitivity = []
        
        for task_id, task_durations in self.results['task_durations'].items():
            task_durations = np.array(task_durations)
            
            # Correlation between task duration and project duration
            correlation = np.corrcoef(task_durations, durations)[0, 1]
            
            # Variance contribution
            task_variance = np.var(task_durations)
            
            # Impact score
            impact_score = abs(correlation) * task_variance
            
            task = self.tasks[task_id]
            sensitivity.append({
                'task_id': task_id,
                'task_name': task.name,
                'category': task.category,
                'correlation': correlation,
                'variance': task_variance,
                'impact_score': impact_score,
                'criticality_percentage': self.results['task_criticality'].get(task_id, 0)
            })
        
        return sorted(sensitivity, key=lambda x: x['impact_score'], reverse=True)
    
    def analyze_categories(self) -> Dict:
        """Analyze results by task category."""
        category_durations = defaultdict(list)
        category_criticality = defaultdict(list)
        
        # Collect data by category
        for task_id, task in self.tasks.items():
            task_durations = self.results['task_durations'][task_id]
            category_durations[task.category].extend(task_durations)
            
            criticality = self.results['task_criticality'].get(task_id, 0)
            category_criticality[task.category].append(criticality)
        
        analysis = {}
        for category in category_durations:
            durations = np.array(category_durations[category])
            criticalities = np.array(category_criticality[category])
            
            analysis[category] = {
                'total_duration_mean': np.mean(durations),
                'total_duration_std': np.std(durations),
                'avg_criticality': np.mean(criticalities),
                'max_criticality': np.max(criticalities),
                'task_count': len([t for t in self.tasks.values() if t.category == category]),
                'risk_contribution': np.var(durations)
            }
        
        return analysis
    
    def calculate_buffer_recommendations(self, percentiles: Dict) -> Dict:
        """Calculate recommended buffers based on risk tolerance."""
        mean_duration = percentiles['Mean']
        
        return {
            'aggressive': {
                'target': percentiles['P50'],
                'buffer': 0,
                'success_probability': 50,
                'description': 'No buffer - 50% chance of success'
            },
            'moderate': {
                'target': percentiles['P75'],
                'buffer': percentiles['P75'] - mean_duration,
                'success_probability': 75,
                'description': 'Moderate buffer - 75% chance of success'
            },
            'conservative': {
                'target': percentiles['P90'],
                'buffer': percentiles['P90'] - mean_duration,
                'success_probability': 90,
                'description': 'Conservative buffer - 90% chance of success'
            },
            'very_conservative': {
                'target': percentiles['P95'],
                'buffer': percentiles['P95'] - mean_duration,
                'success_probability': 95,
                'description': 'Very conservative - 95% chance of success'
            }
        }
    
    def export_results_to_csv(self, output_dir: str, analysis: Dict):
        """Export simulation results to CSV files for easy analysis."""
        import os
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 1. Export distribution data
        self._export_distribution_data(output_path, analysis)
        
        # 2. Export percentiles and buffers
        self._export_percentiles_and_buffers(output_path, analysis)
        
        # 3. Export task criticality
        self._export_task_criticality(output_path, analysis)
        
        # 4. Export sensitivity analysis
        self._export_sensitivity_analysis(output_path, analysis)
        
        # 5. Export category analysis
        self._export_category_analysis(output_path, analysis)
        
        # 6. Export scenario planning
        self._export_scenario_planning(output_path, analysis)
    
    def _export_distribution_data(self, output_path: Path, analysis: Dict):
        """Export project duration distribution data."""
        durations = np.array(self.results['durations'])
        
        # Create frequency distribution
        hist, bin_edges = np.histogram(durations, bins=50)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Calculate cumulative probability
        sorted_durations = np.sort(durations)
        cumulative_prob = np.arange(1, len(sorted_durations) + 1) / len(sorted_durations)
        
        # Export detailed distribution
        with open(output_path / 'project_duration_distribution.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Duration_Days', 'Frequency', 'Cumulative_Probability'])
            
            for duration, prob in zip(sorted_durations, cumulative_prob):
                writer.writerow([f"{duration:.1f}", 1, f"{prob:.4f}"])
    
    def _export_percentiles_and_buffers(self, output_path: Path, analysis: Dict):
        """Export percentiles and buffer analysis."""
        percentiles = analysis['percentiles']
        baseline = percentiles['P50']
        
        with open(output_path / 'percentiles_and_buffers.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Percentile', 'Days', 'Buffer_Days', 'Buffer_Percentage', 'Use_Case'])
            
            percentile_data = [
                ('P10', percentiles['P10'], 0, 0, 'Optimistic scenario'),
                ('P25', percentiles['P25'], 0, 0, 'Aggressive planning'),
                ('P50', percentiles['P50'], 0, 0, 'Baseline estimate'),
                ('P75', percentiles['P75'], percentiles['P75'] - baseline, 
                 ((percentiles['P75'] - baseline) / baseline) * 100, 'Internal planning'),
                ('P80', percentiles['P80'], percentiles['P80'] - baseline,
                 ((percentiles['P80'] - baseline) / baseline) * 100, 'Moderate buffer'),
                ('P90', percentiles['P90'], percentiles['P90'] - baseline,
                 ((percentiles['P90'] - baseline) / baseline) * 100, 'External commitments'),
                ('P95', percentiles['P95'], percentiles['P95'] - baseline,
                 ((percentiles['P95'] - baseline) / baseline) * 100, 'Conservative buffer')
            ]
            
            for percentile, days, buffer_days, buffer_pct, use_case in percentile_data:
                writer.writerow([percentile, f"{days:.1f}", f"{buffer_days:.1f}", 
                               f"{buffer_pct:.1f}%", use_case])
    
    def _export_task_criticality(self, output_path: Path, analysis: Dict):
        """Export task criticality analysis."""
        with open(output_path / 'task_criticality.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Task_ID', 'Task_Name', 'Category', 'Criticality_Percentage', 
                           'Priority_Level', 'Resource_Allocation'])
            
            # Sort all tasks by criticality
            all_tasks = []
            for task_id, task in self.tasks.items():
                criticality = self.results['task_criticality'].get(task_id, 0)
                
                if criticality > 80:
                    priority = 'Critical'
                    allocation = 'Best resources'
                elif criticality > 50:
                    priority = 'High'
                    allocation = 'Monitor closely'
                elif criticality > 20:
                    priority = 'Medium'
                    allocation = 'Monitor closely'
                else:
                    priority = 'Low'
                    allocation = 'Standard'
                
                all_tasks.append([task_id, task.name, task.category, 
                                f"{criticality:.1f}%", priority, allocation])
            
            # Sort by criticality descending
            all_tasks.sort(key=lambda x: float(x[3].rstrip('%')), reverse=True)
            
            for task_data in all_tasks:
                writer.writerow(task_data)
    
    def _export_sensitivity_analysis(self, output_path: Path, analysis: Dict):
        """Export sensitivity analysis (risk drivers)."""
        with open(output_path / 'sensitivity_analysis.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Task_ID', 'Task_Name', 'Category', 'Impact_Score', 
                           'Correlation', 'Variance', 'Risk_Level'])
            
            for task in analysis['sensitivity_analysis']:
                if task['impact_score'] > 1.0:
                    risk_level = 'High'
                elif task['impact_score'] > 0.3:
                    risk_level = 'Medium'
                else:
                    risk_level = 'Low'
                
                writer.writerow([
                    task['task_id'], task['task_name'], task['category'],
                    f"{task['impact_score']:.3f}", f"{task['correlation']:.3f}",
                    f"{task['variance']:.2f}", risk_level
                ])
    
    def _export_category_analysis(self, output_path: Path, analysis: Dict):
        """Export category risk analysis."""
        with open(output_path / 'category_analysis.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Category', 'Task_Count', 'Mean_Duration', 'Std_Duration', 
                           'Risk_Contribution', 'Avg_Criticality'])
            
            for category, data in analysis['category_analysis'].items():
                writer.writerow([
                    category, data['task_count'], f"{data['total_duration_mean']:.1f}",
                    f"{data['total_duration_std']:.1f}", f"{data['risk_contribution']:.1f}",
                    f"{data['avg_criticality']:.1f}%"
                ])
    
    def _export_scenario_planning(self, output_path: Path, analysis: Dict):
        """Export scenario planning data."""
        with open(output_path / 'scenario_planning.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Scenario', 'Target_Days', 'Success_Probability', 
                           'Buffer_Days', 'Recommended_For'])
            
            buffers = analysis['buffer_recommendations']
            baseline = analysis['percentiles']['P50']
            
            scenarios = [
                ('Aggressive', buffers['aggressive']['target'], '50%', 
                 f"{buffers['aggressive']['buffer']:.1f}", 'Internal stretch goals'),
                ('Moderate', buffers['moderate']['target'], '75%',
                 f"{buffers['moderate']['buffer']:.1f}", 'Team planning'),
                ('Conservative', buffers['conservative']['target'], '90%',
                 f"{buffers['conservative']['buffer']:.1f}", 'Client commitments'),
                ('Very_Conservative', buffers['very_conservative']['target'], '95%',
                 f"{buffers['very_conservative']['buffer']:.1f}", 'High-risk projects')
            ]
            
            for scenario, target, prob, buffer, recommended in scenarios:
                writer.writerow([scenario, f"{target:.1f}", prob, buffer, recommended])
