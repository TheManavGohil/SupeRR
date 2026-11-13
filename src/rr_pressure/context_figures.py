"""Compare the preregistered contextual revision with the original baseline."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def make_context_figures(tables, original_calibration, out):
    targets = ["bat_runs", "striker_wicket", "bowl_runs", "bowler_wicket"]
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    with PdfPages(out / "CONTEXT_CHARTS.pdf") as pdf:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        paired = tables["paired_against_v1"].set_index("target").loc[targets]
        axes[0].barh(targets, paired.relative_improvement_percent, color="#127c8a")
        axes[0].axvline(0, color="gray", linewidth=1)
        axes[0].set(xlabel="Primary loss reduction versus v1 (%)", title="Prediction improvement")
        counts = tables["alert_counts"].pivot(index="target", columns="candidate", values="material_alert").loc[targets]
        counts.plot.barh(ax=axes[1], color=["#127c8a", "#e6a23c"])
        axes[1].set(xlabel="Overlapping material calibration alerts", ylabel="", title="Same calibration screen")
        fig.tight_layout()
        pdf.savefig(fig)
        fig.savefig(out / "candidate_comparison.png", dpi=150)
        plt.close(fig)
        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        for ax, target in zip(axes.flat, targets):
            for label, table, color in [("Historical v1", original_calibration, "#e6a23c"),
                                       ("Context v2", tables["calibration"], "#127c8a")]:
                part = table.loc[table.target.eq(target) & table.resolution.eq("pressure")].sort_values("pressure_full")
                ax.plot(["Ordinary", "Pressure"], part.mean_bias * 100, marker="o", color=color, label=label)
            ax.axhline(0, color="gray", linewidth=1)
            ax.set(title=target.replace("_", " "), ylabel="Observed − expected per 100 opportunities")
            ax.legend(fontsize=8)
        fig.suptitle("Population residual bias; these are not player-change estimates")
        fig.tight_layout(rect=(0, 0, 1, .95))
        pdf.savefig(fig)
        plt.close(fig)
