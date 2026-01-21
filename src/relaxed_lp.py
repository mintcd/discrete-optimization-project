import pulp

def solve_lp(G):
    """
    Solve the LP relaxation of the vertex cover problem on graph G.

    Args:
        G (Graph)

    Returns:
        tuple: A tuple (obj_value, solution) where:
            - obj_value (float): Optimal objective value of the LP
            - solution (dict): Dictionary mapping vertex -> LP value (0-1)

    Notes:
        Returns (0.0, {}) if the graph has no edges.
    """
    if not G.E:
        return 0.0, {}

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