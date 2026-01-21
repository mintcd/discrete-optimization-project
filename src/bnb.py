import math
import time
from relaxed_lp import solve_lp

""" Strategies for branch and bound: 
    1) Choosing the next vertex
    2) Choose to include or exclude it.

    Return: (v, included, lp_count)
        - v: vertex to branch on
        - included: 1 to include first, 0 to exclude first
        - lp_count: number of LPs solved during strategy
"""

def include_max_degree_vertex(G):
    v = max(G.V, key=lambda u: len(G.neighbors(u)))
    return v, 1, 0  # (vertex, included, lp_count)

def exclude_min_degree_vertex(G):
    v = min(G.V, key=lambda u: len(G.neighbors(u)))
    return v, 0, 0  # (vertex, included, lp_count)

def strong_branch_vc(G, eps=1e-9, max_candidates=None):
    lp_count = 0

    z_base, x = solve_lp(G)
    lp_count += 1

    frac = [v for v in G.V if eps < x[v] < 1 - eps]
    if not frac:
        return None, None, lp_count  # already integral at this node

    # optional restriction
    candidates = frac
    if max_candidates is not None and len(candidates) > max_candidates:
        candidates = sorted(candidates, key=lambda v: len(G.neighbors(v)), reverse=True)[:max_candidates]

    best_v = None
    best_score = -1
    best_first_branch = None

    for v in candidates:
        # x_v = 1
        G1 = G.remove_vertices({v})
        z1 = 1 + (0.0 if not G1.E else solve_lp(G1)[0]); lp_count += (1 if G1.E else 0)

        # x_v = 0 => force N(v) in cover
        Nv = G.neighbors(v)
        G0 = G.remove_vertices({v} | Nv)
        z0 = len(Nv) + (0.0 if not G0.E else solve_lp(G0)[0]); lp_count += (1 if G0.E else 0)

        d1 = z1 - z_base
        d0 = z0 - z_base
        score = min(d0, d1)  # robust strong-branching score

        if score > best_score:
            best_score = score
            best_v = v
            best_first_branch = 1 if z1 <= z0 else 0  # explore smaller bound first

    return best_v, best_first_branch, lp_count

""" Branch-and-bound algorithm """
def branch_and_bound(G, Z=0, strategy=include_max_degree_vertex, UB=math.inf, node_count=0, lp_count=0, timeout=None, start_time=None):
    """
    Solve the minimum weighted vertex cover problem using branch-and-bound with strong branching.
    
    Uses LP relaxation for bounds, graph reduction techniques, and strong branching for 
    intelligent vertex selection. The algorithm recursively explores the search tree, 
    pruning branches when the lower bound exceeds the current upper bound.
    
    Args:
        G: A Graph object with vertices V, edges E, neighbors method, remove_vertices method,
           and vertex costs c (dict mapping vertex -> cost).
        Z: Current cost of included vertices.
        UB: Upper bound (best solution cost found so far).
        node_count: Number of branch-and-bound nodes explored.
        lp_count: Number of LP relaxations solved.
        timeout: Maximum runtime in seconds (None for no timeout).
        start_time: Time when algorithm started (for timeout checking).
    
    Returns:
        tuple: (Z, UB, node_count, lp_count, timed_out)
    """
    
    # Initialize start_time on first call
    if start_time is None:
        start_time = time.time()
    
    # Check timeout
    if timeout is not None and (time.time() - start_time) > timeout:
        return Z, UB, node_count, lp_count, True
    
    node_count += 1
    
    # Base case: no edges
    if not G.E:
        UB = min(UB, Z)
        return Z, UB, node_count, lp_count, False

    # Solve LP relaxation
    lp_val, x = solve_lp(G)
    lp_count += 1
    LB = Z + lp_val

    if LB >= UB:
        return Z, UB, node_count, lp_count, False

    # Take the integral variables
    S0 = {v for v, val in x.items() if val < 1e-6}
    S1 = {v for v, val in x.items() if val > 1 - 1e-6}

    # If all variables are integral, update UB and return
    if len(S0) + len(S1) == len(G.V):
        UB = min(UB, Z + lp_val)
        return Z, UB, node_count, lp_count, False
    
    G_red = G.remove_vertices(S0 | S1)
    Z_new = Z + sum(G.c[v] for v in S1)

    # Choose a vertex to branch on
    v, included, strategy_lp_count = strategy(G_red)
    lp_count += strategy_lp_count

    # Include first
    if included == 1:
        # Branch 1: include v
        _, UB, node_count, lp_count, timed_out = branch_and_bound(
            G_red.remove_vertices({v}),
            Z_new + G_red.c[v],
            strategy,
            UB,
            node_count,
            lp_count,
            timeout,
            start_time
        )
        if timed_out:
            return Z, UB, node_count, lp_count, True
        
        # Branch 2: exclude v
        Nv = G_red.neighbors(v)
        _, UB, node_count, lp_count, timed_out = branch_and_bound(
            G_red.remove_vertices({v} | Nv),
            Z_new + sum(G_red.c[u] for u in Nv),
            strategy,
            UB,
            node_count,
            lp_count,
            timeout,
            start_time
        )
        if timed_out:
            return Z, UB, node_count, lp_count, True
        
        return Z, UB, node_count, lp_count, False
    

    # Exclude first
    Nv = G_red.neighbors(v)
    _, UB, node_count, lp_count, timed_out = branch_and_bound(
        G_red.remove_vertices({v} | Nv),
        Z_new + sum(G_red.c[u] for u in Nv),
        strategy,
        UB,
        node_count,
        lp_count,
        timeout,
        start_time
    )
    if timed_out:
        return Z, UB, node_count, lp_count, True

    _, UB, node_count, lp_count, timed_out = branch_and_bound(
        G_red.remove_vertices({v}),
        Z_new + G_red.c[v],
        strategy,
        UB,
        node_count,
        lp_count,
        timeout,
        start_time
    )
    if timed_out:
        return Z, UB, node_count, lp_count, True
    
    return Z, UB, node_count, lp_count, False
