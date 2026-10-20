#!/usr/bin/env python3
"""Dev utility: convert Default_descriptions.ods (authored by hand in a
spreadsheet, one column per suit / one row per value) into
default_description.md, the markdown table format the backend seeds from
(see backend/app/default_descriptions.py).

Usage:
    python3 scripts/ods_to_default_descriptions.py \
        [Default_descriptions.ods] [default_description.md]

Re-run any time the spreadsheet is updated; it fully regenerates the
"Valeurs" table in the .md file (joker lines, if already present in the
.md file, are preserved as-is).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SUIT_ORDER = ["Coeur", "Careau", "Trèfle", "Pic", "Étoile"]  # matches the .ods headers
SUIT_DISPLAY = ["Cœur", "Carreau", "Trèfle", "Pique", "Star"]  # matches deck.py labels
VALUE_ORDER = ["3", "4", "5", "6", "7", "8", "9", "10", "V", "D", "R"]


def main() -> None:
    ods_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "Default_descriptions.ods"
    md_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "default_description.md"

    sheets = pd.read_excel(ods_path, engine="odf", sheet_name=None)
    df = next(iter(sheets.values()))
    df = df.set_index(df.columns[0])
    df.index = df.index.map(lambda v: str(v).strip())

    rows = []
    rows.append("| Valeur | " + " | ".join(SUIT_DISPLAY) + " |")
    rows.append("|---|" + "---|" * len(SUIT_DISPLAY))
    for value in VALUE_ORDER:
        cells = [value]
        for suit_col in SUIT_ORDER:
            cell = ""
            if value in df.index and suit_col in df.columns:
                raw = df.loc[value, suit_col]
                if pd.notna(raw):
                    cell = str(raw).strip()
            cells.append(cell)
        rows.append("| " + " | ".join(cells) + " |")

    table_md = "\n".join(rows)

    jokers_md = (
        "## Jokers\n\n"
        + "\n".join(f"{i}. " for i in range(1, 7))
    )

    if md_path.exists() and "## Jokers" in md_path.read_text(encoding="utf-8"):
        jokers_md = md_path.read_text(encoding="utf-8").split("## Jokers", 1)[1]
        jokers_md = "## Jokers" + jokers_md

    content = (
        "# Descriptions par défaut\n\n"
        "Ce fichier sert à pré-remplir la description de chaque carte au premier "
        "démarrage de l'application (voir Spec.md). Toute description déjà "
        "modifiée depuis l'application ne sera jamais écrasée par ce fichier.\n\n"
        f"{table_md}\n\n"
        f"{jokers_md}\n"
    )
    md_path.write_text(content, encoding="utf-8")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
