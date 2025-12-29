#!/usr/bin/env python3
"""
GPU Acceleration Benchmark for CKKS Homomorphic Encryption

This script benchmarks the performance improvements of GPU-accelerated
CKKS operations for face recognition workloads.

Usage:
    python gpu_benchmark.py [--sizes 1000 10000 50000] [--iterations 3]

Requirements:
    - OpenFHE (CPU fallback available)
    - CuPy or PyCUDA (optional, for GPU acceleration)
    - NumPy
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from homomorphic_face_encryption.crypto.ckks_encryptor_gpu import CKKSEncryptorGPU
    GPU_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  GPU encryptor not available: {e}")
    print("Falling back to CPU-only benchmarking...")
    from homomorphic_face_encryption.crypto.ckks_encryptor import CKKSEncryptor
    CKKSEncryptorGPU = CKKSEncryptor
    GPU_AVAILABLE = False

import numpy as np


def generate_test_embeddings(num_embeddings: int, embedding_dim: int = 512) -> List[List[float]]:
    """Generate random test embeddings."""
    np.random.seed(42)  # For reproducible results
    embeddings = []

    for _ in range(num_embeddings):
        # Generate normalized embeddings similar to face recognition models
        embedding = np.random.normal(0, 1, embedding_dim)
        # L2 normalize like real face embeddings
        embedding = embedding / np.linalg.norm(embedding)
        embeddings.append(embedding.tolist())

    return embeddings


def benchmark_batch_encryption(encryptor: CKKSEncryptorGPU, embeddings: List[List[float]]) -> Dict[str, Any]:
    """Benchmark batch encryption performance."""
    print(f"🔐 Benchmarking batch encryption of {len(embeddings)} embeddings...")

    start_time = time.time()
    encrypted_embeddings, stats = encryptor.batch_encrypt_embeddings_gpu(embeddings)
    end_time = time.time()

    actual_time = end_time - start_time
    throughput = len(embeddings) / actual_time if actual_time > 0 else 0

    results = {
        'operation': 'batch_encryption',
        'num_embeddings': len(embeddings),
        'method': stats.get('method', 'unknown'),
        'time_seconds': actual_time,
        'throughput_embeddings_per_sec': throughput,
        'estimated_memory_mb': stats.get('estimated_memory_mb', 0),
        'stats': stats
    }

    print(f"  ✅ Completed in {actual_time:.2f}s ({throughput:.1f} embeddings/sec)")
    return results


def benchmark_parallel_distance_computation(
    encryptor: CKKSEncryptorGPU,
    query_ciphertext,
    stored_ciphertexts: List
) -> Dict[str, Any]:
    """Benchmark parallel distance computation performance."""
    num_comparisons = len(stored_ciphertexts)
    print(f"📏 Benchmarking parallel distance computation ({num_comparisons} comparisons)...")

    start_time = time.time()
    encrypted_distances, stats = encryptor.parallel_distance_computation_gpu(
        query_ciphertext, stored_ciphertexts
    )
    end_time = time.time()

    actual_time = end_time - start_time
    throughput = num_comparisons / actual_time if actual_time > 0 else 0

    results = {
        'operation': 'parallel_distance_computation',
        'num_comparisons': num_comparisons,
        'method': stats.get('method', 'unknown'),
        'time_seconds': actual_time,
        'throughput_comparisons_per_sec': throughput,
        'time_per_comparison_ms': stats.get('time_per_comparison_ms', 0),
        'estimated_memory_mb': stats.get('estimated_memory_mb', 0),
        'stats': stats
    }

    print(f"  ✅ Completed in {actual_time:.2f}s ({throughput:.1f} comparisons/sec)")
    return results


def run_comprehensive_benchmark(
    sizes: List[int],
    iterations: int = 3,
    output_file: str = None
) -> Dict[str, Any]:
    """Run comprehensive CPU vs GPU benchmark."""
    print("🚀 Starting Comprehensive CKKS GPU Performance Benchmark")
    print("=" * 60)

    # Initialize encryptor
    print("🔧 Initializing CKKS encryptor...")
    encryptor = CKKSEncryptorGPU()

    try:
        encryptor.setup_context()
        encryptor.generate_keys()
        print("✅ CKKS context initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize CKKS context: {e}")
        return {'error': str(e)}

    # Get GPU info
    gpu_info = encryptor.get_gpu_info()
    print(f"🎮 GPU Info: {gpu_info}")

    all_results = {
        'timestamp': time.time(),
        'gpu_info': gpu_info,
        'benchmark_sizes': sizes,
        'iterations': iterations,
        'results': []
    }

    for size in sizes:
        print(f"\n📊 Testing with {size} templates")

        size_results = {
            'template_count': size,
            'iterations': []
        }

        for iteration in range(iterations):
            print(f"  🔄 Iteration {iteration + 1}/{iterations}")

            # Generate test data
            query_embeddings = generate_test_embeddings(1)
            stored_embeddings = generate_test_embeddings(size)

            iteration_results = {}

            try:
                # Benchmark batch encryption
                query_cts, _ = encryptor.batch_encrypt_embeddings_gpu(query_embeddings)
                stored_cts, _ = encryptor.batch_encrypt_embeddings_gpu(stored_embeddings)

                # Benchmark encryption performance
                encryption_results = benchmark_batch_encryption(encryptor, stored_embeddings)
                iteration_results['encryption'] = encryption_results

                # Benchmark distance computation
                distance_results = benchmark_parallel_distance_computation(
                    encryptor, query_cts[0], stored_cts
                )
                iteration_results['distance_computation'] = distance_results

                # Combined performance
                total_time = encryption_results['time_seconds'] + distance_results['time_seconds']
                total_throughput = size / total_time if total_time > 0 else 0

                iteration_results['combined'] = {
                    'total_time_seconds': total_time,
                    'total_throughput_templates_per_sec': total_throughput,
                    'method': encryption_results['method']  # Same for both
                }

                print(f"    ✅ Combined: {total_time:.2f}s ({total_throughput:.1f} templates/sec)")
            except Exception as e:
                print(f"    ❌ Iteration {iteration + 1} failed: {e}")
                iteration_results['error'] = str(e)

            size_results['iterations'].append(iteration_results)

            # Memory cleanup between iterations
            encryptor.cleanup_gpu_memory()

        all_results['results'].append(size_results)

    # Calculate summary statistics
    summary = calculate_summary_statistics(all_results)
    all_results['summary'] = summary

    # Print final results
    print("\n🏆 Final Benchmark Summary")
    print("=" * 60)
    print_summary(summary)

    # Save results
    if output_file:
        try:
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
            print(f"📄 Results saved to {output_file}")
        except Exception as e:
            print(f"⚠️  Failed to save results: {e}")

    return all_results


def calculate_summary_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate summary statistics across all benchmark runs."""
    summary = {
        'sizes_tested': [],
        'cpu_performance': {},
        'gpu_performance': {},
        'speedup_analysis': {}
    }

    for size_result in results['results']:
        size = size_result['template_count']
        summary['sizes_tested'].append(size)

        size_cpu_times = []
        size_gpu_times = []

        for iteration in size_result['iterations']:
            if 'error' in iteration:
                continue

            combined = iteration.get('combined', {})
            method = combined.get('method', 'unknown')
            total_time = combined.get('total_time_seconds', 0)

            if method == 'cpu':
                size_cpu_times.append(total_time)
            elif method == 'gpu':
                size_gpu_times.append(total_time)

        # Calculate averages
        if size_cpu_times:
            summary['cpu_performance'][size] = {
                'avg_time': np.mean(size_cpu_times),
                'std_time': np.std(size_cpu_times),
                'throughput': size / np.mean(size_cpu_times) if size_cpu_times else 0
            }

        if size_gpu_times:
            summary['gpu_performance'][size] = {
                'avg_time': np.mean(size_gpu_times),
                'std_time': np.std(size_gpu_times),
                'throughput': size / np.mean(size_gpu_times) if size_gpu_times else 0
            }

    # Calculate speedup factors
    for size in summary['sizes_tested']:
        cpu_perf = summary['cpu_performance'].get(size)
        gpu_perf = summary['gpu_performance'].get(size)

        if cpu_perf and gpu_perf:
            speedup = cpu_perf['avg_time'] / gpu_perf['avg_time'] if gpu_perf['avg_time'] > 0 else 0
            summary['speedup_analysis'][size] = {
                'speedup_factor': speedup,
                'cpu_time': cpu_perf['avg_time'],
                'gpu_time': gpu_perf['avg_time'],
                'cpu_throughput': cpu_perf['throughput'],
                'gpu_throughput': gpu_perf['throughput']
            }

    return summary


def print_summary(summary: Dict[str, Any]):
    """Print formatted benchmark summary."""
    print("Template Sizes Tested:", summary['sizes_tested'])
    print()

    if summary['speedup_analysis']:
        print("🚀 Performance Comparison (CPU vs GPU):")
        print("-" * 80)
        print("<10"        print("-" * 80)

        for size in summary['sizes_tested']:
            analysis = summary['speedup_analysis'].get(size)
            if analysis:
                speedup = analysis['speedup_factor']
                cpu_time = analysis['cpu_time']
                gpu_time = analysis['gpu_time']

                print("<10"
                      "<10.2f"
                      "<10.2f"
                      "<8.1f")

        print()
        print("📈 Throughput Comparison:")
        print("-" * 80)
        print("<10"        print("-" * 80)

        for size in summary['sizes_tested']:
            analysis = summary['speedup_analysis'].get(size)
            if analysis:
                cpu_tp = analysis['cpu_throughput']
                gpu_tp = analysis['gpu_throughput']

                print("<10"
                      "<10.1f"
                      "<10.1f")

    else:
        print("📊 CPU-Only Performance:")
        print("-" * 60)
        print("<10")
        print("-" * 60)

        for size in summary['sizes_tested']:
            cpu_perf = summary['cpu_performance'].get(size)
            if cpu_perf:
                print("<10"
                      "<10.2f"
                      "<10.1f")

    print()
    print("💡 Recommendations:")
    if summary['speedup_analysis']:
        avg_speedup = np.mean([
            analysis['speedup_factor']
            for analysis in summary['speedup_analysis'].values()
        ])

        if avg_speedup > 5:
            print("  🎯 Excellent GPU acceleration! Consider GPU for production workloads.")
        elif avg_speedup > 2:
            print("  👍 Good GPU acceleration. GPU beneficial for larger datasets.")
        else:
            print("  🤔 Limited GPU speedup. CPU might be sufficient for your workload.")

        print(f"  Average speedup: {avg_speedup:.1f}x")
    else:
        print("  🎮 No GPU detected. Consider installing CUDA and CuPy for GPU acceleration.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CKKS GPU Acceleration Performance Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gpu_benchmark.py --sizes 1000 10000 50000 --iterations 5
  python gpu_benchmark.py --output results.json
        """
    )

    parser.add_argument(
        '--sizes', nargs='+', type=int,
        default=[1000, 10000],
        help='Template sizes to benchmark (default: 1000 10000)'
    )

    parser.add_argument(
        '--iterations', type=int, default=3,
        help='Number of iterations per size (default: 3)'
    )

    parser.add_argument(
        '--output', type=str,
        help='Output file for detailed results (JSON format)'
    )

    args = parser.parse_args()

    try:
        results = run_comprehensive_benchmark(
            sizes=args.sizes,
            iterations=args.iterations,
            output_file=args.output
        )

        # Exit with success
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️  Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
