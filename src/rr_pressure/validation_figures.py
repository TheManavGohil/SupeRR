"""Standalone diagnostic plots; no player rankings."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np


def make_validation_figures(frames, matches, out):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    with PdfPages(out / "VALIDATION_CHARTS.pdf") as pdf:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
        for ax, family in zip(axes, ("IPL", "T20I")):
            part = matches.loc[matches.family.eq(family)].copy()
            totals = part.groupby("year").supplied_events.sum()
            base = np.zeros(len(totals))
            for label, mask, colour in [
                ("Verified", part.accepted, "#127c8a"),
                ("Unresolved / excluded", ~part.accepted & ~part.status.eq("missing_external_match"), "#e6a23c"),
                ("Missing external source", part.status.eq("missing_external_match"), "#b34b61")]:
                values = 100 * part.loc[mask].groupby("year").supplied_events.sum().reindex(totals.index, fill_value=0) / totals
                ax.bar(totals.index.astype(str), values, bottom=base, label=label, color=colour)
                base += values.to_numpy()
            ax.set(title=family, xlabel="Match year", ylim=(0, 100))
        axes[0].set_ylabel("Share of supplied delivery events (%)")
        axes[1].legend(loc="upper left", bbox_to_anchor=(0, -.18), ncol=1)
        fig.suptitle("External reconciliation retains different shares by competition")
        fig.tight_layout(rect=(0, .1, 1, .94))
        pdf.savefig(fig, bbox_inches="tight")
        fig.savefig(out / "coverage.png", dpi=160, bbox_inches="tight")
        plt.close(fig)
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        coverage = frames["pressure_coverage"].query("denominator == 'delivery_events'")
        values = coverage.pressure_full_percent.to_numpy()
        axes[0].axvspan(20, 30, color="#cbe8d5", alpha=.7, label="Registered diagnostic target")
        axes[0].barh(["All retained", "Development 2022–25", "Reserved 2026"], values, color="#127c8a")
        for i, v in enumerate(values): axes[0].text(v + .5, i, f"{v:.2f}%", va="center")
        axes[0].set(xlabel="High-pressure delivery events (%)", xlim=(0, 45), title="Unchanged rule exceeds target band")
        axes[0].legend(loc="lower right", fontsize=8)
        support = frames["context_support_summary"].query("resolution == 'finer_context'")
        vals = support.pressure_supported_percent.to_numpy()
        axes[1].barh(["All retained", "Development 2022–25", "Reserved 2026"], vals, color="#e6a23c")
        axes[1].axvline(80, linestyle="--", color="#555555", label="Registered support diagnostic")
        for i, v in enumerate(vals): axes[1].text(v + 1, i, f"{v:.2f}%", va="center")
        axes[1].set(xlabel="Pressure events with supported ordinary comparison (%)", xlim=(0, 100), title="Late overs have zero ordinary controls")
        axes[1].legend(loc="lower right", fontsize=8)
        fig.suptitle("Coverage and context overlap are separate requirements")
        fig.tight_layout(rect=(0, 0, 1, .93))
        pdf.savefig(fig, bbox_inches="tight")
        fig.savefig(out / "pressure_support.png", dpi=160, bbox_inches="tight")
        plt.close(fig)
