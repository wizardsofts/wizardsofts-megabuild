"""
Basic Ray cluster test
Tests: Cluster connectivity, worker availability, basic task execution
"""
import ray
import time
import sys

@ray.remote
def cpu_intensive_task(iterations: int):
    """Simulate CPU-intensive task"""
    result = 0
    for i in range(iterations):
        result += i ** 2
    return {
        "result": result,
        "node": ray.get_runtime_context().get_node_id(),
        "worker_id": ray.get_runtime_context().get_worker_id()
    }

def main():
    # Connect to Ray cluster
    print("🔗 Connecting to Ray cluster...")
    try:
        ray.init(address="ray://10.0.0.84:10001")
    except Exception as e:
        print(f"❌ Failed to connect to Ray cluster: {e}")
        print("Make sure Ray head node is running on Server 84")
        sys.exit(1)

    print("\n📊 Cluster Information:")
    print(f"   Nodes: {len(ray.nodes())}")
    print(f"   Available CPUs: {ray.available_resources().get('CPU', 0)}")
    print(f"   Available Memory: {ray.available_resources().get('memory', 0) / 1e9:.2f} GB")

    print("\n🚀 Running distributed tasks...")

    # Submit 20 tasks across cluster
    futures = [cpu_intensive_task.remote(1_000_000) for _ in range(20)]

    start_time = time.time()
    results = ray.get(futures)
    elapsed = time.time() - start_time

    print(f"\n✅ Completed {len(results)} tasks in {elapsed:.2f}s")

    # Show task distribution
    node_distribution = {}
    for result in results:
        node = result['node']
        node_distribution[node] = node_distribution.get(node, 0) + 1

    print("\n📈 Task Distribution:")
    for node, count in node_distribution.items():
        print(f"   Node {node[:8]}: {count} tasks")

    ray.shutdown()
    print("\n✅ Test passed!")

if __name__ == "__main__":
    main()
