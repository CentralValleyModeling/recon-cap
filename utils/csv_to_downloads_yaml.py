
# csv_to_downloads_yaml_v2.py
# Convert a CSV to a YAML manifest for the Downloads page
# Field order:
#   title (first), id, description, category, planning_horizon, loc, slr, assumptions, box_link, filename, size, updated (optional)
#
# Usage:
#   python csv_to_downloads_yaml_v2.py input.csv output.yaml
#
import sys
import pandas as pd
import yaml
from datetime import datetime

EXPECTED_COLS = [
    "title", "id", "description", "category",
    "planning_horizon", "loc", "slr", "assumptions",
    "box_link", "filename", "size", "updated"
]

def norm_str(x):
    if x is None:
        return ""
    s = str(x).strip()
    return s

def norm_date(v):
    if v is None:
        return ""
    s = str(v).strip()
    if not s:
        return ""
    # Try a few common formats, else return as-is
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return s

def drop_empty_keys(d):
    # Remove keys that are empty string
    return {k: v for k, v in d.items() if v not in ("", None)}

def main(csv_path, yaml_path):
    df = pd.read_csv(csv_path)

    # Ensure all expected columns exist
    for col in EXPECTED_COLS:
        if col not in df.columns:
            df[col] = ""

    rows = []
    for _, r in df.iterrows():
        item = {
            # Keep this order exactly
            "title":          norm_str(r["title"]),
            "id":             norm_str(r["id"]),
            "description":    norm_str(r["description"]),
            "category":       norm_str(r["category"]),
            "planning_horizon": norm_str(r["planning_horizon"]),
            "loc":            norm_str(r["loc"]),
            "slr":            norm_str(r["slr"]),
            "assumptions":    norm_str(r["assumptions"]),
            "box_link":       norm_str(r["box_link"]),
            "filename":       norm_str(r["filename"]),
            "size":           norm_str(r["size"]),
            "updated":        norm_date(r["updated"]),
        }
        item = drop_empty_keys(item)
        rows.append(item)

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(rows, f, sort_keys=False, allow_unicode=True)

    print(f"Wrote {yaml_path} with {len(rows)} items.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python csv_to_downloads_yaml_v2.py input.csv output.yaml")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])