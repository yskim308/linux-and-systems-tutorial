import matplotlib.pyplot as plt
import pandas as pd

df_reg = pd.read_csv("regular.csv")
df_heavy = pd.read_csv("heavy.csv")

for df in [df_reg, df_heavy]:
    df["time"] = pd.to_datetime(df["time"])
    df["elapsed"] = (df["time"] - df["time"].iloc[0]).dt.total_seconds()

plt.figure(figsize=(10, 6))

plt.plot(
    df_reg["elapsed"],
    df_reg["utilization"],
    label="4 Regular Tabs",
    color="blue",
    linewidth=2,
)
plt.plot(
    df_heavy["elapsed"],
    df_heavy["utilization"],
    label="4 Heavy JS Tabs",
    color="red",
    linewidth=2,
)

plt.title("Memory Utilization: Regular vs. Heavy JavaScript")
plt.xlabel("Time (seconds)")
plt.ylabel("Memory Utilization (Units)")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.7)

plt.savefig("memory_comparison.png")
print("Plot saved as memory_comparison.png")
