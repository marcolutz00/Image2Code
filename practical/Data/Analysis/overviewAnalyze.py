import os
import json
from pathlib import Path
from statistics import mean
from collections import Counter
import matplotlib.pyplot as plt


CURR_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_INSIGHTS_DIR = os.path.join(CURR_DIR, '..', 'Input', 'insights')

def analyze_overview_files(directory: str) -> None:
    """
    Liest alle overview_*.json-Dateien in *directory*,
    zeigt eine Tabelle mit IR / IW-IR (automatic & manual)
    und erstellt einen Box-Plot, der die Verteilung illustriert.
    """

    # ── 1. Daten einsammeln ─────────────────────────────────────────────
    rows = []
    for fname in sorted(os.listdir(directory)):
        number = fname.split("_")[1]
        number = number.split(".")[0]
        if number.isdigit() and int(number) < 29:
            continue
        if fname.startswith("overview_") and fname.endswith(".json"):
            with open(Path(directory) / fname, encoding="utf-8") as fh:
                data = json.load(fh)

            rows.append({
                "file"        : fname,
                "auto_status" : data["overall_status"]["automatic"],
                "manual_status":data["overall_status"]["manual"],
                "auto_ir"     : data["benchmark"]["automatic_ir"],
                "auto_iwir"   : data["benchmark"]["automatic_iw-ir"],
                "manual_ir"   : data["benchmark"]["manual_ir"],
                "manual_iwir" : data["benchmark"]["manual_iw-ir"],
            })

    if not rows:
        print("⚠️  Keine overview_*.json-Dateien gefunden.\n")
        return

    # ── 2. Tabelle drucken ─────────────────────────────────────────────
    header = (
        "File".ljust(20)
        + "Auto-Status".ljust(14)
        + "Manual-Status".ljust(15)
        + "Auto IR".rjust(10)
        + "Auto IW-IR".rjust(14)
        + "Manual IR".rjust(12)
        + "Manual IW-IR".rjust(16)
    )
    sep = "-" * len(header)
    print(header)
    print(sep)
    for r in rows:
        print(
            f"{r['file']:<20}"
            f"{r['auto_status']:<14}"
            f"{r['manual_status']:<15}"
            f"{r['auto_ir']:>10.4f}"
            f"{r['auto_iwir']:>14.4f}"
            f"{r['manual_ir']:>12.4f}"
            f"{r['manual_iwir']:>16.4f}"
        )

    # ── 3. Zusammenfassung ─────────────────────────────────────────────
    auto_status_cnt   = Counter(r["auto_status"]   for r in rows)
    manual_status_cnt = Counter(r["manual_status"] for r in rows)

    print("\n── Zusammenfassung ──")
    print(f"Dateien gesamt: {len(rows)}")
    print(f"Ø Automatic IR     : {mean(r['auto_ir']   for r in rows):.4f}")
    print(f"Ø Automatic IW-IR  : {mean(r['auto_iwir'] for r in rows):.4f}")
    print(f"Ø Manual IR        : {mean(r['manual_ir']   for r in rows):.4f}")
    print(f"Ø Manual IW-IR     : {mean(r['manual_iwir'] for r in rows):.4f}")
    print("\nStatus-Verteilung (Automatic):", dict(auto_status_cnt))
    print("Status-Verteilung (Manual)   :", dict(manual_status_cnt))

    # ── 4. Box-Plot erstellen ──────────────────────────────────────────
    plt.figure(figsize=(8, 6))
    plt.boxplot(
        [
            [r["auto_ir"]    for r in rows],
            [r["auto_iwir"]  for r in rows],
            [r["manual_ir"]  for r in rows],
            [r["manual_iwir"]for r in rows],
        ],
        labels=["Auto IR", "Auto IW-IR", "Manual IR", "Manual IW-IR"],
        showmeans=True,             # Mittelwert als Raute
    )
    plt.ylabel("Rate")
    plt.title("Verteilung der Benchmarks (IR & IW-IR)")
    plt.grid(axis="y")
    plt.tight_layout()
    plt.show()


# analyze_overview_files(r"..\Input\insights")
if __name__ == "__main__":
    # Beispielaufruf:
    analyze_overview_files(INPUT_INSIGHTS_DIR)