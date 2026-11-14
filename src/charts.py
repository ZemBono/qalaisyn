"""Make the figures for the write-up, notebook and video."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
chrf = json.loads((R / "translation_chrf.json").read_text())

INK, MUTED, BAD, GOOD, MID = "#1f2937", "#9ca3af", "#e4572e", "#0f9d74", "#f2b134"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#d1d5db", "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})


def main_chart(name="test_tatoeba", title="Everyday sentences (Tatoeba, 623 sentences x 4 writing styles)"):
    d = chrf[name]
    labels = ["Proper\nKazakh text", "Chat text\nas typed", "Simple\nletter rules", "Dictionary\nlookup", "Qalaisyn"]
    keys = ["gold", "B0 raw chat", "B1 rules", "B2 dictionary", "M2 Qalaisyn+typos"]
    vals = [d[f"all|{k}"] for k in keys]
    colors = [MUTED, BAD, MID, MID, GOOD]
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=160)
    bars = ax.bar(labels, vals, color=colors, width=0.62)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}", ha="center", fontsize=12, color=INK, weight="bold")
    lost = vals[0] - vals[1]
    rec = (vals[4] - vals[1]) / lost
    ax.annotate("", xy=(1, vals[0]), xytext=(1, vals[1] + 4), arrowprops=dict(arrowstyle="<->", color=BAD, lw=1.6))
    ax.text(1.12, (vals[0] + vals[1]) / 2, f"{lost / vals[0]:.0%} of the\nmeaning lost", color=BAD, fontsize=10, va="center")
    ax.set_ylabel("Translation quality (chrF vs. professional English)")
    ax.set_ylim(0, max(vals) * 1.22)
    ax.set_title(f"Qalaisyn recovers {rec:.0%} of the meaning lost in chat-style Kazakh", fontsize=14, color=INK,
                 loc="left", weight="bold")
    ax.text(0, max(vals) * 1.13, title + " · translator: NLLB-200", fontsize=9.5, color="#6b7280")
    fig.tight_layout()
    fig.savefig(FIG / f"main_{name}.png")
    plt.close(fig)
    return rec


def messy_chart():
    conds = [("test_tatoeba", "all", "Clean chat"), ("test_tatoeba_typos-5", "typos-5", "5% typos"),
             ("test_tatoeba_typos-15", "typos-15", "15% typos"),
             ("test_tatoeba_unseen-habits", "unseen-habits", "Unseen spellings\n(ae, kh, kk)")]
    models = [("B0 raw chat", "Chat as typed", BAD), ("B2 dictionary", "Dictionary", MID),
              ("M1 Qalaisyn", "Qalaisyn (context only)", "#7cc6b0"), ("M2 Qalaisyn+typos", "Qalaisyn + typo search", GOOD)]
    fig, ax = plt.subplots(figsize=(9.5, 5.4), dpi=160)
    w = 0.2
    for j, (k, lab, col) in enumerate(models):
        xs, ys = [], []
        for i, (name, grp, _) in enumerate(conds):
            if name in chrf:
                xs.append(i + (j - 1.5) * w)
                ys.append(chrf[name][f"{grp}|{k}"])
        ax.bar(xs, ys, width=w, color=col, label=lab)
    gold = chrf["test_tatoeba"]["all|gold"]
    ax.axhline(gold, color=MUTED, ls="--", lw=1)
    ax.text(3.45, gold + 0.8, "proper Kazakh", color="#6b7280", fontsize=9, ha="right")
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels([c[2] for c in conds])
    ax.set_ylabel("Translation quality (chrF)")
    ax.set_title("Real messages are messy: typo search keeps the meaning", loc="left", fontsize=14, weight="bold", color=INK)
    ax.legend(frameon=False, ncol=4, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    ax.set_ylim(0, 66)
    fig.tight_layout()
    fig.savefig(FIG / "messy_messages.png")
    plt.close(fig)


def letters_chart():
    a = json.loads((R / "analysis.json").read_text(encoding="utf-8"))
    items = sorted(((l, v["error_rate"]) for l, v in a["letters"].items() if v["n"] > 500), key=lambda x: -x[1])
    fig, ax = plt.subplots(figsize=(8, 4), dpi=160)
    ax.bar([l for l, _ in items], [v * 100 for _, v in items], color=[BAD if v > 0.012 else GOOD for _, v in items])
    ax.set_ylabel("% of this letter restored wrongly")
    ax.set_title("Hardest letters: ң/н and і/ы/и", loc="left", fontsize=13, weight="bold", color=INK)
    fig.tight_layout()
    fig.savefig(FIG / "letters.png")
    plt.close(fig)


if __name__ == "__main__":
    print("recovered tatoeba", main_chart())
    print("recovered flores", main_chart("test_flores", "News-style sentences (FLORES-200, 300 sentences x 4 writing styles)"))
    messy_chart()
    letters_chart()
    print("figures:", [p.name for p in FIG.iterdir()])
