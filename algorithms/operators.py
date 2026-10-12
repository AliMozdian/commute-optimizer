"""
algorithms/operators.py
Reference solution: Candidate neighborhood generation and genetic crossover.
"""

from typing import List, Optional, Set
import random

from core.state import State
from core.problem import CommuteProblem


def _find_detour_subpaths(
    network,
    u: str,
    v: str,
    forbidden: Set[str],
    max_hops: int = 5
) -> List[List[str]]:
    """
    Finds simple, loop-free alternate subpaths from u to v in the network
    that do not visit any nodes in the forbidden set.
    """
    valid_detours: List[List[str]] = []
    # Stack stores: (current_node, path_accumulated)
    stack = [(u, [u])]

    while stack:
        curr, path = stack.pop()
        if curr == v and len(path) > 1:
            valid_detours.append(path)
            if len(valid_detours) >= 4:
                break
            continue

        if len(path) > max_hops:
            continue

        neighbors = network.get_neighbors(curr)
        for nxt in neighbors:
            if nxt not in forbidden and nxt not in path:
                stack.append((nxt, path + [nxt]))

    return valid_detours


def get_neighbors(state: State, problem: CommuteProblem) -> List[State]:
    """
    Generates adjacent configurations for local search:
    1. Departure time shifts (+/- t_step).
    2. Topological path detours between random waypoint pairs.
    """
    neighbors: List[State] = []
    seen = {state}

    # 1. Time Shifts (exploration across the departure time window)
    for delta in (-problem.t_step, problem.t_step):
        new_time = round(state.departure_time + delta, 2)
        if problem.t_min <= new_time <= problem.t_max:
            cand = State(path=state.path, departure_time=new_time)
            if cand not in seen and problem.is_valid_state(cand):
                neighbors.append(cand)
                seen.add(cand)

    # 2. Route Mutations (local detours)
    path_len = len(state.path)
    if path_len >= 2:
        # Try several random waypoint pairs along the path
        indices = list(range(path_len))
        pairs_to_try = []
        for _ in range(min(5, path_len)):
            i = random.choice(indices[:-1])
            j = random.choice(indices[i + 1:])
            pairs_to_try.append((i, j))

        for i, j in pairs_to_try:
            u, v = state.path[i], state.path[j]
            # Nodes outside the [i, j] segment cannot be reused (avoids loops)
            forbidden_nodes = set(state.path[:i]) | set(state.path[j + 1:])

            detours = _find_detour_subpaths(
                problem.network, u, v, forbidden_nodes, max_hops=4
            )
            for detour in detours:
                new_path = tuple(list(state.path[:i]) + detour + list(state.path[j + 1:]))
                cand = State(path=new_path, departure_time=state.departure_time)
                if cand not in seen and problem.is_valid_state(cand):
                    neighbors.append(cand)
                    seen.add(cand)

    # Fallback: if no structural detour was found, add wider time shifts
    if len(neighbors) <= 1:
        for mult in (-2, 2, -3, 3):
            alt_time = round(state.departure_time + mult * problem.t_step, 2)
            if problem.t_min <= alt_time <= problem.t_max:
                cand = State(path=state.path, departure_time=alt_time)
                if cand not in seen and problem.is_valid_state(cand):
                    neighbors.append(cand)
                    seen.add(cand)

    return neighbors


def crossover(parent1: State, parent2: State, problem: CommuteProblem) -> State:
    """
    Performs topological crossover:
    - Finds shared intermediate nodes and splices parent paths.
    - Averages departure times aligned to t_step.
    - Falls back to the fitter parent path if paths are disjoint or cycles occur.
    """
    # Blended departure time aligned to t_step grid
    avg_time = (parent1.departure_time + parent2.departure_time) / 2.0
    steps = round((avg_time - problem.t_min) / problem.t_step)
    child_time = round(problem.t_min + steps * problem.t_step, 2)
    child_time = max(problem.t_min, min(problem.t_max, child_time))

    # Shared waypoints (excluding origin and destination)
    p1_mid = parent1.path[1:-1]
    p2_mid = parent2.path[1:-1]
    common_waypoints = [node for node in p1_mid if node in set(p2_mid)]

    if common_waypoints:
        pivot = random.choice(common_waypoints)
        idx1 = parent1.path.index(pivot)
        idx2 = parent2.path.index(pivot)

        # Splice: parent1 up to pivot + parent2 from pivot onward
        spliced_path = tuple(list(parent1.path[:idx1]) + list(parent2.path[idx2:]))
        candidate = State(path=spliced_path, departure_time=child_time)
        if problem.is_valid_state(candidate):
            return candidate

    # Fallback to the fitter parent route with the blended time
    fitter_path = (
        parent1.path
        if problem.evaluate(parent1) <= problem.evaluate(parent2)
        else parent2.path
    )
    return State(path=fitter_path, departure_time=child_time)
