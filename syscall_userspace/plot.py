import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("utilization.csv")

# 2. Convert the 'time' column from strings to datetime objects
df["time"] = pd.to_datetime(df["time"])

# 3. Create the plot
plt.figure(figsize=(10, 6))
plt.plot(df["time"], df["utilization"], linestyle="-", marker=".", color="b")

# 4. Format the graph
plt.title("System Utilization Over Time")
plt.xlabel("Time")
plt.ylabel("Utilization")

# Format the x-axis to show only Hours:Minutes:Seconds to keep it clean
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
plt.gcf().autofmt_xdate()  # Automatically rotates the time labels so they don't overlap

plt.grid(True, linestyle="--", alpha=0.7)
plt.tight_layout()

# 5. Display the graph
plt.savefig("system_utilization_plot.png", dpi=300)
