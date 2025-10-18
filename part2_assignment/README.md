
# Part 2 Assignment

This project contains the implementation for the Factory Steady State and Bounded Belts assignment.

## Factory Modeling Choices

The factory problem is modeled as a standard **Linear Programming (LP)** problem. The goal is to find an optimal vector of recipe craft rates that minimizes machine usage while satisfying all production and resource constraints.

The problem is formulated in the following structure, which is then solved using `scipy.optimize.linprog`:

**minimize**
`c @ x`

**such that**
`A_ub @ x <= b_ub`
`A_eq @ x == b_eq`
`0 <= x`

---

Here is what each component represents:

*   **`x` (Decision Variables)**: This is a vector where each element `x_r` represents the **crafts per minute** for a given recipe `r`. This is what the solver is trying to find.

*   **`c` (Objective Function Coefficients)**: This vector represents the "cost" of each craft. To minimize the total number of machines, each element `c_r` is the number of machines required for one craft per minute of recipe `r`. It is calculated as `1 / eff_crafts_per_min(r)`. Therefore, `c @ x` equals the **total number of machines used**.

*   **`A_eq @ x == b_eq` (Equality Constraints)**: These equations enforce **perfect balance**.
    *   For **intermediate items**, they ensure that the net flow (production minus consumption) is exactly zero.
    *   For the **target item**, they ensure the net flow is equal to the required `target_rate`.

*   **`A_ub @ x <= b_ub` (Inequality Constraints)**: These inequalities enforce **resource limits**.
    *   For **raw materials**, they ensure that total consumption does not exceed the `raw_supply_per_min`.
    *   For **machines**, they ensure that the total number of machines of each type used does not exceed the `max_machines` limit.

*   **`0 <= x` (Bounds)**: This ensures that the craft rates (`x_r`) can only be non-negative, as it's impossible to run a recipe a negative number of times. The upper bound is infinity.

---
The `scipy.optimize.linprog` function is used to solve this LP problem. If the initial problem is infeasible, a binary search is performed on the target rate to find the maximum feasible rate.

## Belts Modeling Choices

The problem of finding a feasible flow in a network with lower bounds and node capacities is transformed into a standard maximum flow problem through a series of steps. The **Edmonds-Karp algorithm** is then used to solve the transformed problem.

### Mathematical Formulation

A flow network is a directed graph `G = (V, E)` with sources `S`, a sink `T`, and the following properties:
- For each edge `(u,v) in E`, a lower bound `l(u,v) >= 0` and an upper capacity `c(u,v)`.
- For some nodes `v in V`, a throughput capacity `cap(v)`.

The goal is to find a flow `f(u,v)` for each edge that satisfies:
1.  **Capacity Constraints**: `l(u,v) <= f(u,v) <= c(u,v)`
2.  **Flow Conservation**: For any node `v` that is not a source or sink, the total flow entering the node must equal the total flow leaving it.
3.  **Node Capacity**: For any node `v` with a capacity, the total flow passing through it must not exceed `cap(v)`.

### Modeling Steps

The problem is solved using the following transformations:

**Step 1: Eliminate Node Capacities**
Throughput capacity on a node `v` is converted into an edge capacity. The node `v` is split into two nodes, `v_in` and `v_out`, connected by a new edge `(v_in, v_out)` with capacity `cap(v)`. All original edges entering `v` now enter `v_in`, and all original edges leaving `v` now leave from `v_out`. This enforces the node capacity as a standard edge capacity.

**Step 2: Eliminate Lower Bounds**
This is the main transformation. For a flow `f` to be feasible, we define a new flow `f'(u,v) = f(u,v) - l(u,v)`. The new constraints on `f'` are `0 <= f'(u,v) <= c(u,v) - l(u,v)`, which is the standard form for a max-flow problem.

However, this change breaks flow conservation. The new conservation equation has an **imbalance** `B(v)` at each node `v`:
`sum(f'(u,v) for u) - sum(f'(v,w) for w) = sum(l(v,w) for w) - sum(l(u,v) for u) = -B(v)`
where `B(v) = sum(l(u,v) for u) - sum(l(v,w) for w)`.
- If `B(v) > 0`, node `v` has a net **demand** of `B(v)`.
- If `B(v) < 0`, node `v` has a net **supply** of `-B(v)`.

**Step 3: Check Feasibility (The Circulation Problem)**
To satisfy the imbalances, we must check if a valid "circulation" `f'` exists. We do this by creating a new network with a global super-source `s*` and super-sink `t*`:
- For each node `v` with a demand `B(v) > 0`, add an edge `(s*, v)` with capacity `B(v)`.
- For each node `v` with a supply `B(v) < 0`, add an edge `(v, t*)` with capacity `-B(v)`.

A feasible flow exists in the original network **if and only if** the maximum flow from `s*` to `t*` in this new network is equal to the total demand from all nodes. If the max flow is less than the total demand, it's impossible to satisfy the lower bounds, and the problem is infeasible.

**Step 4: The Role of Edmonds-Karp**
The Edmonds-Karp algorithm is the specific max-flow algorithm used to solve the circulation problem in Step 3 and to find the final flow distribution. It works by repeatedly finding an "augmenting path" from a source to a sink in the residual graph. It uses a **Breadth-First Search (BFS)** to find the shortest augmenting path in terms of the number of edges. This process is repeated until no more augmenting paths can be found.

## Note on the Sample Output in the PDF (Part A)

The assignment PDF provides a sample input and output on page 5. The provided sample output is **not a feasible solution** for the given input. Here's why:

1.  **Raw Material Violation**: The plan requires **5400** `copper_ore` per minute, but the supply is limited to **5000**.

2.  **Intermediate Item Imbalance**: The factory would not be in a steady state. For example, consider iron plates:
    *   **Consumption**: The `green_circuit` recipe runs 1800 times/min, consuming `1800` iron plates.
    *   **Production**: The `iron_plate` recipe also runs 1800 times/min, but on a machine with a `+20%` productivity bonus, producing `1800 * 1.2 = 2160` iron plates.
    *   This creates a surplus of **360** iron plates per minute, violating the perfect balance rule.

3.  **Incorrect Target Production**: The plan would produce **1980** green circuits per minute (`1800 crafts * 1.1 items/craft`), exceeding the required target of 1800.

The correct, feasible solution provided by this tool accounts for all module effects to satisfy all constraints exactly.
