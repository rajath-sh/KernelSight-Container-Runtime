import streamlit as st
import pandas as pd
import os
import time
import altair as alt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Container Monitoring Dashboard", layout="wide")
st.title("📊 Container Monitoring Dashboard")

# ---------------- DYNAMIC SELECTOR ----------------
# Find all metrics files to support multiple containers
if not os.path.exists("monitoring"):
    os.makedirs("monitoring")

files = [f for f in os.listdir("monitoring") if f.startswith("metrics_") and f.endswith(".csv")]
container_list = [f.replace("metrics_", "").replace(".csv", "") for f in files]

if not container_list:
    st.warning("No monitoring data found. Start a container and monitor.py first.")
    time.sleep(2)
    st.rerun()

# Sidebar to switch between containers
selected_container = st.sidebar.selectbox("Select Container", container_list)
metrics_file = f"monitoring/metrics_{selected_container}.csv"

# ---------------- LOAD DATA ----------------
df = pd.read_csv(metrics_file)

if df.empty:
    st.warning(f"Waiting for data in {metrics_file}...")
    time.sleep(2)
    st.rerun()

df["time"] = pd.to_datetime(df["timestamp"], unit='s')
latest = df.iloc[-1]

# ---------------- LIVE METRICS ----------------
c1, c2, c3 = st.columns(3)
c1.metric("CPU Usage (%)", f"{latest['cpu']:.2f}%")
c2.metric("Memory Usage (%)", f"{latest['mem']:.2f}%")
c3.metric("Process Count", int(latest["proc"]))

# ---------------- CPU & MEMORY GRAPH ----------------
st.subheader(f"Usage for: {selected_container}")
plot_df = df.tail(100)

cpu_mem_df = plot_df.melt(
    id_vars="time",
    value_vars=["cpu", "mem"],
    var_name="Metric",
    value_name="Value"
)

cpu_mem_chart = (
    alt.Chart(cpu_mem_df)
    .mark_line(interpolate='monotone')
    .encode(
        x=alt.X("time:T", title="Time (s)"),
        y=alt.Y("Value:Q", title="Usage (%)", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("Metric:N", title="Metric"),
        tooltip=["time:T", "Metric:N", "Value:Q"]
    )
    .properties(height=300)
)
st.altair_chart(cpu_mem_chart, use_container_width=True)

# ---------------- PROCESS COUNT GRAPH ----------------
proc_chart = (
    alt.Chart(plot_df)
    .mark_line(color="orange")
    .encode(
        x=alt.X("time:T", title="Time (s)"),
        y=alt.Y("proc:Q", title="Processes", scale=alt.Scale(zero=False)),
        tooltip=["time:T", "proc:Q"]
    )
    .properties(height=200)
)
st.altair_chart(proc_chart, use_container_width=True)

# ---------------- AUTO REFRESH ----------------
time.sleep(2)
st.rerun()