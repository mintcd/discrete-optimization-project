import networkx as nx
import pulp
import time

# ------------------------------------------------------------
# Parse .vc file
# ------------------------------------------------------------
def parse_vc(path):
    with open(path) as f:
        n, m = map(int, f.readline().split())
        _ = f.readline()  # skip vertex weights
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
# Branch and Bound Algorithm
# ------------------------------------------------------------
def vertex_cover_bnb(G, cutoff=60):
    start = time.time()

    UB = G.number_of_nodes()
    lp_calls = 0
    bnb_nodes = 0   # <-- size of BnB tree

    def recurse(G, Z):
        nonlocal UB, lp_calls, bnb_nodes
        bnb_nodes += 1   # count this node in BnB tree

        # cutoff
        if time.time() - start > cutoff:
            return

        # feasible solution
        if G.number_of_edges() == 0:
            UB = min(UB, Z)
            return

        # LP relaxation
        x, lp_val = solve_lp(G)
        lp_calls += 1

        LB = Z + lp_val
        if LB >= UB:
            return

        # integral LP solution
        fractional = [v for v in x if x[v] not in (0, 1)]
        if not fractional:
            UB = min(UB, Z + int(lp_val))
            return

        # Nemhauser–Trotter Theorem
        S1 = {v for v in x if x[v] == 1}
        S0 = {v for v in x if x[v] == 0}

        Gp = G.copy()
        Zp = Z

        for v in S1:
            if v in Gp:
                Gp.remove_node(v)
                Zp += 1

        for v in S0:
            if v in Gp:
                nbrs = list(Gp.neighbors(v))
                Gp.remove_node(v)
                for u in nbrs:
                    if u in Gp:
                        Gp.remove_node(u)
                        Zp += 1

        # branch on fractional variable
        v = fractional[0]

        # Branch 1: include v
        G1 = Gp.copy()
        if v in G1:
            G1.remove_node(v)
        recurse(G1, Zp + 1)

        # Branch 2: exclude v (include neighbors)
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
# Main
# ------------------------------------------------------------
if __name__ == "__main__":
    path = "/Users/quanlamnhat/Documents/code/code_sample/discrete-optimization-project/instances/MANN-a9.vc"   # <-- change the file direction here
    cutoff = 60

    G = parse_vc(path)
    print("Vertices:", G.number_of_nodes())
    print("Edges:", G.number_of_edges())

    opt, lp_calls, bnb_nodes, runtime = vertex_cover_bnb(G, cutoff)

    print("\n===== RESULT =====")
    print("Optimal Vertex Cover Size:", opt)
    print("LP relaxations solved:", lp_calls)
    print("BnB tree size:", bnb_nodes)
    print("Runtime (s):", round(runtime, 2))
