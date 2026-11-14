"""Exportable figures for the saved-prediction review."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def make_review_figures(pairs, exposure, out):
    targets = ["bat_runs", "bowl_runs", "striker_wicket", "bowler_wicket"]
    plt.rcParams.update({"font.size":10, "axes.spines.top":False, "axes.spines.right":False})
    with PdfPages(out / "INSTABILITY_REVIEW.pdf") as pdf:
        fig, axes = plt.subplots(2,2,figsize=(11,8))
        for ax,target in zip(axes.flat, targets):
            g=pairs.loc[pairs.target.eq(target)]
            for alert,color,label in [(False,"#939da8","No fold alert"),(True,"#c65870","At least one fold alert")]:
                part=g.loc[g.any_alert.eq(alert)]
                ax.scatter(100*part.mean_bias_0,100*part.mean_bias_1,color=color,label=label,s=30)
            ax.axhline(0,color="gray",linewidth=.7)
            ax.axvline(0,color="gray",linewidth=.7)
            ax.set(title=target.replace("_"," "),xlabel="Fold 0 bias per 100 opportunities",ylabel="Fold 1 bias per 100 opportunities")
            ax.legend(fontsize=8)
        fig.suptitle("Opposing conditional errors can cancel in pooled predictions")
        fig.tight_layout(rect=(0,0,1,.96))
        pdf.savefig(fig)
        fig.savefig(out / "opposing_errors.png",dpi=150)
        plt.close(fig)
        fig,axes=plt.subplots(1,2,figsize=(11,5))
        for ax,role in zip(axes,["batting","bowling"]):
            g=exposure.loc[exposure.resolution.eq("family_phase") & exposure.exposure.eq("pressure") & exposure.role.eq(role)].copy()
            labels=g.family+" "+g.phase
            positions=list(range(len(g)))
            ax.barh(positions,100*g.either_fold_alert_fraction,color="#d6c6da",label="Context alerted in either fold")
            ax.barh(positions,100*g.own_fold_alert_fraction,color="#447f98",label="Actual fold alerted")
            ax.set_yticks(positions,labels)
            ax.set(title=role,xlabel="Pressure opportunities affected (%)",xlim=(0,100))
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5,.92), ncol=2, fontsize=9)
        fig.suptitle("Exposure to run-or-wicket alerts, counting each role opportunity once")
        fig.tight_layout(rect=(0,0,1,.85))
        pdf.savefig(fig)
        fig.savefig(out / "pressure_exposure.png",dpi=150)
        plt.close(fig)
