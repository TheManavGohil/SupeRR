"""Static publication artifacts for the EDA milestone."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/rr-matplotlib")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

COLORS = {"IPL": "#d74b86", "T20I": "#276b96", "Other T20": "#8b919a"}


def markdown_table(frame, columns=None, digits=2):
    part = frame[columns] if columns else frame
    headers = list(part.columns)
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for values in part.itertuples(index=False, name=None):
        text = [f"{v:.{digits}f}" if isinstance(v, (float, np.floating)) else str(v) for v in values]
        lines.append("| " + " | ".join(text) + " |")
    return "\n".join(lines)


def make_figures(tables, events, out):
    directory = out / "figures"
    directory.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.titleweight": "bold", "figure.facecolor": "white"})
    figures = []
    pdf = PdfPages(out / "EDA_CHARTS.pdf")

    def save(fig, name, note):
        fig.text(0.02, 0.015, note, fontsize=8, color="#555555")
        fig.tight_layout(rect=(0, 0.055, 1, 0.97))
        fig.savefig(directory / f"{name}.png", dpi=170)
        fig.savefig(directory / f"{name}.svg")
        pdf.savefig(fig)
        plt.close(fig)
        figures.append(name)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    source = tables["match_coverage"].pivot(index="year", columns="family", values="matches").fillna(0)
    source.plot.bar(stacked=True, color=[COLORS[c] for c in source], ax=axes[0], rot=0)
    axes[0].set(title="Matches supplied by year", xlabel="Year", ylabel="Matches")
    retention = tables["retention_by_year_family"].pivot(index="year", columns="family", values="retained_pct")
    retention.plot.bar(color=[COLORS[c] for c in retention], ax=axes[1], rot=0)
    axes[1].set(title="Retained for pressure-proxy EDA", xlabel="Year", ylabel="% of primary normal-innings events", ylim=(0, 105))
    save(fig, "01_coverage", "Cutoff 1 Nov 2026. Coverage measures this supplied pack; 2026 is a partial-year sample.")

    phase = tables["phase_metrics"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for family, sub in phase.groupby("family"):
        pooled = sub.groupby("phase").agg(runs=("recorded_runs", "sum"), opportunities=("batting_opportunities", "sum"),
                                          wickets=("bowler_credited_wickets", "sum"), attempts=("delivery_events", "sum"))
        axes[0].plot(pooled.index, 100 * pooled.runs / pooled.opportunities, "o-", color=COLORS[family], label=family)
        axes[1].plot(pooled.index, 100 * pooled.wickets / pooled.attempts, "o-", color=COLORS[family], label=family)
    axes[0].set(title="Recorded scoring by innings phase", xlabel="Overs", ylabel="Recorded runs / 100 non-wide opportunities")
    axes[1].set(title="Bowler-credited wickets by phase", xlabel="Overs", ylabel="Wickets / 100 delivery attempts")
    for ax in axes:
        ax.legend(); ax.grid(axis="y", alpha=.2)
    save(fig, "02_phase_patterns", "Accepted IPL/T20I proxy cohort. Analytical rates; recorded runs exclude unresolved extra quantities.")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, family in zip(axes, ("IPL", "T20I")):
        sub = phase[phase.family.eq(family)]
        for innings, group in sub.groupby("innings"):
            ax.plot(group.phase, group.recorded_runs_per_100_opportunities, "o-", label=f"Innings {innings}")
        ax.set(title=f"{family}: innings comparison", xlabel="Overs", ylabel="Recorded runs / 100 non-wide opportunities")
        ax.legend(); ax.grid(axis="y", alpha=.2)
    save(fig, "03_innings_comparison", "Descriptive patterns are affected by innings survival, targets and player selection; they do not identify a chasing effect.")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    reasons = tables["pressure_reason_counts"].pivot(index="family", columns="reason", values="events").fillna(0)
    pct = reasons.div(reasons.sum(axis=1), axis=0) * 100
    order = ["ordinary_proxy", "late_only", "collapse_only", "late_and_collapse"]
    pct.reindex(columns=order, fill_value=0).plot.barh(stacked=True, color=["#dfe4e8", "#d74b86", "#eaa84e", "#674496"], ax=axes[0])
    axes[0].set(title="What the pressure proxy flags", xlabel="% of delivery events", ylabel="")
    axes[0].legend(fontsize=8, loc="upper center", bbox_to_anchor=(.5, -.16), ncol=2)
    over = tables["over_metrics"].groupby(["family", "overid"])[["delivery_events", "proxy_pressure_events"]].sum().reset_index()
    for family, sub in over.groupby("family"):
        axes[1].plot(sub.overid, 100 * sub.proxy_pressure_events / sub.delivery_events, label=family, color=COLORS[family])
    axes[1].set(title="Proxy pressure share by over", xlabel="Over", ylabel="% of events", ylim=(0, 105))
    axes[1].legend(); axes[1].grid(axis="y", alpha=.2)
    save(fig, "04_pressure_exposure", "Proxy = late OR collapse. Tight-chase flags are unavailable until scores are verified; overs 16–20 always qualify.")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    exposure = tables["player_exposure"]
    for ax, role, color in zip(axes, ("batting", "bowling"), ("#d74b86", "#276b96")):
        sub = exposure[exposure.role.eq(role)]
        ax.hist(sub.pressure_matches, bins=[0, 1, 3, 5, 8, 12, 20, 35, 60, 100, 200], color=color, alpha=.85)
        ax.axvline(8, color="#333333", linestyle="--", label="Initial minimum: 8")
        ax.set(title=f"{role.title()}: pressure-match evidence", xlabel="Distinct pressure matches", ylabel="Players")
        ax.legend(fontsize=9)
    save(fig, "05_player_evidence", "All observed primary players included, including those with zero retained opportunities. No performance ranking.")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    funnel = tables["sample_eligibility_funnel"]
    for ax, role, color in zip(axes, ("batting", "bowling"), ("#d74b86", "#276b96")):
        sub = funnel[funnel.role.eq(role)]
        bars = ax.barh(np.arange(len(sub)), sub.players, color=color)
        ax.set_yticks(np.arange(len(sub)), ["Observed", "Total sample", "Pressure sample", "8 pressure matches", "Ordinary evidence", "Effective sample"])
        ax.invert_yaxis()
        ax.bar_label(bars, padding=3)
        ax.set(title=f"{role.title()}: sample thresholds", xlabel="Players remaining", xlim=(0, sub.players.max() * 1.15))
    save(fig, "06_eligibility_funnel", "Thresholds are the initial registered plan values. Passing means evidence volume only; it is not a player recommendation.")

    fig, ax = plt.subplots(figsize=(10, 4.8))
    chases = tables["chase_outcomes"]
    for family, sub in chases.groupby("family"):
        ax.plot(sub.year, sub.chase_win_pct, "o-", label=family, color=COLORS[family])
        for r in sub.itertuples():
            ax.annotate(f"n={r.matches}", (r.year, r.chase_win_pct), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=8)
    ax.axhline(50, color="#999999", linestyle="--", linewidth=1)
    ax.set(title="Chasing-side win share in the supplied matches", xlabel="Year", ylabel="% of decisive, unadjusted matches")
    ax.set_xticks(sorted(chases.year.unique())); ax.legend(); ax.grid(axis="y", alpha=.2)
    save(fig, "07_chase_outcomes", "Uses recorded winning side and innings teams, not reconstructed targets. No adjustment for venue, opposition or selection.")

    fig, ax = plt.subplots(figsize=(10, 4.8))
    missing = tables["annotation_missingness"].pivot(index="family", columns="year", values="speed_zero_pct")
    image = ax.imshow(missing, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(missing.columns)), missing.columns)
    ax.set_yticks(range(len(missing)), missing.index)
    for i in range(len(missing)):
        for j in range(len(missing.columns)):
            value = missing.iloc[i, j]
            ax.text(j, i, "—" if np.isnan(value) else f"{value:.0f}%", ha="center", va="center", color="white" if value > 60 else "#222222")
    fig.colorbar(image, ax=ax, label="Speed recorded as zero (%)")
    ax.set(title="Speed annotation availability varies by cohort", xlabel="Year")
    save(fig, "08_annotation_quality", "All supplied deliveries within cutoff. Zero is a missingness diagnostic; speed is excluded from the initial model feature set.")
    pdf.close()
    return figures


def make_report(tables, events, ledger, audit, out, figures, config):
    d = events[events.eligible_proxy]
    pressure_count = int(d.pressure_proxy.sum())
    exposure = tables["player_exposure"]
    qualifies = exposure.groupby("role").meets_initial_sample_thresholds.sum()
    poor = exposure[exposure.meets_initial_sample_thresholds].groupby("role").weak_coverage_under_80pct.sum()
    primary_source = int((events.primary_scope & events.innings.isin([1, 2])).sum())
    pressure = tables["pressure_metrics"]
    funnel = tables["sample_eligibility_funnel"]
    sections = [
        "# EDA milestone — SupeRR Selector Season 2",
        f"Data cutoff: **{config['data_cutoff_inclusive']} inclusive**. This report uses the supplied files and a score-independent pressure proxy. Exact scores, chase targets, required run rates and full pressure labels remain unverified and null in the processed data.",
        "## Findings that affect implementation",
        f"- **{len(d):,} of {primary_source:,} primary normal-innings events retained ({100*len(d)/primary_source:.2f}%)**, from {d.match_id.nunique():,} matches and {len(ledger[ledger.eligible_proxy]):,} innings. Some matches contribute only one innings. Retention can vary by player and competition.",
        f"- **{pressure_count:,} events ({100*pressure_count/len(d):.2f}%) are late/collapse proxy pressure.** This already exceeds the requested 20–30% range; the registered thresholds were preserved. Tight-chase pressure cannot yet be evaluated as a verified feature.",
        f"- **{int(qualifies.get('batting', 0))} batters and {int(qualifies.get('bowling', 0))} bowlers meet the initial sample thresholds** on this proxy cohort. Of those, {int(poor.get('batting', 0))} batters and {int(poor.get('bowling', 0))} bowlers retain less than 80% of their supplied primary opportunities. These are evidence-volume diagnostics, not selected players.",
        f"- The lineup table has **{int(audit['inventory'].set_index('file').loc['playing_eleven.csv', 'duplicate_key_surplus'])} duplicate-key surplus rows**. They were preserved in a separate audit and never joined directly to deliveries.",
        "- Context adjustment is necessary: pressure is structurally concentrated in the late phase and collapse windows. Raw pressure/ordinary averages combine different innings states and player mixes; their difference does not establish that pressure caused a performance change.",
        "## 1. Population, joins and exclusions",
        "Raw files are immutable. Competition and match joins enforce many-to-one cardinality. Player identity uses IDs; name aliases are retained. Lineup rows remain separate because they contain roster entries, substitutes and duplicate keys.",
        markdown_table(tables["retention_by_year_family"], ["year", "family", "source_events", "retained_events", "retained_pct"]),
        "Acceptance is evaluated per innings: normal innings, IPL/T20I, completed unadjusted match, known extra categories, contiguous event sequence, consistent legal-ball over structure, and no detected chasing wicket-margin conflict. Unknown extras invalidate that innings' reconstructed legal-ball history. Super overs, rain/revision cases and no-result matches remain in the audit. Other T20 is an explicitly separate cohort.",
        "## 2. What the rates mean",
        "**Recorded runs per 100 non-wide opportunities** uses the supplied `runs` field. It is an analytical rate, pending confirmation of the run field's meaning. Non-wide opportunities include no-balls. **Zero recorded-run percentage** includes events with extra runs absent from `runs`; it is not a team dot-ball percentage. Boundary measures use supplied four/six flags. **Bowler wickets per 100 attempts** excludes run-outs, retirement and obstruction; attempts include illegal deliveries. No figure here is labelled official economy or official batting strike rate.",
        "## 3. Phase, innings and pressure patterns",
        markdown_table(pressure, ["pressure_proxy", "delivery_events", "batting_opportunities", "recorded_runs_per_100_opportunities", "boundary_pct", "bowler_wickets_per_100_attempts"]),
        "The pressure proxy is `late OR collapse`: overs 16–20, or two wickets in the preceding 12 legal-ball positions, or at least four wickets already lost in overs 1–10. Every state uses preceding events. The early collapse clause ends after over 10. All late-phase events are pressure by definition, so the late phase has no ordinary comparison group. This lack of overlap must be considered when estimating an individual player's pressure change.",
        "## 4. Whole-match uncertainty for descriptive aggregates",
        "Intervals below are the 10th–90th percentiles from 200 debug-stage bootstrap resamples of entire matches, sampled jointly for both pressure groups. The final ranking stage retains the approved 1,000 match resamples and approximately 20 upstream-model variants. These descriptive intervals do not correct selection or context confounding.",
        markdown_table(tables["pressure_metric_uncertainty"], ["metric", "group", "estimate", "p10", "p90"]),
        "## 5. Player evidence and coverage",
        markdown_table(funnel),
        "Initial eligibility: at least 300 batting opportunities/240 bowling attempts; 75/60 pressure opportunities; pressure in eight matches; ordinary evidence in five matches and 100 opportunities; recency-weight concentration effective count at least 40. Recency half-life is 730 days from the frozen cutoff. The effective count is a concentration diagnostic, not an independent-ball sample size. All player rows are exported in ID order without a performance leaderboard.",
        "The coverage denominator is all supplied IPL/T20I normal-innings opportunities for that role, including those excluded for quality or outcome. Coverage loss must be examined before interpreting a low rating. Match-block sufficient statistics are saved for later bootstrap analysis.",
        "## 6. What we can currently say about chasing",
        markdown_table(tables["chase_outcomes"], ["year", "family", "matches", "chase_wins", "chase_win_pct"]),
        "This table uses the recorded winner and the second-innings team for decisive, unadjusted matches. It does not require scores, so it is available now. It describes the supplied matches only; it cannot establish a causal advantage to chasing. Required-rate curves, target difficulty, close-chase success and win-probability training remain gated on verified event-level scores.",
        "## 7. Feature contracts and the next gate",
        "`data/processed/score_independent_states.parquet` preserves every source delivery with separate quality and scope flags. Accepted rows have pre-event legal balls, wickets, recent wicket counts, phase and proxy-pressure reasons. Excluded innings have null reconstructed states. `score_before`, `chase_target`, `required_run_rate`, `tight_chase` and `pressure_full` are deliberately null, and `mode_a_ready` is false.",
        "A separate `preball_features.parquet` contains only the allowlisted accepted pre-event features; delivery outcomes are stored separately. No winner, final margin, current runs/wicket, shot or current delivery speed enters that feature table.",
        "Next gate: obtain a corrected scoring export/dictionary or carry out verified external event alignment. Then reconcile complete innings, quantify repaired coverage, and enable Mode A state features. The organiser question is prepared locally and remains unsent. Before ML, resolve the pressure-definition coverage and context-overlap issue using registered anonymous scenarios. The 70/30 level/change default and 50/50 registered variant remain fixed comparisons.",
        "## 8. Reproduce and inspect",
        "Run `rtk proxy .venv/bin/python -m rr_pressure eda`. Dependencies are locked in `uv.lock`. Run `rtk proxy .venv/bin/python -m unittest discover -s tests -v` for validation. The report manifest records source/config/code/output hashes, dependency versions, timing, counts and the random seed. The original reconciliation remains independently reproducible.",
        "Local artifacts: [chart pack](EDA_CHARTS.pdf), [table directory](tables), [manifest](manifest.json). These contain competition-derived data and remain private. EDA includes all dates through the frozen cutoff to describe coverage; no predictive model or player-ranking choice has been selected using 2026 outcomes.",
        "## Figures",
    ]
    for figure in figures:
        sections.append(f"![{figure.replace('_', ' ')}](figures/{figure}.png)")
    (out / "REPORT.md").write_text("\n\n".join(sections) + "\n")
