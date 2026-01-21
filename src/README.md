# Vertex Cover Solver

Branch and bound solver for the minimum vertex cover problem with multiple branching strategies.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Arguments:

- `--all` : Run all instances in the `instances/` folder
- `--instance [path]` : Run a specific instance file
- `--strategy [1-3]` : Select branching strategy (optional, defaults to all strategies)
  - `1` : Include max degree vertex first
  - `2` : Exclude max degree vertex first
  - `3` : Full strong branching (default)
- `--out [path]` : Output CSV file path (default: `solutions.csv`)

## Branching Strategies

1. **Include Max Degree**: Selects the vertex with maximum degree and branches by including it first
2. **Exclude Max Degree**: Selects the vertex with maximum degree and branches by excluding it first
3. **Full Strong Branching**: Evaluates all candidates by solving LP relaxations and selects the vertex with the best score

## Output Format

Results are saved to a CSV file with the following columns:

- `instance` : Instance filename
- `|V|` : Number of vertices
- `|E|` : Number of edges
- `strategy` : Strategy name used
- `opt_VC` : Optimal vertex cover size found
- `BnB_nodes` : Number of branch-and-bound nodes explored
- `LP_calls` : Number of LP relaxations solved
- `runtime_sec` : Runtime in seconds

## Examples

```bash
# Quick test on one instance
python main.py --instance instances/MANN-a9.vc --strategy 3

# Full benchmark with all strategies
python main.py --all --out full_benchmark.csv

# Compare strategy 1 vs strategy 3
python main.py --all --strategy 1 --out strategy1.csv
python main.py --all --strategy 3 --out strategy3.csv
```

## Customizations

The solver is encapsulated in branch_and_bound function. You can implement your custom strategy as follows

```python
def custom_strategy(G:graph):
  # Your implementation


  return (v, included) # if included is True, execute the branch where v is included first.
```
