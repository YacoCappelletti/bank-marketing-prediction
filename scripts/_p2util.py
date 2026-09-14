"""Shared helpers for the Phase 2 business-analysis scripts.

Every question script produces the same trio of artifacts:
  - docs/json/p2_qNN_metrics.json
  - docs/snippets/p2_qNN_output.md
  - docs/images/p2_qNN_chart.png

G1 note: these scripts are strictly *descriptive* business analysis (aggregations,
response-rate comparisons, distributions). No predictive model is trained and no
modeling target is selected or ranked here.
"""

import _bootstrap  # noqa: F401

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import load_dataset, docs_json, docs_snippets, docs_path


def data():
    return load_dataset()


def pct(x, digits=2):
    return round(100.0 * float(x), digits)


def save_metrics(qid, payload):
    path = docs_json("{}_metrics.json".format(qid))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return path


def save_snippet(qid, lines):
    path = docs_snippets("{}_output.md".format(qid))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def save_chart(fig, qid):
    path = docs_path("images", "{}_chart.png".format(qid))
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return path


def md_table(header, rows):
    out = [
        "| " + " | ".join(str(h) for h in header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return out
