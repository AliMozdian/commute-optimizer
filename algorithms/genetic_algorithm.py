"""
algorithms/genetic_algorithm.py
Reference solution: Genetic Algorithm with elitism and tournament selection.
"""

from typing import Tuple, List, Set
import random

from algorithms.base import LocalSearchSolver
from core.state import State
from core.problem import CommuteProblem
from algorithms.operators import get_neighbors, crossover


class GeneticAlgorithmSolver(LocalSearchSolver):
    def __init__(self, problem: CommuteProblem, **kwargs):
        super().__init__(problem, **kwargs)
        self.population_size: int = int(self.params.get("population_size", 40))
        self.generations: int = int(self.params.get("generations", 120))
        self.crossover_rate: float = float(self.params.get("crossover_rate", 0.8))
        self.mutation_rate: float = float(self.params.get("mutation_rate", 0.25))
        self.elitism: int = int(self.params.get("elitism", 2))

    def _initialize_population(self) -> List[State]:
        """Creates an initial population using randomized neighborhood walks."""
        base_state = self.problem.generate_initial_state()
        valid_times = self.problem.get_valid_time_domain()
        pop: List[State] = []
        seen: Set[State] = set()

        for _ in range(self.population_size * 3):
            if len(pop) >= self.population_size:
                break
            rand_time = random.choice(valid_times)
            curr = State(path=base_state.path, departure_time=rand_time)
            # Take 1 to 3 random walks to diversify route topologies
            for _ in range(random.randint(0, 3)):
                nbrs = get_neighbors(curr, self.problem)
                if nbrs:
                    curr = random.choice(nbrs)
            if curr not in seen and self.problem.is_valid_state(curr):
                seen.add(curr)
                pop.append(curr)

        while len(pop) < self.population_size:
            pop.append(base_state)

        return pop

    def _tournament_select(self, population: List[State], k: int = 3) -> State:
        """Selects the fittest individual from a random tournament group."""
        tournament = random.sample(population, min(k, len(population)))
        return min(tournament, key=lambda s: self.problem.evaluate(s))

    def solve(self) -> Tuple[State, float]:
        population = self._initialize_population()
        global_best_state = min(population, key=lambda s: self.problem.evaluate(s))
        global_best_cost = self.problem.evaluate(global_best_state)
        self.history = [global_best_cost]

        for _ in range(self.generations):
            # Sort current generation by fitness (lowest cost first)
            population.sort(key=lambda s: self.problem.evaluate(s))
            gen_best = population[0]
            gen_best_cost = self.problem.evaluate(gen_best)

            if gen_best_cost < global_best_cost:
                global_best_cost = gen_best_cost
                global_best_state = gen_best

            self.history.append(global_best_cost)

            # Preserve elite solutions
            new_population: List[State] = population[: self.elitism]

            # Reproduction loop
            while len(new_population) < self.population_size:
                p1 = self._tournament_select(population)
                p2 = self._tournament_select(population)

                # Crossover
                if random.random() < self.crossover_rate:
                    child = crossover(p1, p2, self.problem)
                else:
                    child = p1

                # Mutation
                if random.random() < self.mutation_rate:
                    nbrs = get_neighbors(child, self.problem)
                    if nbrs:
                        child = random.choice(nbrs)

                if self.problem.is_valid_state(child):
                    new_population.append(child)
                else:
                    new_population.append(p1)

            population = new_population

        return global_best_state, global_best_cost
