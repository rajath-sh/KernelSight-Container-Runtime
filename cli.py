import argparse
import json
import os

STATE_FILE = "containers.json"

# ---------------- HELPER ----------------
def is_pid_running(pid):
    """Check if a process ID exists in the system /proc directory."""
    if not pid:
        return False
    # In Linux, every running process has a folder in /proc/
    # We just check if the folder exists. No special permissions needed.
    return os.path.exists(f"/proc/{pid}")

# ---------------- STATE HANDLING ----------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ---------------- LIST COMMAND ----------------
def is_container_active(name):
    """
    Checks if the container is active by looking at its Cgroup.
    This is the most accurate way for your specific project.
    """
    path = f"/sys/fs/cgroup/{name}/cgroup.procs"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                content = f.read().strip()
                # If there is at least one PID in this file, it's running
                return len(content) > 0
        except:
            return False
    return False

def list_containers():
    # 1. Load the existing state from JSON
    state = load_state()
    
    # 2. Scan the monitoring folder to find ALL containers (test1, test2, etc.)
    monitoring_dir = "monitoring"
    if os.path.exists(monitoring_dir):
        for filename in os.listdir(monitoring_dir):
            if filename.startswith("metrics_") and filename.endswith(".csv"):
                # Extract "test1" from "metrics_test1.csv"
                name = filename.replace("metrics_", "").replace(".csv", "")
                if name not in state:
                    state[name] = {"status": "unknown"}

    if not state:
        print("No containers found (check if monitor.py is running).")
        return

    print(f"{'NAME':<15} | {'STATUS':<10}")
    print("-" * 30)
    
    changed = False
    # Sort the names so test1 comes before test2
    for name in sorted(state.keys()):
        # Check if active in system using the Cgroup check we built
        alive = is_container_active(name)
        
        display_status = "RUNNING" if alive else "STOPPED"
        
        # Sync the status in our state variable
        new_status = display_status.lower()
        if state[name].get("status") != new_status:
            state[name]["status"] = new_status
            changed = True

        print(f"{name:<15} | {display_status:<10}")

    # 3. Save the discovered containers back to the JSON so they stay there
    if changed:
        save_state(state)

# ---------------- STATUS COMMAND ----------------
def read_latest_metrics(container):
    file = f"monitoring/metrics_{container}.csv"
    if not os.path.exists(file):
        return None

    try:
        with open(file, "r") as f:
            lines = f.readlines()
            if len(lines) < 2:
                return None
            last_line = lines[-1].strip().split(",")
            return {
                "cpu": last_line[1],
                "mem": last_line[2],
                "proc": last_line[3],
            }
    except:
        return None

def show_status(container):
    stats = read_latest_metrics(container)
    if not stats:
        print(f"Error: No active metrics found for '{container}'.")
        return

    print(f"\nContainer Status: {container}")
    print("-" * 30)
    print(f"CPU Usage      : {stats['cpu']}%")
    print(f"Memory Usage   : {stats['mem']}%")
    print(f"Process Count  : {stats['proc']}")
    print("-" * 30)

# ---------------- MAIN ----------------
def main():
    parser = argparse.ArgumentParser(description="Container Monitoring CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list")
    status_cmd = sub.add_parser("status")
    status_cmd.add_argument("name")

    args = parser.parse_args()

    if args.cmd == "list":
        list_containers()
    elif args.cmd == "status":
        show_status(args.name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()