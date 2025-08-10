#!/usr/bin/env python3
"""
Advanced Monte Carlo Simulation for Web Development Project Management
Main execution script implementing the comprehensive framework from the specification.
"""

import os
import sys
import json
import datetime
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.append(str(src_path))

from monte_carlo import MonteCarloSimulator
from visualizer import ResultsVisualizer


def main():
    """Main execution function for advanced Monte Carlo simulation."""
    print("=" * 80)
    print("ADVANCED MONTE CARLO SIMULATION")
    print("Web Development Project with Dynamic Critical Path Analysis")
    print("=" * 80)
    
    # Define paths
    project_dir = Path(__file__).parent
    config_path = project_dir / 'config' / 'project_config.yaml'
    data_dir = project_dir / 'data'
    output_dir = project_dir / 'output'
    
    # Create directories
    data_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Step 1: Load Project Data
    print("\n1. Loading Project Data with Dependencies...")
    simulator = MonteCarloSimulator(str(config_path))
    
    # Load project tasks with dependencies
    project_tasks_file = data_dir / 'project_tasks.csv'
    if not project_tasks_file.exists():
        print(f"Error: {project_tasks_file} not found!")
        print("Please ensure the project tasks file exists with task dependencies.")
        return
    
    tasks = simulator.load_project_data(str(project_tasks_file))
    print(f"   Loaded {len(tasks)} tasks with dependencies")
    print(f"   Network validated successfully")
    
    # Step 2: Run Advanced Monte Carlo Simulation
    print("\n2. Running Advanced Monte Carlo Simulation...")
    print("   Features: Dynamic Critical Path, Sensitivity Analysis, Risk Assessment")
    
    analysis = simulator.run_simulation()
    
    # Step 3: Generate Advanced Visualizations
    print("\n3. Generating Advanced Visualizations and Reports...")
    try:
        visualizer = ResultsVisualizer(str(output_dir))
        
        # Generate sample results for visualization
        print("   Creating visualization data...")
        sample_results = []
        for i in range(min(1000, len(simulator.results['durations']))):
            sample_results.append({
                'project_duration': simulator.results['durations'][i],
                'critical_path': simulator.results['critical_paths'][i]
            })
        
        # Create visualizations with new analysis data
        visualizer.create_advanced_visualizations(sample_results, analysis, simulator.results)
        
    except Exception as e:
        print(f"   Warning: Visualization generation failed: {e}")
        print("   Continuing with analysis results...")
    
    # Step 4: Generate Comprehensive Report
    print("\n4. Generating Comprehensive Analysis Report...")
    
    report = {
        'simulation_metadata': {
            'date': datetime.datetime.now().isoformat(),
            'iterations': analysis['project_summary']['simulation_runs'],
            'total_tasks': analysis['project_summary']['total_tasks'],
            'framework_version': '2.0 - Advanced Critical Path Analysis'
        },
        'project_summary': analysis['project_summary'],
        'percentiles': analysis['percentiles'],
        'confidence_intervals': analysis['confidence_intervals'],
        'critical_tasks': analysis['critical_tasks'][:10],  # Top 10
        'sensitivity_analysis': analysis['sensitivity_analysis'][:10],  # Top 10
        'risk_analysis': analysis['risk_analysis'],
        'category_analysis': analysis['category_analysis'],
        'buffer_recommendations': analysis['buffer_recommendations']
    }
    
    # Save detailed report
    report_file = output_dir / 'advanced_simulation_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Step 5: Display Executive Summary
    print("\n" + "=" * 80)
    print("EXECUTIVE SUMMARY - ADVANCED MONTE CARLO ANALYSIS")
    print("=" * 80)
    
    print(f"\n📊 PROJECT DURATION ANALYSIS:")
    print(f"   Mean Duration: {analysis['percentiles']['Mean']:.1f} days")
    print(f"   Standard Deviation: ±{analysis['percentiles']['StdDev']:.1f} days")
    print(f"   Range: {analysis['project_summary']['min_duration']:.1f} - {analysis['project_summary']['max_duration']:.1f} days")
    
    print(f"\n📈 KEY PERCENTILES:")
    for p in ['P50', 'P75', 'P80', 'P90', 'P95']:
        print(f"   {p}: {analysis['percentiles'][p]:.1f} days")
    
    print(f"\n🎯 CONFIDENCE INTERVALS:")
    for level, bounds in analysis['confidence_intervals'].items():
        print(f"   {level}: {bounds['lower_bound']:.1f} - {bounds['upper_bound']:.1f} days (range: {bounds['range']:.1f})")
    
    print(f"\n⚠️  RISK ANALYSIS:")
    print(f"   Probability of exceeding mean: {analysis['risk_analysis']['probability_over_mean']*100:.1f}%")
    print(f"   Probability of exceeding 150%: {analysis['risk_analysis']['probability_over_150_percent']*100:.1f}%")
    print(f"   Value at Risk (95%): {analysis['risk_analysis']['value_at_risk_95']:.1f} days")
    
    print(f"\n🔥 TOP CRITICAL TASKS (>50% criticality):")
    critical_tasks = analysis['critical_tasks']
    if critical_tasks:
        for i, task in enumerate(critical_tasks[:5], 1):
            print(f"   {i}. {task['task_name']} ({task['category']}) - {task['criticality_percentage']:.1f}% critical")
    else:
        print("   No tasks are critical >50% of the time")
    
    print(f"\n📊 SENSITIVITY ANALYSIS (Top Risk Drivers):")
    sensitivity = analysis['sensitivity_analysis']
    for i, task in enumerate(sensitivity[:5], 1):
        print(f"   {i}. {task['task_name']} - Impact Score: {task['impact_score']:.3f}")
    
    print(f"\n💰 BUFFER RECOMMENDATIONS:")
    buffers = analysis['buffer_recommendations']
    print(f"   Conservative (90%): {buffers['conservative']['target']:.1f} days (+{buffers['conservative']['buffer']:.1f} buffer)")
    print(f"   Moderate (75%): {buffers['moderate']['target']:.1f} days (+{buffers['moderate']['buffer']:.1f} buffer)")
    print(f"   Aggressive (50%): {buffers['aggressive']['target']:.1f} days (no buffer)")
    
    print(f"\n📁 OUTPUT FILES:")
    print(f"   Project Data: {data_dir}/project_tasks.csv")
    print(f"   Detailed Report: {output_dir}/advanced_simulation_report.json")
    print(f"   Visualizations: {output_dir}/")
    
    print(f"\n🎯 RECOMMENDED ACTION:")
    recommended = buffers['conservative']
    print(f"   Plan for {recommended['target']:.1f} days ({recommended['description']})")
    print(f"   Monitor critical tasks: {', '.join([t['task_id'] for t in critical_tasks[:3]])}")
    
    print("\n" + "=" * 80)
    print("ADVANCED SIMULATION COMPLETE!")
    print("Dynamic critical path analysis provides more accurate risk assessment")
    print("than traditional deterministic methods.")
    print("=" * 80)


if __name__ == "__main__":
    main()
