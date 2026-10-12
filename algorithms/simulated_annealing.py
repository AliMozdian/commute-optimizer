"""
algorithms/simulated_annealing.py
Reference solution: Simulated Annealing with exponential cooling.
"""

from typing import Tuple
import math
import random

from algorithms.base import LocalSearchSolver
from core.state import State
from core.problem import CommuteProblem
from algorithms.operators import get_neighbors


class SimulatedAnnealingSolver(LocalSearchSolver):
    def __init__(self, problem: CommuteProblem, **kwargs):
        super().__init__(problem, **kwargs)
        self.initial_temp: float = float(self.params.get("initial_temp", 100.0))
        self.cooling_rate: float = float(self.params.get("cooling_rate", 0.995))
        self.min_temp: float = float(self.params.get("min_temp", 0.001))
        self.max_iterations: int = int(self.params.get("max_iterations", 2500))

    def solve(self) -> Tuple[State, float]:
        current = self.problem.generate_initial_state()
        current_cost = self.problem.evaluate(current)

        best_state = current
        best_cost = current_cost

        temp = self.initial_temp
        self.history = [best_cost]

        for step in range(self.max_iterations):
            if temp <= self.min_temp:
                break

            neighbors = get_neighbors(current, self.problem)
            if not neighbors:
                break

            # Pick a random candidate neighbor
            candidate = random.choice(neighbors)
            candidate_cost = self.problem.evaluate(candidate)
            delta_e = candidate_cost - current_cost  # Minimization: delta_e < 0 is improvement

            # Metropolis acceptance step
            if delta_e < 0:
                current = candidate
                current_cost = candidate_cost
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_state = current
            else:
                prob = math.exp(-delta_e / max(temp, 1e-12))
                if random.random() < prob:
                    current = candidate
                    current_cost = candidate_cost

            self.history.append(best_cost)
            temp *= self.cooling_rate

        return best_state, best_cost
