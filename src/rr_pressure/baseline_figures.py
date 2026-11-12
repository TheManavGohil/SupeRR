"""Standalone development diagnostics for the historical peer baseline."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def make_baseline_figures(tables, config, out):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    targets = ["bat_runs", "striker_wicket", "bowl_runs", "bowler_wicket"]
    with PdfPages(out / "BASELINE_CHARTS.pdf") as pdf:
        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        annual = tables["annual_metrics"]
        for ax, target in zip(axes.flat, targets):
            part = annual.loc[annual.target.eq(target) & annual.prior_events.eq(config["default_prior_events"])]
            for model, group in part.groupby("model"):
                ax.plot(group.year, group.primary_loss, marker="o", label=model)
            ax.set(title=target.replace("_", " "), xlabel="Evaluation year", ylabel=part.primary_loss_name.iloc[0])
            ax.set_xticks([2023, 2024, 2025])
            ax.legend(fontsize=8)
        fig.suptitle("Earlier-year peer expectations: lower prediction loss is better")
        fig.tight_layout(rect=(0, 0, 1, .96))
        pdf.savefig(fig)
        fig.savefig(out / "annual_prediction_loss.png", dpi=150)
        plt.close(fig)
        fig, axes = plt.subplots(1, 2, figsize=(11, 5))
        for ax, target in zip(axes, ["striker_wicket", "bowler_wicket"]):
            p = tables["reliability"].loc[lambda x: x.target.eq(target)]
            maximum = max(p.predicted.max(), p.observed.max(), .1) * 1.1
            ax.plot([0, maximum], [0, maximum], "--", color="gray")
            ax.scatter(p.predicted, p.observed, s=30 + 300 * p.events / p.events.max(), color="#127c8a")
            ax.set(title=target.replace("_", " "), xlabel="Mean predicted probability", ylabel="Observed rate", xlim=(0, maximum), ylim=(0, maximum))
        fig.suptitle("Development wicket calibration; marker area reflects exposure")
        fig.tight_layout(rect=(0, 0, 1, .93))
        pdf.savefig(fig)
        fig.savefig(out / "wicket_calibration.png", dpi=150)
        plt.close(fig)
        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        pooled = tables["pooled_metrics"]
        for ax, target in zip(axes.flat, targets):
            p = pooled.loc[pooled.target.eq(target) & pooled.model.eq("hierarchical")]
            ax.plot(p.prior_events, p.primary_loss, marker="o", color="#127c8a")
            ax.axvline(config["default_prior_events"], linestyle="--", color="#b34b61", label="Registered default")
            ax.set(title=target.replace("_", " "), xlabel="Prior event count", ylabel="Primary loss")
            ax.legend(fontsize=8)
        fig.suptitle("Registered sensitivity settings; default is not automatically retuned")
        fig.tight_layout(rect=(0, 0, 1, .96))
        pdf.savefig(fig)
        plt.close(fig)
