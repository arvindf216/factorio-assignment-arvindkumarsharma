import sys
import json
from collections import deque

def main():
    try:
        input_data = json.load(sys.stdin)
        output_data = process_belts(input_data)
        json.dump(output_data, sys.stdout, indent=2)
    except Exception as e:
        json.dump({"status": "error", "message": str(e)}, sys.stdout, indent=2)

def bfs(graph, s, t, parent):
    visited = {node: False for node in graph}
    queue = deque()
    queue.append(s)
    visited[s] = True
    parent[s] = -1
    while queue:
        u = queue.popleft()
        if u not in graph:
            continue
        for v, capacity in graph[u].items():
            if v in visited and not visited[v] and capacity > 0:
                queue.append(v)
                visited[v] = True
                parent[v] = u
    return True if t in visited and visited[t] else False

def edmonds_karp(graph, source, sink):
    parent = {}
    max_flow = 0
    residual_graph = {u: dict(v) for u, v in graph.items()}
    while bfs(residual_graph, source, sink, parent):
        path_flow = float('Inf')
        s = sink
        while s != source:
            path_flow = min(path_flow, residual_graph[parent[s]][s])
            s = parent[s]
        v = sink
        while v != source:
            u = parent[v]
            residual_graph[u][v] -= path_flow
            if v not in residual_graph:
                residual_graph[v] = {}
            if u not in residual_graph[v]:
                residual_graph[v][u] = 0
            residual_graph[v][u] += path_flow
            v = parent[v]
        max_flow += path_flow
    return max_flow, residual_graph

def process_belts(data):
    edges = data.get('edges', [])
    node_caps = data.get('node_caps', {})
    sources = data.get('sources', {})
    sink_node = data.get('sink', {})

    nodes = set(sources.keys()) | {sink_node}
    for edge in edges:
        nodes.add(edge['from'])
        nodes.add(edge['to'])
    
    graph = {node: {} for node in nodes}
    balance = {node: 0 for node in nodes}

    for edge in edges:
        u, v, lo, hi = edge['from'], edge['to'], edge.get('lo', 0), edge.get('hi', float('inf'))
        if v not in graph[u]:
            graph[u][v] = 0
        graph[u][v] = hi - lo
        balance[u] -= lo
        balance[v] += lo

    for source, supply in sources.items():
        balance[source] += supply
    balance[sink_node] -= sum(sources.values())

    demand_graph = {node: dict(adj) for node, adj in graph.items()}
    s_star, t_star = "s*", "t*"
    demand_graph[s_star] = {}
    demand_graph[t_star] = {}
    total_demand = 0

    for node, b in balance.items():
        if b > 0:
            demand_graph[s_star][node] = b
            total_demand += b
        elif b < 0:
            demand_graph[node][t_star] = -b

    flow, residual_graph = edmonds_karp(demand_graph, s_star, t_star)

    if abs(flow - total_demand) > 1e-9:
        q = deque([s_star])
        reachable_nodes = {s_star}
        while q:
            u = q.popleft()
            for v, capacity in residual_graph.get(u, {}).items():
                if capacity > 0 and v not in reachable_nodes:
                    reachable_nodes.add(v)
                    q.append(v)

        cut_reachable = sorted(list(set(n.replace('_in', '').replace('_out', '') for n in reachable_nodes if n not in [s_star, t_star])))
        demand_balance = total_demand - flow

        tight_edges = []
        for edge in edges:
            u, v = edge['from'], edge['to']
            u_rep = f"{u}_out" if f"{u}_out" in nodes else u
            v_rep = f"{v}_in" if f"{v}_in" in nodes else v
            if u_rep in reachable_nodes and v_rep not in reachable_nodes:
                tight_edges.append({"from": u, "to": v, "flow_needed": demand_balance})

        tight_nodes = []
        for node in cut_reachable:
            is_tight = True
            if node in sources or node == sink_node:
                continue
            
            # Check if all outgoing edges to unreachable nodes are saturated
            for edge in edges:
                if edge['from'] == node:
                    u_rep = f"{node}_out" if f"{node}_out" in nodes else node
                    v_rep = f"{edge['to']}_in" if f"{edge['to']}_in" in nodes else edge['to']
                    if u_rep in reachable_nodes and v_rep not in reachable_nodes:
                        if residual_graph.get(u_rep, {}).get(v_rep, 0) > 0:
                            is_tight = False
                            break
            if is_tight:
                tight_nodes.append(node)

        # Add nodes with explicit capacity limits that are tight
        for node in node_caps:
            if f'{node}_in' in reachable_nodes and f'{node}_out' not in reachable_nodes:
                if node not in tight_nodes:
                    tight_nodes.append(node)

        return {
            "status": "infeasible",
            "cut_reachable": cut_reachable,
            "deficit": {
                "demand_balance": demand_balance,
                "tight_nodes": sorted(tight_nodes),
                "tight_edges": tight_edges
            }
        }

    # Main flow
    main_graph = {node: dict(adj) for node, adj in graph.items()}
    super_source = "super_source"
    super_sink = "super_sink"
    main_graph[super_source] = {}
    main_graph[super_sink] = {}
    for source in sources:
        main_graph[super_source][source] = float('inf')
    main_graph[sink_node][super_sink] = float('inf')

    max_flow, residual_graph = edmonds_karp(main_graph, super_source, super_sink)

    final_flows = []
    for edge in edges:
        u, v, lo = edge['from'], edge['to'], edge.get('lo', 0)
        capacity = edge.get('hi', float('inf')) - lo
        flow_val = capacity - residual_graph.get(u, {}).get(v, 0)
        final_flows.append({"from": u, "to": v, "flow": flow_val + lo})

    return {
        "status": "ok",
        "max_flow_per_min": sum(f['flow'] for f in final_flows if f['to'] == sink_node),
        "flows": final_flows
    }

if __name__ == "__main__":
    main()