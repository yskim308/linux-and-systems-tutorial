import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("output.csv")

df["time"] = pd.to_datetime(df["time"])

plt.figure(figsize=(10, 6))
plt.plot(df["time"], df["utilization"], linestyle="-", marker=".", color="b")

plt.title("System Utilization Over Time")
plt.xlabel("Time")
plt.ylabel("Utilization")

plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
plt.gcf().autofmt_xdate()

plt.grid(True, linestyle="--", alpha=0.7)
plt.tight_layout()

plt.show()
