import pulp
import math

# ======================================================
# Graph structure
# ======================================================

class Graph:
    def __init__(self, V, E, c):
        self.V = set(V)
        self.E = set(frozenset(e) for e in E if len(e) == 2)
        self.c = dict(c)

    def neighbors(self, v):
        return {u for e in self.E if v in e for u in e if u != v}

    def remove_vertices(self, S):
        S = set(S)
        V_new = self.V - S
        E_new = {e for e in self.E if e.isdisjoint(S) and len(e) == 2}
        c_new = {v: self.c[v] for v in V_new}
        return Graph(V_new, E_new, c_new)


# ======================================================
# Global counters
# ======================================================

UB = math.inf
node_counter = 0
lp_counter = 0


# ======================================================
# LP relaxation (SAFE)
# ======================================================

def solve_lp(G):
    global lp_counter

    # No edges → LP value is 0
    if not G.E:
        return 0.0, {}

    lp_counter += 1

    prob = pulp.LpProblem("VC_LP", pulp.LpMinimize)
    x = {v: pulp.LpVariable(f"x_{v}", 0, 1) for v in G.V}

    prob += pulp.lpSum(G.c[v] * x[v] for v in G.V)

    for e in G.E:
        if len(e) != 2:
          continue
        u, v = tuple(e)
        prob += x[u] + x[v] >= 1

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    obj = pulp.value(prob.objective)
    if obj is None:
        return 0.0, {}

    return obj, {v: x[v].value() for v in G.V}


# ======================================================
# Strong branching (SAFE)
# ======================================================

def strong_branch_vertex(G, candidates, max_candidates=5, eps=1e-6):
    base_lp, _ = solve_lp(G)

    cand = sorted(
        candidates,
        key=lambda v: len(G.neighbors(v)),
        reverse=True
    )[:max_candidates]

    best_v = None
    best_score = -1

    for v in cand:
        # x_v = 1
        G1 = G.remove_vertices({v})
        lp1 = 0.0 if not G1.E else solve_lp(G1)[0]

        # x_v = 0
        Nv = G.neighbors(v)
        G0 = G.remove_vertices({v} | Nv)
        lp0 = 0.0 if not G0.E else solve_lp(G0)[0]

        score = max(lp1 - base_lp, lp0 - base_lp, eps)

        if score > best_score:
            best_score = score
            best_v = v

    return best_v


# ======================================================
# Branch and Bound
# ======================================================

def branch_and_bound(G, Z):
    global UB, node_counter

    node_counter += 1

    # No edges → feasible cover
    if not G.E:
        UB = min(UB, Z)
        return

    lp_val, x = solve_lp(G)
    LB = Z + lp_val

    if LB >= UB:
        return

    # Nemhauser-Trotter
    S0 = {v for v, val in x.items() if val < 1e-6}
    S1 = {v for v, val in x.items() if val > 1 - 1e-6}

    # Integral LP
    if len(S0) + len(S1) == len(G.V):
        UB = min(UB, Z + lp_val)
        return

    # Reduction
    N_S0 = set().union(*(G.neighbors(v) for v in S0)) if S0 else set()
    fixed = S1 | N_S0
    Z_new = Z + sum(G.c[v] for v in fixed)

    G_red = G.remove_vertices(S0 | S1 | N_S0)

    if not G_red.E:
        UB = min(UB, Z_new)
        return

    # Recompute LP after reduction
    lp_red, x_red = solve_lp(G_red)
    S_half = {v for v, val in x_red.items() if 1e-6 < val < 1 - 1e-6}

    if not S_half:
        UB = min(UB, Z_new + lp_red)
        return

    # Strong branching
    v = strong_branch_vertex(G_red, S_half)
    assert v in G_red.V

    # Branch 1: include v
    branch_and_bound(
        G_red.remove_vertices({v}),
        Z_new + G_red.c[v]
    )

    # Branch 2: exclude v
    Nv = G_red.neighbors(v)
    branch_and_bound(
        G_red.remove_vertices({v} | Nv),
        Z_new + sum(G_red.c[u] for u in Nv)
    )


# ======================================================
# Instance loader
# ======================================================

def load_instance(path):
    with open(path) as f:
        n, m = map(int, f.readline().split())
        weights = list(map(float, f.readline().split()))
        V = list(range(1, n + 1))
        c = {i + 1: weights[i] for i in range(n)}
        E = [tuple(map(int, line.split())) for line in f]
    return Graph(V, E, c)


# ======================================================
# Main
# ======================================================

if __name__ == "__main__":
    import sys

    G = load_instance("instances/MANN-a9.vc")
    UB = math.inf
    node_counter = 0
    lp_counter = 0

    branch_and_bound(G, 0)

    print("Optimal vertex cover cost:", UB)
    print("Branch-and-bound tree size:", node_counter)
    print("LP relaxations solved:", lp_counter)
