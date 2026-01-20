import pulp
import copy
import math

# ---------- Graph representation ----------

node_counter = 0
lp_counter = 0

class Graph:
    def __init__(self, V, E, c):
        self.V = set(V)
        self.E = set(frozenset(e) for e in E)
        self.c = dict(c)

    def neighbors(self, v):
        return {u for e in self.E for u in e if v in e and u != v}

    def remove_vertices(self, S):
        V_new = self.V - S
        E_new = {e for e in self.E if e.isdisjoint(S)}
        c_new = {v: self.c[v] for v in V_new}
        return Graph(V_new, E_new, c_new)


# ---------- LP relaxation ----------

def solve_lp(G):
    """
    Solves LP relaxation of weighted vertex cover.
    Returns (LP_value, x_dict)
    """
    prob = pulp.LpProblem("VC_LP", pulp.LpMinimize)

    x = {v: pulp.LpVariable(f"x_{v}", 0, 1) for v in G.V}

    prob += pulp.lpSum(G.c[v] * x[v] for v in G.V)


    for e in G.E:
        if len(e) != 2:
            continue
        u, v = tuple(e)
        prob += x[u] + x[v] >= 1

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    lp_val = pulp.value(prob.objective)
    x_val = {v: x[v].value() for v in G.V}

    return lp_val, x_val



# =========================
# Strong branching
# =========================

def strong_branch_vertex(G, S_half, max_candidates=5, eps=1e-6):
    """
    Partial strong branching:
    evaluates LP bound improvement for a few candidates
    """
    base_lp, _ = solve_lp(G)

    # heuristic preselection: highest degree first
    candidates = sorted(
        S_half,
        key=lambda v: len(G.neighbors(v)),
        reverse=True
    )[:max_candidates]

    best_v = None
    best_score = -1

    for v in candidates:
        # x_v = 1
        G1 = G.remove_vertices({v})
        lp1, _ = solve_lp(G1)

        # x_v = 0
        Nv = G.neighbors(v)
        G0 = G.remove_vertices({v} | Nv)
        lp0, _ = solve_lp(G0)

        score = max(lp1 - base_lp, lp0 - base_lp, eps)

        if score > best_score:
            best_score = score
            best_v = v

    return best_v


# ---------- Branch and Bound ----------

UB = math.inf

def branch_and_bound(G, Z):
    global UB, lp_counter, node_counter

    node_counter += 1  # <-- tree size counter

    if not G.E:
        UB = min(UB, Z)
        return

    lp_val, x = solve_lp(G)
    lp_counter += 1

    LB = Z + lp_val
    if LB >= UB:
        return

    S0 = {v for v, val in x.items() if val < 1e-6}
    S1 = {v for v, val in x.items() if val > 1 - 1e-6}
    S_half = G.V - S0 - S1

    if not S_half:
        UB = min(UB, Z + lp_val)
        return

    N_S0 = set().union(*(G.neighbors(v) for v in S0)) if S0 else set()
    fixed = S1 | N_S0
    Z_new = Z + sum(G.c[v] for v in fixed)

    G_red = G.remove_vertices(S0 | S1 | N_S0)

    if not G_red.V:
        UB = min(UB, Z_new)
        return

    #v = branch_and_bound(G_red, S_half)
    v = strong_branch_vertex(G_red, S_half)

    branch_and_bound(
        G_red.remove_vertices({v}),
        Z_new + G_red.c[v]
    )

    Nv = G_red.neighbors(v)
    branch_and_bound(
        G_red.remove_vertices({v} | Nv),
        Z_new + sum(G_red.c[u] for u in Nv)
    )




# ---------- Instance loader ----------

def load_instance(path):
    with open(path) as f:
        n, m = map(int, f.readline().split())
        weights = list(map(float, f.readline().split()))
        V = list(range(1, n + 1))
        c = {i + 1: weights[i] for i in range(n)}
        E = [tuple(map(int, line.split())) for line in f]
    return Graph(V, E, c)


G = load_instance("/Users/quanlamnhat/Documents/code/code_sample/discrete-optimization-project/instances/mk11-b2.vc")
UB = math.inf
branch_and_bound(G, 0)
print("Optimal vertex cover cost:", UB)
print("Number of nodes:", node_counter)
print("Number of LPs solved:", lp_counter)
