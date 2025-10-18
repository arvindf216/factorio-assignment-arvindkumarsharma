
import sys
import json
from scipy.optimize import linprog
import numpy as np

def main():
    try:
        input_data = json.load(sys.stdin)
        output_data = process_factory(input_data)
        json.dump(output_data, sys.stdout, indent=2)
    except Exception as e:
        json.dump({"status": "error", "message": str(e)}, sys.stdout, indent=2)

def process_factory(data):
    target_rate = data.get("target", {}).get("rate_per_min", 0)
    
    c, A_eq, b_eq_template, A_ub, b_ub, recipe_to_idx, all_items, raw_items, eff_crafts_per_min, machines, item_to_idx, intermediate_items, A_raw = get_lp_matrices(data)

    def solve_lp(rate):
        b_eq = np.copy(b_eq_template)
        target_item = data.get("target", {}).get("item")
        if target_item:
            b_eq[-1] = rate
        return linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')

    res = solve_lp(target_rate)

    if res.success:
        return format_success_output(res, data, recipe_to_idx, all_items, raw_items, eff_crafts_per_min, machines, A_raw, item_to_idx)
    else:
        low = 0
        high = target_rate
        best_rate = 0

        for _ in range(100):
            mid = (low + high) / 2
            if high - low < 1e-9:
                break
            res_test = solve_lp(mid)
            if res_test.success:
                best_rate = mid
                low = mid
            else:
                high = mid
        
        bottleneck_hint = []
        if best_rate > 0:
            res_final = solve_lp(best_rate)
            if res_final.success:
                slacks = res_final.slack
                
                sorted_raw_items = sorted(list(raw_items))
                for i in range(len(raw_items)):
                    if abs(slacks[i]) < 1e-6:
                        item_name = sorted_raw_items[i]
                        bottleneck_hint.append(f"{item_name} supply")

                sorted_machine_types = sorted(machines.keys())
                num_raw_constraints = len(raw_items)
                for i in range(len(machines)):
                    constraint_index = num_raw_constraints + i
                    if abs(slacks[constraint_index]) < 1e-6:
                        machine_name = sorted_machine_types[i]
                        bottleneck_hint.append(f"{machine_name} cap")

        return {
            "status": "infeasible",
            "max_feasible_target_per_min": best_rate,
            "bottleneck_hint": sorted(bottleneck_hint)
        }

def get_lp_matrices(data):
    machines = data.get("machines", {})
    recipes = data.get("recipes", {})
    modules = data.get("modules", {})
    limits = data.get("limits", {})
    target = data.get("target", {})

    all_items_set = set()
    for recipe_name, recipe_data in recipes.items():
        for item in recipe_data.get("in", {}):
            all_items_set.add(item)
        for item in recipe_data.get("out", {}):
            all_items_set.add(item)
    all_items = sorted(list(all_items_set))

    raw_items = set(limits.get("raw_supply_per_min", {}).keys())
    intermediate_items = sorted(list(all_items_set - raw_items - {target.get("item")}))
    item_to_idx = {item: i for i, item in enumerate(all_items)}
    num_recipes = len(recipes)
    recipe_to_idx = {recipe: i for i, recipe in enumerate(recipes.keys())}

    eff_crafts_per_min = {}
    for recipe_name, recipe_data in recipes.items():
        machine_type = recipe_data["machine"]
        base_speed = machines[machine_type]["crafts_per_min"]
        time_s = recipe_data["time_s"]
        speed_mod = 1 + modules.get(machine_type, {}).get("speed", 0)
        eff_crafts_per_min[recipe_name] = base_speed * speed_mod * 60 / time_s

    c = np.zeros(num_recipes)
    for recipe_name, recipe_idx in recipe_to_idx.items():
        c[recipe_idx] = 1 / eff_crafts_per_min[recipe_name]

    A_eq = np.zeros((len(intermediate_items) + 1, num_recipes))
    b_eq = np.zeros(len(intermediate_items) + 1)

    for i, item in enumerate(intermediate_items):
        for recipe_name, recipe_idx in recipe_to_idx.items():
            recipe_data = recipes[recipe_name]
            prod_mod = 1 + modules.get(recipe_data["machine"], {}).get("prod", 0)
            if item in recipe_data.get("out", {}):
                A_eq[i, recipe_idx] += recipe_data["out"].get(item, 0) * prod_mod
            if item in recipe_data.get("in", {}):
                A_eq[i, recipe_idx] -= recipe_data["in"].get(item, 0)

    target_item = target.get("item")
    if target_item:
        for recipe_name, recipe_idx in recipe_to_idx.items():
            recipe_data = recipes[recipe_name]
            prod_mod = 1 + modules.get(recipe_data["machine"], {}).get("prod", 0)
            if target_item in recipe_data.get("out", {}):
                A_eq[-1, recipe_idx] += recipe_data["out"].get(target_item, 0) * prod_mod
            if target_item in recipe_data.get("in", {}):
                A_eq[-1, recipe_idx] -= recipe_data["in"].get(target_item, 0)

    num_machine_types = len(machines)
    A_raw = np.zeros((len(raw_items), num_recipes))
    b_raw = np.zeros(len(raw_items))
    for i, item in enumerate(sorted(list(raw_items))):
        for recipe_name, recipe_idx in recipe_to_idx.items():
            recipe_data = recipes[recipe_name]
            if item in recipe_data.get("in", {}):
                A_raw[i, recipe_idx] += recipe_data["in"].get(item, 0)
        b_raw[i] = limits.get("raw_supply_per_min", {}).get(item, 0)

    A_machine = np.zeros((num_machine_types, num_recipes))
    b_machine = np.zeros(num_machine_types)
    machine_type_to_idx = {mtype: i for i, mtype in enumerate(machines.keys())}
    for mtype, m_idx in machine_type_to_idx.items():
        for recipe_name, r_idx in recipe_to_idx.items():
            if recipes[recipe_name]["machine"] == mtype:
                A_machine[m_idx, r_idx] = 1 / eff_crafts_per_min[recipe_name]
        b_machine[m_idx] = limits.get("max_machines", {}).get(mtype, 1e9)

    A_ub = np.vstack([A_raw, A_machine])
    b_ub = np.concatenate([b_raw, b_machine])
    
    return c, A_eq, b_eq, A_ub, b_ub, recipe_to_idx, all_items, raw_items, eff_crafts_per_min, machines, item_to_idx, intermediate_items, A_raw

def format_success_output(res, data, recipe_to_idx, all_items, raw_items, eff_crafts_per_min, machines, A_raw, item_to_idx):
    per_recipe_crafts_per_min = {recipe: res.x[idx] for recipe, idx in recipe_to_idx.items()}
    per_machine_counts = {}
    for mtype in machines:
        count = 0
        for r_name, r_idx in recipe_to_idx.items():
            if data["recipes"][r_name]["machine"] == mtype:
                count += res.x[r_idx] / eff_crafts_per_min[r_name]
        per_machine_counts[mtype] = count

    raw_consumption_per_min = {}
    for i, item in enumerate(sorted(list(raw_items))):
        consumption = np.dot(A_raw[i, :], res.x)
        raw_consumption_per_min[item] = consumption

    return {
        "status": "ok",
        "per_recipe_crafts_per_min": per_recipe_crafts_per_min,
        "per_machine_counts": per_machine_counts,
        "raw_consumption_per_min": raw_consumption_per_min
    }

if __name__ == "__main__":
    main()
