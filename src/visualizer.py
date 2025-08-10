"""
Visualization and reporting module for Monte Carlo simulation results.
Creates charts and detailed reports for project management insights.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List
import os


class ResultsVisualizer:
    """Creates visualizations and reports from Monte Carlo simulation results."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def create_project_duration_chart(self, results: List[Dict], analysis: Dict):
        """Create histogram of project duration distribution."""
        total_days = [r['total_days'] for r in results]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Histogram
        ax1.hist(total_days, bins=50, alpha=0.7, edgecolor='black')
        ax1.axvline(analysis['project_summary']['mean_days'], 
                   color='red', linestyle='--', linewidth=2, label='Mean')
        ax1.axvline(np.percentile(total_days, 50), 
                   color='orange', linestyle='--', linewidth=2, label='Median')
        ax1.set_xlabel('Project Duration (Days)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Project Duration Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Box plot
        ax2.boxplot(total_days)
        ax2.set_ylabel('Project Duration (Days)')
        ax2.set_title('Duration Distribution Box Plot')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/project_duration_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_confidence_interval_chart(self, analysis: Dict):
        """Create confidence interval visualization."""
        confidence_data = analysis['confidence_intervals']
        
        confidence_levels = []
        lower_bounds = []
        upper_bounds = []
        means = []
        
        for level, bounds in confidence_data.items():
            confidence_levels.append(level)
            lower_bounds.append(bounds['days']['lower'])
            upper_bounds.append(bounds['days']['upper'])
            means.append(analysis['project_summary']['mean_days'])
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        y_pos = np.arange(len(confidence_levels))
        
        # Create horizontal error bars
        errors = [[m - l for m, l in zip(means, lower_bounds)],
                 [u - m for m, u in zip(means, upper_bounds)]]
        
        ax.errorbar(means, y_pos, xerr=errors, fmt='o', capsize=5, capthick=2)
        
        # Add confidence level labels
        for i, (level, lower, upper) in enumerate(zip(confidence_levels, lower_bounds, upper_bounds)):
            ax.text(upper + 5, i, f'{lower:.1f} - {upper:.1f} days', 
                   va='center', fontweight='bold')
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(confidence_levels)
        ax.set_xlabel('Project Duration (Days)')
        ax.set_ylabel('Confidence Level')
        ax.set_title('Project Duration Confidence Intervals')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/confidence_intervals.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_category_analysis_chart(self, analysis: Dict):
        """Create category breakdown and risk analysis charts."""
        category_data = analysis['category_analysis']
        
        categories = list(category_data.keys())
        mean_hours = [data['mean_hours'] for data in category_data.values()]
        contributions = [data['contribution_percent'] for data in category_data.values()]
        risks = [data['risk_variance'] for data in category_data.values()]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Category hours bar chart
        bars1 = ax1.bar(categories, mean_hours, alpha=0.7)
        ax1.set_xlabel('Category')
        ax1.set_ylabel('Mean Hours')
        ax1.set_title('Average Hours by Category')
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, hours in zip(bars1, mean_hours):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{hours:.1f}h', ha='center', va='bottom')
        
        # Contribution pie chart
        ax2.pie(contributions, labels=categories, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Project Time Contribution by Category')
        
        # Risk variance chart
        bars3 = ax3.bar(categories, risks, alpha=0.7, color='red')
        ax3.set_xlabel('Category')
        ax3.set_ylabel('Variance (Risk)')
        ax3.set_title('Risk Level by Category')
        ax3.tick_params(axis='x', rotation=45)
        
        # Risk vs Contribution scatter
        ax4.scatter(contributions, risks, s=100, alpha=0.7)
        for i, cat in enumerate(categories):
            ax4.annotate(cat, (contributions[i], risks[i]), 
                        xytext=(5, 5), textcoords='offset points')
        ax4.set_xlabel('Contribution to Project (%)')
        ax4.set_ylabel('Risk Variance')
        ax4.set_title('Risk vs Contribution Analysis')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/category_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_risk_analysis_chart(self, analysis: Dict):
        """Create risk probability visualization."""
        risk_data = analysis['risk_analysis']
        
        scenarios = ['Over Mean', 'Over 150%', 'Over 200%']
        probabilities = [
            risk_data['probability_over_mean'] * 100,
            risk_data['probability_over_150_percent'] * 100,
            risk_data['probability_over_200_percent'] * 100
        ]
        
        colors = ['yellow', 'orange', 'red']
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        bars = ax.bar(scenarios, probabilities, color=colors, alpha=0.7, edgecolor='black')
        
        # Add percentage labels on bars
        for bar, prob in zip(bars, probabilities):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   f'{prob:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        ax.set_ylabel('Probability (%)')
        ax.set_title('Project Overrun Risk Analysis')
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/risk_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_detailed_report(self, analysis: Dict, expert_estimates: pd.DataFrame):
        """Generate detailed text report with interpretation."""
        
        report = f"""
# Monte Carlo Simulation Report: Web Development Project

## Executive Summary

**Project Overview:**
- Total Tasks: {len(expert_estimates)}
- Simulation Runs: {10000:,}
- Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

## Project Duration Estimates

**Mean Estimates:**
- Duration: {analysis['project_summary']['mean_days']:.1f} days ({analysis['project_summary']['mean_hours']:.1f} hours)
- Standard Deviation: ±{analysis['project_summary']['std_days']:.1f} days

**Range:**
- Minimum: {analysis['project_summary']['min_hours'] / 8:.1f} days
- Maximum: {analysis['project_summary']['max_hours'] / 8:.1f} days

## Confidence Intervals

"""
        
        for level, bounds in analysis['confidence_intervals'].items():
            report += f"**{level} Confidence:**\n"
            report += f"- Range: {bounds['days']['lower']:.1f} - {bounds['days']['upper']:.1f} days\n"
            report += f"- Hours: {bounds['hours']['lower']:.1f} - {bounds['hours']['upper']:.1f} hours\n\n"
        
        report += """
## Category Breakdown

| Category | Mean Hours | Contribution | Risk Level |
|----------|------------|--------------|------------|
"""
        
        for category, data in analysis['category_analysis'].items():
            report += f"| {category.title()} | {data['mean_hours']:.1f}h | {data['contribution_percent']:.1f}% | {data['risk_variance']:.2f} |\n"
        
        report += f"""

## Risk Analysis

**Probability of Project Overruns:**
- Exceeding mean estimate: {analysis['risk_analysis']['probability_over_mean']*100:.1f}%
- Exceeding 150% of mean: {analysis['risk_analysis']['probability_over_150_percent']*100:.1f}%
- Exceeding 200% of mean: {analysis['risk_analysis']['probability_over_200_percent']*100:.1f}%

## Interpretation and Recommendations

### Key Insights:
1. **Most Likely Completion:** {analysis['project_summary']['mean_days']:.1f} days
2. **Planning Buffer:** Consider adding {analysis['project_summary']['std_days']:.1f} days buffer
3. **High-Risk Categories:** Categories with variance > 100 require extra attention
4. **Resource Allocation:** Focus on categories with highest contribution percentages

### Risk Mitigation Strategies:
- **High Variance Categories:** Increase monitoring and add contingency time
- **Critical Path:** Focus on categories contributing >20% to total time
- **Team Planning:** Use 75% confidence interval ({analysis['confidence_intervals']['75%']['days']['upper']:.1f} days) for realistic scheduling

### Project Management Recommendations:
1. Use {analysis['confidence_intervals']['75%']['days']['upper']:.1f} days as baseline schedule
2. Plan for {analysis['confidence_intervals']['90%']['days']['upper']:.1f} days in worst-case scenarios
3. Implement weekly progress tracking to identify early warning signs
4. Allocate extra resources to high-risk categories early in the project

---
*This report was generated using Monte Carlo simulation with {10000:,} iterations,
incorporating expert estimates and historical project data calibration.*
"""
        
        with open(f'{self.output_dir}/simulation_report.md', 'w') as f:
            f.write(report)
    
    def create_all_visualizations(self, results: List[Dict], analysis: Dict, expert_estimates: pd.DataFrame):
        """Generate all charts and reports."""
        print("Creating visualizations...")
        
        self.create_project_duration_chart(results, analysis)
        self.create_confidence_interval_chart(analysis)
        self.create_category_analysis_chart(analysis)
        self.create_risk_analysis_chart(analysis)
        self.generate_detailed_report(analysis, expert_estimates)
        
        print(f"Visualizations saved to {self.output_dir}/")
        print("Generated files:")
        print("- project_duration_distribution.png")
        print("- confidence_intervals.png") 
        print("- category_analysis.png")
        print("- risk_analysis.png")
        print("- simulation_report.md")