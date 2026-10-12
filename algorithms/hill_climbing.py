"""
algorithms/hill_climbing.py
Reference solution: Steepest Descent with sideways move tracking and restarts.
"""

from typing import Tuple
import random

from algorithms.base import LocalSearchSolver
from core.state import State
from core.problem import CommuteProblem
from algorithms.operators import get_neighbors


class HillClimbingSolver(LocalSearchSolver):
    def __init__(self, problem: CommuteProblem, **kwargs):
        super().__init__(problem, **kwargs)
        self.max_sideways: int = self.params.get("max_sideways", 100)
        self.max_restarts: int = self.params.get("max_restarts", 5)

    def _generate_random_state(self) -> State:
        """Constructs a randomized valid initial configuration."""
        base_state = self.problem.generate_initial_state()
        valid_times = self.problem.get_valid_time_domain()
        rand_time = random.choice(valid_times)

        curr = State(path=base_state.path, departure_time=rand_time)
        # Apply a few random neighbor steps to diversify the starting route
        for _ in range(random.randint(1, 4)):
            nbrs = get_neighbors(curr, self.problem)
            if nbrs:
                curr = random.choice(nbrs)
        return curr

    def solve(self) -> Tuple[State, float]:
        global_best_state = self.problem.generate_initial_state()
        global_best_cost = self.problem.evaluate(global_best_state)
        self.history = [global_best_cost]

        for restart_idx in range(self.max_restarts + 1):
            current = (
                self.problem.generate_initial_state()
                if restart_idx == 0
                else self._generate_random_state()
            )
            current_cost = self.problem.evaluate(current)
            sideways_count = 0

            if current_cost < global_best_cost:
                global_best_cost = current_cost
                global_best_state = current

            while True:
                neighbors = get_neighbors(current, self.problem)
                if not neighbors:
                    break

                # Steepest Descent: evaluate all neighbors and pick the minimum
                best_neighbor = None
                best_neighbor_cost = float("inf")

                for nbr in neighbors:
                    c = self.problem.evaluate(nbr)
                    if c < best_neighbor_cost:
                        best_neighbor_cost = c
                        best_neighbor = nbr

                if best_neighbor is None:
                    break

                if best_neighbor_cost < current_cost:
                    # Strict improvement
                    current = best_neighbor
                    current_cost = best_neighbor_cost
                    sideways_count = 0
                    if current_cost < global_best_cost:
                        global_best_cost = current_cost
                        global_best_state = current
                elif abs(best_neighbor_cost - current_cost) < 1e-9:
                    # Sideways plateau move
                    if sideways_count < self.max_sideways:
                        current = best_neighbor
                        current_cost = best_neighbor_cost
                        sideways_count += 1
                    else:
                        break  # Sideways budget exhausted
                else:
                    # Local minimum: all neighbors are strictly worse
                    break

                self.history.append(global_best_cost)

        return global_best_state, global_best_cost
