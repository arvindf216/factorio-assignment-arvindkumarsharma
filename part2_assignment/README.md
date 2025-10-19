# Part 2 Assignment

This project contains the implementation for the Factory Steady State and Bounded Belts assignment.

## Factory Modeling Choices

The factory problem is modeled as a standard **Linear Programming (LP)** problem. The goal is to find an optimal vector of recipe craft rates that minimizes machine usage while satisfying all production and resource constraints.

### LP Formulation

The problem is formulated in the following structure, which is then solved using `scipy.optimize.linprog`:

**minimize**
`c @ x`

**such that**
`A_ub @ x <= b_ub`
`A_eq @ x == b_eq`
`0 <= x`

*   **`x` (Decision Variables)**: A vector where each element `x_r` represents the **crafts per minute** for a given recipe `r`.
*   **`c` (Objective Function)**: To minimize total machines, each coefficient `c_r` is the number of machines for one craft/min of recipe `r`, calculated as `1 / eff_crafts_per_min(r)`.
*   **`A_eq @ x == b_eq` (Equality Constraints)**: These enforce **item balances**. For intermediate items, net flow (production - consumption) is zero. For the target item, net flow equals the required `target_rate`.
*   **`A_ub @ x <= b_ub` (Inequality Constraints)**: These enforce **resource limits**, ensuring raw material consumption and machine usage do not exceed their respective caps.

### Specific Modeling Points

*   **Module Application**: `speed` and `productivity` modules are handled by directly modifying the coefficients in the LP matrices. `speed` modules alter the effective crafts per minute, affecting both the objective function (`c`) and machine usage constraints. `productivity` modules increase item output, so they only modify the production side of the item balance equations (`A_eq`).

*   **Cycles, Byproducts, and Self-Contained Recipes**: The LP formulation inherently handles these cases. By defining conservation of flow constraints for *all* intermediate items (setting their net production to zero), the model correctly balances complex recipe chains, including those with cycles (A -> B -> A) or byproducts. The solver finds the necessary rates to maintain a perfect steady state.

*   **Infeasibility Detection**: If the primary LP problem is infeasible for the requested `target_rate`, a binary search is performed. It iteratively lowers the target rate and re-solves the LP to find the maximum possible feasible production rate.

## Belts Modeling Choices

The problem of finding a feasible flow in a network with lower bounds and node capacities is transformed into a standard maximum flow problem, which is then solved using a hand-rolled **Edmonds-Karp algorithm**.

### Modeling Steps

1.  **Node-Splitting for Capacity Constraints**: Throughput capacity on a node `v` is converted into an edge capacity by splitting the node into `v_in` and `v_out`, connected by a new edge with capacity `cap(v)`.

2.  **Transformation for Lower Bounds**: To handle flow lower bounds, a new flow variable `f' = f - l` is used. This transforms the edge constraints to the standard `0 <= f' <= c - l`, but it creates an imbalance `B(v)` at each node.

3.  **Feasibility Check Strategy**: To resolve the imbalances, a circulation network is created with a super-source `s*` and a super-sink `t*`. Nodes with a net demand are connected from `s*`, and nodes with a net supply are connected to `t*`. A feasible flow exists if and only if the max flow in this circulation network equals the total demand.

### Infeasibility Reporting (Min-Cut)

When a belts problem is infeasible, a min-cut analysis is performed to identify the bottleneck.

*   **`cut_reachable`**: After the feasibility check fails, a Breadth-First Search (BFS) is performed on the residual graph starting from the super-source (`s*`) to find all nodes on the source side of the cut.

*   **`tight_edges`**: These are edges crossing the cut from a reachable to an unreachable node that are fully saturated (zero residual capacity).

*   **`tight_nodes`**: A node is "tight" if it is a point of constriction. This includes nodes with an explicit `node_caps` limit that is saturated, and nodes on the cut boundary whose outgoing edges across the cut are all saturated.

## Numeric Approach and Determinism

*   **Solver Choice**: `scipy.optimize.linprog` is used for the factory problem as it is a robust, well-tested solver for LP problems. For the belts problem, a from-scratch implementation of Edmonds-Karp is used to provide precise control over the max-flow/min-cut logic and reporting.

*   **Tolerances**: A standard tolerance of `1e-9` is used for floating-point comparisons in both problems to manage potential precision issues.

*   **Tie-Breaking and Determinism**: Deterministic output is guaranteed. For the factory problem, while the LP solver has its own internal tie-breaking, determinism is ensured by consistently ordering recipes and items (lexicographically) before constructing the constraint matrices. For the belts problem, the Edmonds-Karp implementation is deterministic by nature (due to the BFS path selection).

## Failure Modes & Edge Cases

*   **Infeasible Constraints**: Infeasible raw material supplies or machine counts in the factory problem are detected by the LP solver, triggering the binary search for the maximum feasible rate. In the belts problem, they are caught by the feasibility check.

*   **Degenerate or Redundant Recipes**: The LP formulation is robust to these cases. A redundant recipe (e.g., two identical ways to make an item) simply presents the solver with an additional valid path, and it will choose the one that best minimizes the objective (i.e., uses fewer machines). 

*   **Disconnected Graph Components (Belts)**: The graph construction and max-flow algorithm naturally handle disconnected components. If a source is in a component disconnected from the sink, its flow will simply not be routed, and the feasibility check will correctly identify the deficit.

## Note on the Sample Output in the PDF (Part A)

The assignment PDF provides a sample input and output on page 5. The provided sample output is **not a feasible solution** for the given input. Here's why:

1.  **Raw Material Violation**: The plan requires **5400** `copper_ore` per minute, but the supply is limited to **5000**.

2.  **Intermediate Item Imbalance**: The factory would not be in a steady state. For example, the plan produces a surplus of **360** iron plates per minute.

3.  **Incorrect Target Production**: The plan would produce **1980** green circuits per minute, exceeding the required target of 1800.

The correct, feasible solution provided by this tool accounts for all module effects to satisfy all constraints exactly.