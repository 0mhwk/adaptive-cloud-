"""
scripts/stress_cpu.py
Safely spikes all CPU cores on your laptop to 95-100% for 20 seconds.
Press Ctrl+C anytime to stop immediately.
"""
import os
import sys
import time
from multiprocessing import Pool, cpu_count


def burn_cpu(core_idx: int) -> None:
    """Tight math loop to max out one CPU core."""
    end_time = time.time() + 25  # 25 seconds duration
    x = 0
    while time.time() < end_time:
        x = (x + 1) * (x + 1) % 10000007


def main():
    cores = cpu_count()
    print("=" * 70)
    print(f"🔥 ADAPTIVECLOUD REAL HARDWARE STRESS TEST")
    print(f"   Spawning worker threads across all {cores} CPU cores...")
    print("   Target: Your laptop's physical CPU")
    print("   Duration: 25 seconds (auto-stops, or press Ctrl+C)")
    print("=" * 70)
    print("\n[*] Starting CPU stress NOW... Open your browser at:")
    print("    👉 http://localhost:5173/monitoring")
    print("    Watch the 'Host Laptop (You)' CPU gauge jump to 90%+ in real time!\n")

    try:
        with Pool(cores) as p:
            p.map(burn_cpu, range(cores))
        print("\n[✓] Stress test complete! CPU returning to idle baseline.")
    except KeyboardInterrupt:
        print("\n[✓] Stopped by user. CPU returning to idle baseline.")


if __name__ == "__main__":
    main()
