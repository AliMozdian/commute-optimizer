# Commute Optimizer: Urban Route & Departure Scheduling via Local Search

An extensible benchmarking environment and practical assignment for solving dynamic urban commute problems using Classical Artificial Intelligence and Local Search heuristics.

---

## 1. Problem Overview

In classical pathfinding (e.g., Dijkstra, A*), an agent incrementally explores edges from origin to destination. However, in real-world urban networks, travel times are **time-dependent**: departing at 07:45 AM yields drastically different delays compared to departing at 08:30 AM due to dynamic congestion.

This project formulates the commute task as a **Complete-State Configuration Optimization Problem**. Rather than deciding turns step-by-step, the search agent optimizes an entire commute configuration simultaneously:

$$x = \langle P, \; t_{\text{start}} \rangle$$

where:
* $P = \langle v_0, v_1, \dots, v_m \rangle$ is a complete, loop-free topological path from Origin ($v_0$) to Destination ($v_m$) in the road network.
* $t_{\text{start}}$ is the departure time chosen from a discrete set of options within a commute window:
  $$\mathcal{T} = \{t_{\min} + k \cdot \Delta t \mid k \in \mathbb{N}_0, \; t_{\min} + k \cdot \Delta t \le t_{\max}\}$$

The objective is to discover the configuration $x^*$ that minimizes the total commute duration $f(x)$ under dynamic rush-hour traffic waves.

---

## 2. Mathematical Formulation

### 2.1 The Road Network
The urban layout is represented as a directed graph $G = (V, E)$. Every directed edge $e = (u, v) \in E$ has:
* A baseline free-flow travel time $t_e^{\text{base}} > 0$ (the traversal time under zero traffic).
* Spatial 2D coordinates $(x_v, y_v)$ for visualization.

### 2.2 Dynamic Congestion Model
Each road segment experiences dynamic, time-dependent traffic intensity represented by a non-negative multiplier $C_e(t) \ge 0$. The dynamic travel time $\tau(e, t)$ to traverse edge $e$ when entered at timestamp $t$ is:

$$\tau(e, t) = t_e^{\text{base}} \times \big(1 + C_e(t)\big)$$

Congestion waves are generated using a **Gaussian Rush-Hour Peak Model**:

$$C_e(t) = \sum_{k} A_{e, k} \cdot \exp\left(-\frac{(t - \mu_{e, k})^2}{2\sigma_{e, k}^2}\right)$$

where $\mu$ denotes peak bottleneck time, $\sigma$ controls duration, and $A$ indicates congestion severity.

### 2.3 The Objective Function $f(x)$
Given a candidate configuration $x = \big(\langle v_0, v_1, \dots, v_m \rangle, \; t_{\text{start}}\big)$, the simulation advances the clock along the path using a First-In-First-Out (FIFO) dynamic network simulation:

1. Initialize clock: $t_0 = t_{\text{start}}$
2. For each successive edge $e_i = (v_i, v_{i+1})$ along path $P$:
   $$\Delta t_i = \tau(e_i, t_i)$$
   $$t_{i+1} = t_i + \Delta t_i$$
3. Total travel duration:
   $$f(x) = t_m - t_{\text{start}} = \sum_{i=0}^{m-1} \Delta t_i$$

If a state contains cycles, lacks path continuity, or sets a departure time outside $[t_{\min}, t_{\max}]$, the evaluation engine assigns an infinite penalty: $f(x) = \infty$.

---

## 3. Local Search Algorithms

You will implement four local search algorithms:

1. **Hill Climbing (Steepest Descent)**:
   * Greedily transitions to the neighboring state with the lowest travel duration.
   * Handles flat local minima and shoulders by allowing a limited budget of sideways moves (`max_sideways`).
   * Escapes sub-optimal local basins using random restarts (`max_restarts`).

2. **Simulated Annealing**:
   * A stochastic search method governed by an exponential cooling schedule $T_{k+1} = \alpha \cdot T_k$.
   * Improvements ($\Delta E < 0$) are always accepted.
   * Sub-optimal moves ($\Delta E \ge 0$) are accepted probabilistically via the Metropolis criterion:
     $$P(\text{accept}) = \exp\left(-\frac{\Delta E}{T}\right)$$

3. **Local Beam Search**:
   * Simultaneously tracks $K$ candidate commute plans.
   * In each iteration, successors are generated from all $K$ active states and pooled together.
   * The top $K$ configurations from the entire pool are selected for the next iteration.

4. **Genetic Algorithm (GA)**:
   * Maintains a population of valid commute configurations across successive generations.
   * Uses fitness assignment to bias selection (e.g., Tournament or Roulette Wheel) toward faster routes.
   * Performs topological crossover by identifying shared intermediate nodes between parent routes to splice sub-paths and blend departure times.
   * Applies stochastic mutation (detours or time adjustments) to maintain population diversity.

---

## 4. Repository Architecture

```text
commute-optimizer/
│
├── core/                         # [DO NOT MODIFY] Core simulation engine
│   ├── graph.py                  # Directed road network representation & JSON I/O
│   ├── state.py                  # Immutable State(path, departure_time)
│   ├── congestion.py             # Dynamic congestion models
│   └── problem.py                # Dynamic FIFO path evaluator f(x)
│
├── algorithms/                   # [YOUR IMPLEMENTATION AREA]
│   ├── operators.py              # Candidate neighborhood generation & crossover
│   ├── base.py                   # Abstract base solver class
│   ├── hill_climbing.py          # Hill Climbing solver
│   ├── simulated_annealing.py    # Simulated Annealing solver
│   ├── beam_search.py            # Local Beam Search solver
│   └── genetic_algorithm.py      # Genetic Algorithm solver
│
├── visualization/                # Plotting utilities
│   ├── plot_routes.py            # Network renderer with traffic heatmaps
│   └── plot_metrics.py           # Objective convergence curve plotter
│
├── data/                         # Maps and scenario files
│   ├── maps/                     # Network topology definitions
│   └── scenarios/                # Congestion profiles and rush-hour bottlenecks
│
├── config.json                   # Centralized hyperparameter configuration
├── main.py                       # CLI execution and benchmarking harness
└── requirements.txt              # Dependencies
```

---

## 5. Getting Started

### Prerequisites
* Python 3.9+
* Recommended: Virtual environment (`venv` or `conda`)

### Fork This Repository
First you need to <ins>**fork this repo**</ins> by your personal GitHub account, so you can develop your code over this already built standard environment.

### Setup
```bash
git clone <your_forked_repository_url>
cd commute-optimizer
python -m venv .venv
source .venv/bin/activate       # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running Solvers
Execute individual algorithms or benchmark all four solvers side-by-side using `main.py`:

```bash
# Run Simulated Annealing on the default map
python main.py --algo sa

# Benchmark all implemented algorithms and display convergence curves
python main.py --algo all --seed 42 --plot-metrics

# Visualize the optimal route chosen by the Genetic Algorithm on the network map
python main.py --algo ga --plot-route

# Run benchmarks on a custom map and save generated plots to disk
python main.py --algo all --map data/maps/toy_graph.json --scenario data/scenarios/rush_hour.json --save-figs
```

#### CLI Arguments
* `--algo`: Solver to run (`hc`, `sa`, `beam`, `ga`, or `all`).
* `--map`: Path to the road network JSON file.
* `--scenario`: Path to the congestion scenario JSON file.
* `--config`: Path to hyperparameter configuration file (defaults to `config.json`).
* `--seed`: Integer seed for deterministic runs.
* `--plot-route`: Renders the road network with traffic heat and the chosen path.
* `--plot-metrics`: Displays convergence curves ($f(x)$ vs. iteration step).
* `--save-figs`: Saves generated plots to disk as PNG images instead of displaying a GUI window.

---

## 6. Hyperparameter Configuration (`config.json`)

To decouple search logic from hardcoded constants, all tunable parameters are stored in `config.json`:

```json
{
  "problem": {
    "origin": "Home",
    "destination": "Uni",
    "t_min": 420.0,
    "t_max": 600.0,
    "t_step": 5.0
  },
  "hill_climbing": {
    "max_sideways": 100,
    "max_restarts": 5
  },
  "simulated_annealing": {
    "initial_temp": 100.0,
    "cooling_rate": 0.995,
    "min_temp": 0.001,
    "max_iterations": 2500
  },
  "beam_search": {
    "beam_width": 5,
    "max_iterations": 150
  },
  "genetic_algorithm": {
    "population_size": 40,
    "generations": 120,
    "crossover_rate": 0.8,
    "mutation_rate": 0.25,
    "elitism": 2
  }
}
```

### Adding New Parameters
Solvers inherit from `LocalSearchSolver` and receive these dictionary parameters dynamically via `**kwargs`. To add a new parameter (e.g., `tournament_size`):
1. Add the key-value pair under the corresponding block in `config.json`.
2. Retrieve it inside your solver's `__init__` via `self.params.get("tournament_size", default_val)`.
3. No changes to `main.py` or the evaluation pipeline are needed.

---

## 7. Implementation Tasks


You must complete the implementation of files located in `algorithms/`:

1. **`algorithms/operators.py`**:
   * `get_neighbors(state, problem)`: Generate adjacent configurations by perturbing departure times ($\pm \Delta t$) and finding valid, loop-free detour paths between waypoints.
   * `crossover(parent1, parent2, problem)`: Recombine two routes using a shared intermediate junction node and blend their departure times.
2. **`algorithms/hill_climbing.py`**: Implement steepest descent with sideways move tracking and restarts.
3. **`algorithms/simulated_annealing.py`**: Implement the Metropolis acceptance criterion and temperature cooling schedule.
4. **`algorithms/beam_search.py`**: Implement pooled successor generation across $K$ states and select the top $K$.
5. **`algorithms/genetic_algorithm.py`**: Implement fitness calculation, parent selection, crossover, mutation, and elitism.

### Invariants & Requirements
* **Path Validity:** Every generated path must be a continuous sequence of directed edges from `problem.origin` to `problem.destination`.
* **No Cycles:** Paths must not contain duplicate nodes.
* **Time Bounds:** Departure times must remain within $[t_{\min}, t_{\max}]$.
* **History Tracking:** Record the minimum objective cost at each step into `self.history` for metric plotting.

---

## 8. Submit Your Homework

Remember that you must <ins>**fork this repo**</ins> to your personal GitHub account, and to submit your homework, send the link to your forked repo on the given platform (Quera).

Make sure to **commit** your work **regularly** to show progress towards solving the problem using different algorithms, and compare the results in your final report document (Markdown or PDF).

**Attention**: Send the link to your repo before the deadline and **DO NOT COMMIT** ANY CHANGES <ins>AFTER THE DEADLINE</ins>.
Late changes will lead to **HUGE PENALTIES**, if not canceling your whole commit after the deadline.
