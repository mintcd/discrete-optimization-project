from Graph import Graph

def load_instance(path):
    with open(path) as f:
        n, m = map(int, f.readline().split())
        weights = list(map(float, f.readline().split()))
        V = list(range(1, n + 1))
        c = {i + 1: weights[i] for i in range(n)}
        E = [tuple(map(int, line.split())) for line in f]
    return Graph(V, E, c)