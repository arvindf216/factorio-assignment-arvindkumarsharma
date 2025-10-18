
# Part 2 Assignment

This project contains the implementation for the Factory Steady State and Bounded Belts assignment.

## Factory Modeling Choices

The factory problem is modeled as a linear programming problem. The objective is to minimize the total number of machines used, which is a linear function of the recipe production rates. The constraints are as follows:

*   **Item Conservation:** The production and consumption of each intermediate item must be balanced. This is enforced using equality constraints.
*   **Target Production:** The production of the target item must meet the specified rate. This is also an equality constraint.
*   **Raw Material Supply:** The consumption of raw materials must not exceed the available supply. This is enforced using inequality constraints.
*   **Machine Capacity:** The number of machines of each type used must not exceed the available capacity. This is also an inequality constraint.

The `scipy.optimize.linprog` function is used to solve the linear program. If the problem is infeasible, a binary search is performed to find the maximum feasible target rate.

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
