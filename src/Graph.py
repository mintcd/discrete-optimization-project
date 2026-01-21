class Graph:
    def __init__(self, V, E, c):
        self.V = set(V)
        self.E = set(frozenset(e) for e in E if len(e) == 2)
        self.c = dict(c)

    def neighbors(self, v):
        return {u for e in self.E if v in e for u in e if u != v}

    def remove_vertices(self, S):
        """ Remove vertices in S from the graph and return the new graph."""
        S = set(S)
        V_new = self.V - S
        E_new = {e for e in self.E if e.isdisjoint(S) and len(e) == 2}
        c_new = {v: self.c[v] for v in V_new}
        return Graph(V_new, E_new, c_new)