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
    while bfs(graph, source, sink, parent):
        path_flow = float('Inf')
        s = sink
        while s != source:
            path_flow = min(path_flow, graph[parent[s]][s])
            s = parent[s]
        v = sink
        while v != source:
            u = parent[v]
            graph[u][v] -= path_flow
            if v not in graph:
                graph[v] = {}
            if u not in graph[v]:
                graph[v][u] = 0
            graph[v][u] += path_flow
            v = parent[v]
        max_flow += path_flow
    return max_flow, graph

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
    super_source = "super_source"
    super_sink = "super_sink"
    graph[super_source] = {}
    graph[super_sink] = {}

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

    flow, _ = edmonds_karp(demand_graph, s_star, t_star)

    if abs(flow - total_demand) > 1e-9:
        return {"status": "infeasible"}

    # Main flow
    main_graph = {node: dict(adj) for node, adj in graph.items()}
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