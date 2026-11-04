"""Buat grafik L3.4 dari hasil benchmark pada laporan."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


workers = [1, 4, 10]
time_s = [21.711, 5.176, 2.109]
throughput = [9.21, 38.64, 94.85]
latency_ms = [2067.97, 495.21, 202.91]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
})
fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.3), constrained_layout=True)
fig.suptitle(
    "Praktikum 3 - Pengaruh max_workers terhadap kinerja RPC",
    fontsize=15,
    fontweight="bold",
)

charts = [
    (axes[0], time_s, "Waktu total", "Detik", "#3366A8", "{:.3f}"),
    (axes[1], throughput, "Throughput", "Request per detik", "#2A8C68", "{:.2f}"),
    (axes[2], latency_ms, "Latensi rata-rata", "Milidetik", "#D47A26", "{:.2f}"),
]
for axis, values, title, ylabel, color, number_format in charts:
    bars = axis.bar([str(value) for value in workers], values, color=color, width=0.62)
    axis.set_title(title, fontweight="bold", pad=12)
    axis.set_xlabel("max_workers")
    axis.set_ylabel(ylabel)
    axis.grid(axis="y", linestyle="--", alpha=0.35)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    axis.bar_label(bars, labels=[number_format.format(value) for value in values], padding=4)
    axis.margins(y=0.16)

fig.text(
    0.5,
    -0.025,
    "Data: 200 pemanggilan GetMahasiswa, 20 thread client, delay server 0,1 s",
    ha="center",
    fontsize=9,
    color="#555555",
)
fig.savefig(
    "praktikum3_kegagalan/grafik_l3_4.png",
    dpi=220,
    bbox_inches="tight",
    facecolor="white",
)
