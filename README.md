KernelSight: Intelligent Container Runtime & Monitoring System

KernelSight is a custom, lightweight container runtime developed in C and Python to explore and demonstrate the fundamental mechanics of the Linux Kernel. By bypassing high-level abstractions like Docker, this project provides a transparent look at how Linux Namespaces provide isolation and Cgroups enforce hardware resource constraints.

This project is designed for researchers and engineers who need high-fidelity, isolated observability into containerized processes.

🛠 Project Architecture

The system is divided into three distinct layers:

The Runtime (C): Interfaces directly with the kernel using the clone() system call to create isolated PID, UTS, and Mount namespaces.

Resource Controller (Cgroups v2): Implements hard limits on CPU (50% quota) and Memory (256MB) to ensure host stability and process fairness.

Observability Suite (Python): A host-side monitoring engine and Streamlit dashboard that provides real-time telemetry by polling Cgroup kernel counters.

🚀 Installation & Setup
Prerequisites

OS: Linux or WSL2 (Windows Subsystem for Linux)

Compiler: GCC

Python: 3.8+

1. Initialize Project

Clone the repository and navigate to the root directory:

code
Bash
download
content_copy
expand_less
cd intelligent-container-runtime
2. Prepare the Environment

Compile the C runtime and activate your virtual environment:

code
Bash
download
content_copy
expand_less
# Compile the runtime
gcc runtime/container.c -o runtime/container

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
🚦 Execution Guide (Multi-Terminal Setup)

To see the system in full effect, open separate terminal windows for each component.

Terminal 1: Start the Container
code
Bash
download
content_copy
expand_less
# Start a container named 'test1'
sudo ./runtime/container test1

You are now inside the isolated bash shell of the container.

Terminal 2: Launch the Monitor
code
Bash
download
content_copy
expand_less
# Start the telemetry collector for 'test1'
python3 monitoring/monitor.py test1
Terminal 3: Interactive Dashboard
code
Bash
download
content_copy
expand_less
# Launch the web-based visualization
streamlit run dashboard/app.py

Open http://localhost:8501 in your browser.

Terminal 4: Management CLI
code
Bash
download
content_copy
expand_less
# Use the CLI to check global state
python3 cli.py list

# Check specific container health
python3 cli.py status test1
🧪 Stress Testing & Anomaly Simulation

Use these commands inside the Container Terminal (Terminal 1) to simulate resource anomalies and observe how the kernel enforces limits.

1. CPU Stress (The "Ceiling" Test)

Creates 4 infinite loops to max out the allocated CPU.

code
Bash
download
content_copy
expand_less
# Start 4 background loops
for i in {1..4}; do while true; do :; done & done

Result: The Dashboard will show a flat-line at exactly 50%, validating Cgroup enforcement.

2. Memory Leak Simulation

Uses Python to allocate 1MB of RAM every 0.1 seconds.

code
Bash
download
content_copy
expand_less
python3 -c 'import time; a=[]; [ (a.append("X"*1024*1024), time.sleep(0.1)) for x in range(200) ]'

Result: You will see a steady "staircase" climb on the Memory graph.

3. Process Burst

Spawns 20 background processes to test PID isolation.

code
Bash
download
content_copy
expand_less
for i in {1..20}; do sleep 100 & done
📉 Observing the "Dip" (Validation)

To verify the system's responsiveness, kill the stress processes and watch the metrics drop in real-time.

Metric	Kill Command (Inside Container)	Expected Dashboard Result
CPU (Instant)	pkill -f "while true"	Sudden drop from 50% to ~0%.
CPU (Step)	kill %1, then kill %2	25% incremental drops in the graph.
Memory	pkill python3	Sharp vertical drop as kernel reclaims RAM.
Processes	pkill sleep	Drop from 20+ back down to 1 (the shell).
Emergency	kill -9 $(jobs -p)	Force-kills all background tasks.
Note on Latency

There is a 1–3 second propagation delay between a command and the graph movement. This is a design characteristic:

Monitor: Polls every 1 second.

Dashboard: Refreshes every 2 seconds.

📈 Final Results & Discussion

The project successfully validates that:

Isolation is achieved: Processes inside test1 are invisible to test2.

Limits are absolute: The kernel strictly adheres to the 50% CPU and 256MB RAM limits defined in container.c.

Observability is decoupled: The monitoring and visualization layers operate independently of the containerized workload, ensuring that monitoring does not interfere with process performance.

📂 Repository Structure

runtime/: Contains the C source code and the isolated root filesystem logic.

monitoring/: Python logic for Cgroup v2 data polling and CSV serialization.

dashboard/: Streamlit application for real-time time-series visualization.

cli.py: Command-line utility for container auditing and status reporting.

containers.json: Persistent state tracking for active and stopped containers.

Author: Rajath V S
Topic: Operating Systems, Containerization, Linux Kernel Primitives.