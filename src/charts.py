"""Figures for the notebook, write-up and video.
Palette (validated for colour-blind safety with the dataviz validator): as typed #B24E36, dictionary #D99A1E,
Qalaisyn #00909C; neutral greys for references. Every bar carries a direct value label."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

INK, MUTED, GRID = "#1B2433", "#5F6B7A", "#E4E8ED"
RAW, DICT, QAL, REF = "#B24E36", "#D99A1E", "#00909C", "#AEB6BF"
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
})

CONDS = [("test_tatoeba_cyr", "all", "Russian keyboard · everyday"),
         ("test_flores_cyr", "all", "Russian keyboard · news"),
         ("test_tatoeba_cyr-typos-15", "cyr-typos-15", "Russian keyboard + typos"),
         ("test_tatoeba", "all", "Latin · everyday"),
         ("test_tatoeba_typos-15", "typos-15", "Latin + typos"),
         ("test_tatoeba_unseen-habits", "unseen-habits", "Latin · unseen spellings")]


def title(fig, ax, t, sub):
    fig.text(0.012, 0.975, t, fontsize=15, weight="bold", color=INK, va="top")
    fig.text(0.012, 0.915, sub, fontsize=10.5, color=MUTED, va="top")


def rec(d, g, m):
    return (d[f"{g}|{m}"] - d[f"{g}|B0 raw chat"]) / (d[f"{g}|gold"] - d[f"{g}|B0 raw chat"]) * 100


def meaning_chart():
    chrf = json.loads((R / "translation_chrf.json").read_text())
    conds = [c for c in CONDS if c[0] in chrf]
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=170)
    fig.subplots_adjust(left=0.27, right=0.95, top=0.78, bottom=0.12)
    h = 0.36
    for i, (name, g, lab) in enumerate(conds):
        y = len(conds) - 1 - i
        d, q = rec(chrf[name], g, "B2 dictionary"), rec(chrf[name], g, "M2 Qalaisyn+typos")
        ax.barh(y + h / 2, d, h * 0.92, color=DICT)
        ax.barh(y - h / 2, q, h * 0.92, color=QAL)
        ax.text(d + 1, y + h / 2, f"{d:.0f}%", va="center", fontsize=10, color=INK)
        ax.text(q + 1, y - h / 2, f"{q:.0f}%", va="center", fontsize=10, color=INK, weight="bold")
    ax.set_yticks(range(len(conds)))
    ax.set_yticklabels([c[2] for c in conds][::-1])
    ax.set_xlim(0, 112)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("share of the meaning lost by the translator that comes back (chrF, held-out test data)")
    title(fig, ax, "Qalaisyn wins most where real messages are messy",
          "Meaning recovered after a dictionary lookup vs after Qalaisyn. 0% = message as typed, 100% = correct spelling.")
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=DICT), plt.Rectangle((0, 0), 1, 1, color=QAL)],
               labels=["Dictionary lookup", "Qalaisyn"], frameon=False, loc="upper right",
               bbox_to_anchor=(0.95, 0.86), ncol=2, fontsize=10)
    fig.savefig(FIG / "meaning.png")
    plt.close(fig)


def messages_chart():
    v = json.loads((R / "value.json").read_text(encoding="utf-8"))
    labels = [k for k in v]
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=170)
    fig.subplots_adjust(left=0.27, right=0.95, top=0.80, bottom=0.12)
    for i, k in enumerate(labels):
        y = len(labels) - 1 - i
        m = v[k]["messages_fully_right"]
        d, q = m["dictionary"] * 100, m["qalaisyn"] * 100
        ax.plot([d, q], [y, y], color=GRID, lw=6, solid_capstyle="round", zorder=1)
        ax.scatter([d], [y], s=110, color=DICT, zorder=3, edgecolor="white", linewidth=2)
        ax.scatter([q], [y], s=130, color=QAL, zorder=4, edgecolor="white", linewidth=2)
        lo, hi = m["diff_ci"]
        ax.text(min(d, q) - 2, y, f"{d:.0f}%", ha="right", va="center", fontsize=10, color=MUTED)
        ax.text(max(d, q) + 2, y, f"{q:.0f}%   (+{(q - d):.0f} pts, 95% CI +{lo * 100:.0f}…+{hi * 100:.0f})",
                ha="left", va="center", fontsize=10, color=INK)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels[::-1])
    ax.set_xlim(0, 125)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("messages restored with no mistake at all (held-out test data)")
    title(fig, ax, "A chatbot needs the whole message right",
          "Share of messages with every word correct: dictionary lookup (ochre) vs Qalaisyn (teal).")
    fig.savefig(FIG / "messages.png")
    plt.close(fig)


def system_chart(name="test_tatoeba_cyr", sub="Everyday sentences typed on a Russian keyboard"):
    d = json.loads((R / "translation_chrf.json").read_text())[name]
    keys = [("gold", "Correct spelling", REF), ("B0 raw chat", "As typed", RAW), ("B1 rules", "Letter rules", "#C9CFD6"),
            ("B2 dictionary", "Dictionary", DICT), ("M2 Qalaisyn+typos", "Qalaisyn", QAL)]
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=170)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.80, bottom=0.13)
    vals = [d[f"all|{k}"] for k, _, _ in keys]
    bars = ax.bar([l for _, l, _ in keys], vals, color=[c for _, _, c in keys], width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{v:.1f}", ha="center", fontsize=11, color=INK, weight="bold")
    ax.set_ylim(0, max(vals) * 1.15)
    ax.yaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0, colors=INK)
    ax.set_ylabel("translation quality (chrF)")
    lost = 1 - d["all|B0 raw chat"] / d["all|gold"]
    title(fig, ax, f"Typed as is, the translator loses {lost:.0%} of the meaning",
          f"{sub} · translator NLLB-200 · chrF vs professional English")
    fig.savefig(FIG / f"system_{name}.png")
    plt.close(fig)


def confidence_chart():
    c = json.loads((R / "confidence.json").read_text(encoding="utf-8"))
    rows = [("test_tatoeba_cyr", "Russian keyboard"), ("test_tatoeba", "Latin chat")]
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=170)
    fig.subplots_adjust(left=0.2, right=0.95, top=0.76, bottom=0.15)
    for i, (n, lab) in enumerate(rows):
        a = c[n]["at_threshold"]
        y = 1 - i
        f, e = a["flagged_share"] * 100, a["errors_caught"] * 100
        ax.barh(y + 0.18, f, 0.32, color=REF)
        ax.barh(y - 0.18, e, 0.32, color=QAL)
        ax.text(f + 1, y + 0.18, f"{f:.0f}% of all words are shown as suggestions", va="center", fontsize=10, color=MUTED)
        ax.text(e + 1, y - 0.18, f"{e:.0f}% of Qalaisyn's mistakes are among them", va="center", fontsize=10,
                color=INK, weight="bold")
    ax.set_yticks([1, 0])
    ax.set_yticklabels([r[1] for r in rows])
    ax.set_xlim(0, 115)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("%")
    title(fig, ax, "It asks rarely, and that is where its mistakes are",
          "Words below 90% confidence become suggestions instead of silent changes (held-out test data).")
    fig.savefig(FIG / "confidence.png")
    plt.close(fig)


def letters_chart():
    a = json.loads((R / "analysis.json").read_text(encoding="utf-8"))
    items = sorted(((l, v["error_rate"] * 100) for l, v in a["letters"].items() if v["n"] > 500), key=lambda x: -x[1])
    fig, ax = plt.subplots(figsize=(9, 3.9), dpi=170)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.76, bottom=0.12)
    cols = [RAW if i < 2 else QAL for i in range(len(items))]
    bars = ax.bar([l for l, _ in items], [v for _, v in items], color=cols, width=0.62)
    for b, (_, v) in zip(bars[:4], items[:4]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.05, f"{v:.1f}%", ha="center", fontsize=9.5, color=INK)
    ax.yaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0, colors=INK, labelsize=13)
    ax.set_ylabel("% restored wrongly")
    title(fig, ax, "Hardest letters: ң/н and і/и",
          "Both choices are often real words, so only context can decide.")
    fig.savefig(FIG / "letters.png")
    plt.close(fig)


if __name__ == "__main__":
    meaning_chart()
    if (R / "value.json").exists():
        messages_chart()
    system_chart()
    system_chart("test_tatoeba", "Everyday sentences typed in Latin letters")
    confidence_chart()
    letters_chart()
    print("figures:", sorted(p.name for p in FIG.iterdir()))
