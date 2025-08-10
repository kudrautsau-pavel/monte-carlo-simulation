"""
Task and Project Network classes for Monte Carlo simulation with critical path analysis.
"""

import numpy as np
from typing import List, Dict, Optional
from scipy import stats


class Task:
    """Represents a project task with PERT estimates and network properties."""
    
    def __init__(self, task_id: str, name: str, predecessors: List[str], 
                 optimistic: float, most_likely: float, pessimistic: float,
                 category: str = "general", resources: List[str] = None):
        self.id = task_id
        self.name = name
        self.predecessors = predecessors or []
        self.optimistic = optimistic
        self.most_likely = most_likely
        self.pessimistic = pessimistic
        self.category = category
        self.resources = resources or []
        
        # PERT parameters
        self.mean = (optimistic + 4 * most_likely + pessimistic) / 6
        self.std_dev = (pessimistic - optimistic) / 6
        
        # Network calculation properties (reset each iteration)
        self.duration = 0.0
        self.early_start = 0.0
        self.early_finish = 0.0
        self.late_start = 0.0
        self.late_finish = 0.0
        self.total_float = 0.0
        self.is_critical = False
        
        # Successors (calculated during network setup)
        self.successors = []
    
    def generate_duration(self) -> float:
        """Generate random duration using PERT Beta distribution."""
        if self.pessimistic <= self.optimistic:
            return self.most_likely
        
        # PERT Beta distribution parameters
        alpha = 4  # Standard PERT assumption
        beta = 4
        
        # Scale to task range
        scale = self.pessimistic - self.optimistic
        location = self.optimistic
        
        # Generate random duration
        duration = stats.beta.rvs(alpha, beta) * scale + location
        self.duration = duration
        return duration
    
    def reset_network_properties(self):
        """Reset network calculation properties for new iteration."""
        self.duration = 0.0
        self.early_start = 0.0
        self.early_finish = 0.0
        self.late_start = 0.0
        self.late_finish = 0.0
        self.total_float = 0.0
        self.is_critical = False


class ProjectNetwork:
    """Manages project task network and critical path calculations."""
    
    def __init__(self, tasks: Dict[str, Task]):
        self.tasks = tasks
        self.critical_paths = []
        self.project_duration = 0.0
        
        # Build successor relationships
        self._build_successor_relationships()
        
        # Validate network
        self._validate_network()
    
    def _build_successor_relationships(self):
        """Build successor relationships from predecessor data."""
        for task in self.tasks.values():
            task.successors = []
        
        for task in self.tasks.values():
            for pred_id in task.predecessors:
                if pred_id in self.tasks:
                    self.tasks[pred_id].successors.append(task.id)
    
    def _validate_network(self):
        """Validate network for circular dependencies."""
        visited = set()
        rec_stack = set()
        
        def has_cycle(task_id):
            if task_id in rec_stack:
                return True
            if task_id in visited:
                return False
            
            visited.add(task_id)
            rec_stack.add(task_id)
            
            for successor_id in self.tasks[task_id].successors:
                if has_cycle(successor_id):
                    return True
            
            rec_stack.remove(task_id)
            return False
        
        for task_id in self.tasks:
            if task_id not in visited:
                if has_cycle(task_id):
                    raise ValueError(f"Circular dependency detected involving task {task_id}")
    
    def generate_all_durations(self):
        """Generate random durations for all tasks."""
        for task in self.tasks.values():
            task.reset_network_properties()
            task.generate_duration()
    
    def calculate_forward_pass(self):
        """Calculate early start and early finish times."""
        # Topological sort for forward pass
        in_degree = {task_id: len(task.predecessors) for task_id, task in self.tasks.items()}
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        
        while queue:
            current_id = queue.pop(0)
            current_task = self.tasks[current_id]
            
            # Calculate early start
            if not current_task.predecessors:
                current_task.early_start = 0.0
            else:
                current_task.early_start = max([
                    self.tasks[pred_id].early_finish 
                    for pred_id in current_task.predecessors
                ])
            
            # Calculate early finish
            current_task.early_finish = current_task.early_start + current_task.duration
            
            # Update successors
            for successor_id in current_task.successors:
                in_degree[successor_id] -= 1
                if in_degree[successor_id] == 0:
                    queue.append(successor_id)
        
        # Project duration is the maximum early finish
        self.project_duration = max([task.early_finish for task in self.tasks.values()])
    
    def calculate_backward_pass(self):
        """Calculate late start and late finish times."""
        # Start from tasks with no successors
        for task in self.tasks.values():
            if not task.successors:
                task.late_finish = self.project_duration
            else:
                task.late_finish = min([
                    self.tasks[succ_id].late_start 
                    for succ_id in task.successors
                ])
            
            task.late_start = task.late_finish - task.duration
            task.total_float = task.late_start - task.early_start
            task.is_critical = abs(task.total_float) < 0.001  # Near zero tolerance
    
    def find_critical_path(self) -> List[str]:
        """Identify tasks on the critical path."""
        critical_tasks = [task.id for task in self.tasks.values() if task.is_critical]
        return critical_tasks
    
    def calculate_network(self) -> Dict:
        """Perform complete network calculation for current durations."""
        self.calculate_forward_pass()
        self.calculate_backward_pass()
        
        critical_path = self.find_critical_path()
        
        return {
            'project_duration': self.project_duration,
            'critical_path': critical_path,
            'critical_path_length': len(critical_path),
            'total_tasks': len(self.tasks)
        }
    
    def get_task_statistics(self) -> Dict:
        """Get current iteration task statistics."""
        return {
            task.id: {
                'duration': task.duration,
                'early_start': task.early_start,
                'early_finish': task.early_finish,
                'late_start': task.late_start,
                'late_finish': task.late_finish,
                'total_float': task.total_float,
                'is_critical': task.is_critical,
                'category': task.category
            }
            for task in self.tasks.values()
        }
