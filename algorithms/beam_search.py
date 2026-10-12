"""
algorithms/beam_search.py
Reference solution: Local Beam Search with K communicating states.
"""

from typing import Tuple, List, Set
import random

from algorithms.base import LocalSearchSolver
from core.state import State
from core.problem import CommuteProblem
from algorithms.operators import get_neighbors


class LocalBeamSearchSolver(LocalSearchSolver):
    def __init__(self, problem: CommuteProblem, **kwargs):
        super().__init__(problem, **kwargs)
        self.beam_width: int = int(self.params.get("beam_width", 5))
        self.max_iterations: int = int(self.params.get("max_iterations", 150))

    def _initialize_beam(self) -> List[State]:
        """Builds an initial set of K unique, valid configurations."""
        initial = self.problem.generate_initial_state()
        beam = [initial]
        seen: Set[State] = {initial}

        # Expand neighbors from seed states to collect K diverse starting candidates
        queue = [initial]
        while queue and len(beam) < self.beam_width:
            curr = queue.pop(0)
            nbrs = get_neighbors(curr, self.problem)
            random.shuffle(nbrs)
            for nbr in nbrs:
                if nbr not in seen and self.problem.is_valid_state(nbr):
                    seen.add(nbr)
                    beam.append(nbr)
                    queue.append(nbr)
                    if len(beam) == self.beam_width:
                        break

        # Fallback padding if graph is very sparse
        while len(beam) < self.beam_width:
            beam.append(initial)

        return beam

    def solve(self) -> Tuple[State, float]:
        beam = self._initialize_beam()
        best_state = min(beam, key=lambda s: self.problem.evaluate(s))
        best_cost = self.problem.evaluate(best_state)
        self.history = [best_cost]

        for _ in range(self.max_iterations):
            successors_pool: List[State] = []
            seen: Set[State] = set()

            # Collective successor generation across all K active beams
            for state in beam:
                for nbr in get_neighbors(state, self.problem):
                    if nbr not in seen and self.problem.is_valid_state(nbr):
                        seen.add(nbr)
                        successors_pool.append(nbr)

            if not successors_pool:
                break

            # Sort the entire pool by objective value (lowest travel time first)
            successors_pool.sort(key=lambda s: self.problem.evaluate(s))
            beam = successors_pool[: self.beam_width]

            curr_best = beam[0]
            curr_best_cost = self.problem.evaluate(curr_best)

            if curr_best_cost < best_cost:
                best_cost = curr_best_cost
                best_state = curr_best

            self.history.append(best_cost)

        return best_state, best_cost
