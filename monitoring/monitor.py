import os
import sys
import time

def read_cgroup_val(container, filename):
    """Reads a value from the container's cgroup directory."""
    path = f"/sys/fs/cgroup/{container}/{filename}"
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 monitor.py <container_name>")
        return

    container = sys.argv[1]
    filename = f"monitoring/metrics_{container}.csv"
    
    # Ensure monitoring directory exists
    os.makedirs("monitoring", exist_ok=True)

    print(f"--- MONITORING STARTED FOR: {container} ---")
    
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("timestamp,cpu,mem,proc\n")

    # For CPU calculation: usage_usec is cumulative
    # We need to track the delta over time
    prev_usage = 0
    prev_time = time.time()

    while True:
        # 1. CPU Calculation (using cpu.stat)
        cpu_data = read_cgroup_val(container, "cpu.stat")
        if cpu_data is None:
            print(f"Container {container} not found. Waiting...")
            time.sleep(2)
            continue

        # Extract usage_usec from the first line of cpu.stat
        # Format is usually: usage_usec <value>
        current_usage = int(cpu_data.split()[1]) 
        current_time = time.time()
        
        delta_usage = current_usage - prev_usage
        delta_time = (current_time - prev_time) * 1_000_000 # convert to microseconds
        
        cpu_pct = (delta_usage / delta_time) * 100 if delta_time > 0 else 0
        
        # 2. Memory Usage
        # memory.current gives usage in bytes. 
        # Your C code sets limit to 256MB (268435456 bytes)
        mem_bytes = int(read_cgroup_val(container, "memory.current") or 0)
        mem_pct = (mem_bytes / 268435456) * 100

        # 3. Process Count
        # cgroup.procs lists all PIDs in the container
        procs = read_cgroup_val(container, "cgroup.procs")
        proc_count = len(procs.splitlines()) if procs else 0

        # Save to CSV
        with open(filename, "a") as f:
            f.write(f"{int(current_time)},{cpu_pct:.2f},{mem_pct:.2f},{proc_count}\n")

        # Update previous values for next iteration
        prev_usage = current_usage
        prev_time = current_time
        
        time.sleep(1)

if __name__ == "__main__":
    main()