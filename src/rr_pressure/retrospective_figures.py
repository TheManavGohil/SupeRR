"""Exportable prediction and calibration figures for the frozen reference."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def make_retrospective_figures(tables, out):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    targets = ["bat_runs", "bowl_runs", "striker_wicket", "bowler_wicket"]
    with PdfPages(out / "REFERENCE_CHARTS.pdf") as pdf:
        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        for ax, target in zip(axes.flat, targets):
            d = tables["annual_metrics"].loc[lambda d: d.target.eq(target)]
            for model, g in d.groupby("model"):
                ax.plot(g.year, g.primary_loss, marker="o", label=model)
            ax.set(title=target.replace("_", " "), xlabel="Season", ylabel=d.primary_loss_name.iloc[0])
            ax.set_xticks([2023, 2024, 2025])
            ax.legend(fontsize=8)
        fig.suptitle("Held-out contemporary peer reference: prediction loss")
        fig.tight_layout(rect=(0, 0, 1, .96))
        pdf.savefig(fig)
        fig.savefig(out / "prediction_loss.png", dpi=150)
        plt.close(fig)
        fig, axes = plt.subplots(1, 2, figsize=(11, 5))
        counts = tables["alert_counts"]
        for ax, kind, subset in [(axes[0], "Run targets", targets[:2]), (axes[1], "Wicket targets", targets[2:])]:
            part = counts.loc[counts.target.isin(subset)].pivot(index="target", columns="screen", values="alerts")
            part.plot.bar(ax=ax, rot=0, color=["#cf6679", "#368fa2", "#66558a"])
            ax.set(title=kind, xlabel="", ylabel="Material alerts (overlapping groups)")
            ax.set_xticklabels([s.replace("_", " ") for s in part.index])
        fig.suptitle("Combined and separate evaluation-fold calibration screens")
        fig.tight_layout(rect=(0, 0, 1, .93))
        pdf.savefig(fig)
        fig.savefig(out / "calibration_alerts.png", dpi=150)
        plt.close(fig)
        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        for ax, target in zip(axes.flat, targets):
            d = tables["historical_comparisons"].loc[lambda d: d.target.eq(target)].reset_index(drop=True)
            for i, row in d.iterrows():
                ax.plot([row.p10, row.p90], [i, i], color="#368fa2", linewidth=2)
                ax.scatter(row.primary_loss_delta, i, color="#66558a", zorder=3)
            ax.axvline(0, color="gray", linestyle="--")
            ax.set_yticks(range(len(d)), d.comparator)
            ax.set(title=target.replace("_", " "), xlabel="Loss difference; negative favours contemporary reference")
        fig.suptitle("Whole-match 10th–90th percentile intervals; conditional on fitted references")
        fig.tight_layout(rect=(0, 0, 1, .96))
        pdf.savefig(fig)
        fig.savefig(out / "historical_comparison.png", dpi=150)
        plt.close(fig)
