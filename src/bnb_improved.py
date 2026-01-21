import os
import csv
import networkx as nx
import pulp
import time

# ------------------------------------------------------------
# Parse .vc file
# ------------------------------------------------------------
def parse_vc(path):
    with open(path) as f:
        n, m = map(int, f.readline().split())
        _ = f.readline()  # skip weights
        edges = [tuple(map(int, line.split())) for line in f]

    G = nx.Graph()
    G.add_nodes_from(range(1, n + 1))
    G.add_edges_from(edges)
    return G

# ------------------------------------------------------------
# LP relaxation
# ------------------------------------------------------------
def solve_lp(G):
    prob = pulp.LpProblem("MVC_LP", pulp.LpMinimize)

    x = {v: pulp.LpVariable(f"x_{v}", 0, 1) for v in G.nodes()}
    prob += pulp.lpSum(x[v] for v in G.nodes())

    for u, v in G.edges():
        prob += x[u] + x[v] >= 1

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    return {v: x[v].value() for v in G.nodes()}, pulp.value(prob.objective)

# ------------------------------------------------------------
# Branch and Bound
# ------------------------------------------------------------
def vertex_cover_bnb(G, cutoff=60):
    start = time.time()

    UB = G.number_of_nodes()
    lp_calls = 0
    bnb_nodes = 0

    def recurse(G, Z):
        nonlocal UB, lp_calls, bnb_nodes
        bnb_nodes += 1

        if time.time() - start > cutoff:
            return

        if G.number_of_edges() == 0:
            UB = min(UB, Z)
            return

        x, lp_val = solve_lp(G)
        lp_calls += 1

        if Z + lp_val >= UB:
            return

        fractional = [v for v in x if x[v] not in (0, 1)]
        if not fractional:
            UB = min(UB, Z + int(lp_val))
            return

        S1 = {v for v in x if x[v] == 1}
        S0 = {v for v in x if x[v] == 0}

        Gp = G.copy()
        Zp = Z

        # S1
        for v in S1:
            if v in Gp:
                Gp.remove_node(v)
                Zp += 1

        # S0 (simple version - giữ nguyên code của bạn)
        for v in S0:
            if v in Gp:
                nbrs = list(Gp.neighbors(v))
                Gp.remove_node(v)
                for u in nbrs:
                    if u in Gp:
                        Gp.remove_node(u)
                        Zp += 1

        # branch
        v = fractional[0]

        G1 = Gp.copy()
        if v in G1:
            G1.remove_node(v)
        recurse(G1, Zp + 1)

        G2 = Gp.copy()
        if v in G2:
            nbrs = list(G2.neighbors(v))
            G2.remove_node(v)
            for u in nbrs:
                if u in G2:
                    G2.remove_node(u)
            recurse(G2, Zp + len(nbrs))

    recurse(G.copy(), 0)
    return UB, lp_calls, bnb_nodes, time.time() - start

# ------------------------------------------------------------
# Run all instances
# ------------------------------------------------------------
def run_all_instances(instance_dir, output_file, cutoff=60):
    results = []

    for filename in sorted(os.listdir(instance_dir)):
        if not filename.endswith(".vc"):
            continue

        path = os.path.join(instance_dir, filename)
        print(f"Running {filename}...")

        G = parse_vc(path)

        opt, lp_calls, bnb_nodes, runtime = vertex_cover_bnb(G, cutoff)

        results.append([
            filename,
            G.number_of_nodes(),
            G.number_of_edges(),
            opt,
            lp_calls,
            bnb_nodes,
            round(runtime, 2)
        ])

    # write CSV
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "instance",
            "|V|",
            "|E|",
            "opt_VC",
            "LP_calls",
            "BnB_nodes",
            "runtime_sec"
        ])
        writer.writerows(results)

    print(f"\nResults written to {output_file}")

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
if __name__ == "__main__":
    INSTANCE_DIR = "instances"     # folder of the .vc input
    OUTPUT_FILE = "results.csv"
    CUTOFF = 60

    run_all_instances(INSTANCE_DIR, OUTPUT_FILE, CUTOFF)
