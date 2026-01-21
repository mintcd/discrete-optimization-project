import argparse
import os
import csv
import time
from bnb import (
    branch_and_bound,
    include_max_degree_vertex,
    exclude_min_degree_vertex,
    strong_branch_vc
)
from processing import load_instance


def get_strategy(strategy_num):
    """Map strategy number to strategy function."""
    strategies = {
        1: include_max_degree_vertex,
        2: exclude_min_degree_vertex,
        3: strong_branch_vc
    }
    return strategies.get(strategy_num)


def get_strategy_name(strategy_num):
    """Get the name of the strategy."""
    names = {
        1: "include_max_degree",
        2: "exclude_min_degree",
        3: "strong_branch_vc"
    }
    return names.get(strategy_num, f"strategy_{strategy_num}")


def run_instance(instance_path, strategy_num, strategy_func, timeout=None):
    """Run a single instance with a given strategy."""
    G = load_instance(instance_path)
    
    start_time = time.time()
    Z, UB, node_counter, lp_counter, timed_out = branch_and_bound(G, strategy=strategy_func, timeout=timeout)
    runtime = time.time() - start_time
    
    instance_name = os.path.basename(instance_path)
    strategy_name = get_strategy_name(strategy_num)
    
    return {
        "instance": instance_name,
        "|V|": len(G.V),
        "|E|": len(G.E),
        "strategy": strategy_name,
        "opt_VC": UB if not timed_out else f"{UB}*",
        "BnB_nodes": node_counter,
        "LP_calls": lp_counter,
        "runtime_sec": round(runtime, 2),
        "timed_out": timed_out
    }


def run_single_instance(instance_path, strategy, output_file, timeout=None):
    """Run a single instance with the specified strategy."""
    results = []
    
    if not os.path.exists(instance_path):
        print(f"Error: Instance file not found: {instance_path}")
        return
    
    instance_name = os.path.basename(instance_path)
    strategy_func = get_strategy(strategy)
    strategy_name = get_strategy_name(strategy)
    
    print(f"Running instance: {instance_name}")
    print(f"With strategy: {strategy_name}")
    print("-" * 60)
        
    try:
        result = run_instance(instance_path, strategy, strategy_func, timeout)
        results.append(result)
        status = "TIMEOUT" if result['timed_out'] else "✓"
        print(f"{status} (opt={result['opt_VC']}, time={result['runtime_sec']}s)")
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # Write results to CSV
    if results:
        write_results(results, output_file)
        print(f"\nResults written to {output_file}")
    else:
        print("\nNo results to write.")


def write_results(results, output_file):
    """Write results to CSV file."""
    with open(output_file, "w", newline="") as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)


def main():
    parser = argparse.ArgumentParser(
        description="Run branch and bound vertex cover solver",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single instance with default strategy (1)
  python main.py --instance instances/MANN-a9.vc
  
  # Run single instance with specific strategy
  python main.py --instance instances/MANN-a9.vc --strategy 3
  
  # Run single instance with specific strategy and output file
  python main.py --instance instances/MANN-a9.vc --strategy 1 --out my_results.csv
        """
    )
    
    # Instance selection
    parser.add_argument(
        "--instance",
        type=str,
        required=True,
        help="Path to a specific instance file"
    )
    
    # Strategy selection
    parser.add_argument(
        "--strategy",
        type=int,
        choices=[1, 2, 3],
        default=1,
        help="Strategy to use (1: include_max_degree, 2: exclude_min_degree, 3: strong_branch_vc). Default: 1"
    )
    
    # Output file
    parser.add_argument(
        "--out",
        type=str,
        default="solutions.csv",
        help="Path to output CSV file (default: solutions.csv)"
    )
    
    # Timeout
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Maximum runtime in seconds for each instance (default: no timeout)"
    )
    
    args = parser.parse_args()
    
    # Run the instance with the specified strategy (defaults to 1)
    run_single_instance(args.instance, args.strategy, args.out, args.timeout)


if __name__ == "__main__":
    main()
