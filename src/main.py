import argparse
import os
import csv
import time
from bnb import (
    branch_and_bound,
    include_max_degree_vertex,
    exclude_min_degree_vertex,
    full_strong
)
from processing import load_instance


def get_strategy(strategy_num):
    """Map strategy number to strategy function."""
    strategies = {
        1: include_max_degree_vertex,
        2: exclude_min_degree_vertex,
        3: full_strong
    }
    return strategies.get(strategy_num)


def get_strategy_name(strategy_num):
    """Get the name of the strategy."""
    names = {
        1: "include_max_degree",
        2: "exclude_min_degree",
        3: "full_strong"
    }
    return names.get(strategy_num, f"strategy_{strategy_num}")


def run_instance(instance_path, strategy_num, strategy_func):
    """Run a single instance with a given strategy."""
    G = load_instance(instance_path)
    
    start_time = time.time()
    Z, UB, node_counter, lp_counter = branch_and_bound(G, strategy=strategy_func)
    runtime = time.time() - start_time
    
    instance_name = os.path.basename(instance_path)
    strategy_name = get_strategy_name(strategy_num)
    
    return {
        "instance": instance_name,
        "|V|": len(G.V),
        "|E|": len(G.E),
        "strategy": strategy_name,
        "opt_VC": UB,
        "BnB_nodes": node_counter,
        "LP_calls": lp_counter,
        "runtime_sec": round(runtime, 2)
    }


def run_all_instances(instances_dir, strategies, output_file):
    """Run all instances in the directory with all specified strategies."""
    results = []
    
    # Get all .vc files in the directory
    instance_files = sorted([
        os.path.join(instances_dir, f)
        for f in os.listdir(instances_dir)
        if f.endswith(".vc")
    ])
    
    if not instance_files:
        print(f"No .vc files found in {instances_dir}")
        return
    
    print(f"Found {len(instance_files)} instances")
    print(f"Running with {len(strategies)} strategy/strategies")
    print("-" * 60)
    
    for instance_path in instance_files:
        instance_name = os.path.basename(instance_path)
        
        for strategy_num in strategies:
            strategy_func = get_strategy(strategy_num)
            strategy_name = get_strategy_name(strategy_num)
            
            print(f"Running {instance_name} with {strategy_name}...", end=" ")
            
            try:
                result = run_instance(instance_path, strategy_num, strategy_func)
                results.append(result)
                print(f"✓ (opt={result['opt_VC']}, time={result['runtime_sec']}s)")
            except Exception as e:
                print(f"✗ Error: {e}")
                continue
    
    # Write results to CSV
    if results:
        write_results(results, output_file)
        print(f"\nResults written to {output_file}")
    else:
        print("\nNo results to write.")


def run_single_instance(instance_path, strategies, output_file):
    """Run a single instance with all specified strategies."""
    results = []
    
    if not os.path.exists(instance_path):
        print(f"Error: Instance file not found: {instance_path}")
        return
    
    instance_name = os.path.basename(instance_path)
    print(f"Running instance: {instance_name}")
    print(f"With {len(strategies)} strategy/strategies")
    print("-" * 60)
    
    for strategy_num in strategies:
        strategy_func = get_strategy(strategy_num)
        strategy_name = get_strategy_name(strategy_num)
        
        print(f"Running with {strategy_name}...", end=" ")
        
        try:
            result = run_instance(instance_path, strategy_num, strategy_func)
            results.append(result)
            print(f"✓ (opt={result['opt_VC']}, time={result['runtime_sec']}s)")
        except Exception as e:
            print(f"✗ Error: {e}")
            continue
    
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
  # Run all instances with all strategies
  python main.py --all
  
  # Run all instances with strategy 3 only
  python main.py --all --strategy 3
  
  # Run single instance with all strategies
  python main.py --instance instances/MANN-a9.vc
  
  # Run single instance with specific strategy and output file
  python main.py --instance instances/MANN-a9.vc --strategy 1 --out my_results.csv
        """
    )
    
    # Instance selection (mutually exclusive)
    instance_group = parser.add_mutually_exclusive_group(required=True)
    instance_group.add_argument(
        "--all",
        action="store_true",
        help="Run all instances in the instances folder"
    )
    instance_group.add_argument(
        "--instance",
        type=str,
        help="Path to a specific instance file"
    )
    
    # Strategy selection
    parser.add_argument(
        "--strategy",
        type=int,
        choices=[1, 2, 3],
        help="Strategy to use (1: include_max_degree, 2: exclude_min_degree, 3: full_strong). If not specified, runs all strategies."
    )
    
    # Output file
    parser.add_argument(
        "--out",
        type=str,
        default="solutions.csv",
        help="Path to output CSV file (default: solutions.csv)"
    )
    
    args = parser.parse_args()
    
    # Determine which strategies to run
    if args.strategy:
        strategies = [args.strategy]
    else:
        strategies = [1, 2, 3]  # Run all strategies
    
    # Get script directory for default paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run based on the selected mode
    if args.all:
        instances_dir = os.path.join(script_dir, "instances")
        if not os.path.exists(instances_dir):
            print(f"Error: Instances directory not found: {instances_dir}")
            return
        run_all_instances(instances_dir, strategies, args.out)
    else:  # --instance
        run_single_instance(args.instance, strategies, args.out)


if __name__ == "__main__":
    main()
