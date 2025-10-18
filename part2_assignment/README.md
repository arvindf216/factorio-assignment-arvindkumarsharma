
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

The belts problem is modeled as a maximum flow problem on a directed graph. The goal is to find a valid flow from the sources to the sink that respects the capacity constraints of the edges and nodes.

The problem is transformed to handle lower bounds on edges and node capacities. The transformation involves creating a new graph with a super-source and a super-sink to check for feasibility. After the feasibility check, the main max-flow algorithm is run to find the optimal flow.

The Edmonds-Karp algorithm is used to find the maximum flow. The algorithm is implemented from scratch using a breadth-first search to find augmenting paths in the residual graph.

## Note on the Sample Output in the PDF (Part A)

The assignment PDF provides a sample input and output on page 5. The provided sample output is **not a feasible solution** for the given input. Here's why:

1.  **Raw Material Violation**: The plan requires **5400** `copper_ore` per minute, but the supply is limited to **5000**.

2.  **Intermediate Item Imbalance**: The factory would not be in a steady state. For example, consider iron plates:
    *   **Consumption**: The `green_circuit` recipe runs 1800 times/min, consuming `1800` iron plates.
    *   **Production**: The `iron_plate` recipe also runs 1800 times/min, but on a machine with a `+20%` productivity bonus, producing `1800 * 1.2 = 2160` iron plates.
    *   This creates a surplus of **360** iron plates per minute, violating the perfect balance rule.

3.  **Incorrect Target Production**: The plan would produce **1980** green circuits per minute (`1800 crafts * 1.1 items/craft`), exceeding the required target of 1800.

The correct, feasible solution provided by this tool accounts for all module effects to satisfy all constraints exactly.
