# pages/downloads.py
# Dash multipage "Downloads" page listing references and model packages stored on Box.
# - Uses a YAML/CSV manifest
# - Card and Table views
# - Search, category + tag filters, sort
# - Download-only links (no preview)
# - Filetype icons based on filename extension

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import dash
from dash import html, dcc, dash_table, Input, Output, State, callback

dash.register_page(__name__, path="/downloads", name="Downloads")

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
# Path to your manifest file (.yaml/.yml or .csv)
# Expected fields:
# - title (str)            : display name
# - description (str)      : short text
# - category (str)         : e.g., "Reference" or "Model"
# - tags (list[str] | str) : list or comma-separated
# - box_link (str)         : Box shared link (https://*.box.com/s/<id>)
# - filename (str, opt)    : nice filename (used to detect icon)
# - size (str, opt)        : e.g., "23 MB"
# - updated (str/date, opt): "YYYY-MM-DD" preferred
MANIFEST_PATH = os.environ.get("DOWNLOADS_MANIFEST", "data/downloads_manifest.yaml")

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _coerce_tags(v) -> List[str]:
    # Normalize tags into a list[str]
    if v is None:
        return []
    # NaN as float
    if isinstance(v, float) and pd.isna(v):
        return []
    # Already a python list
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    # Numpy array or Series
    if isinstance(v, (np.ndarray, pd.Series)):
        return [str(x).strip() for x in v.tolist() if str(x).strip()]
    # Fallback: comma-separated string
    return [t.strip() for t in str(v).split(",") if t.strip()]

def _to_download_url(box_link: str) -> str:
    # Append ?download=1 to force download
    sep = "&" if "?" in box_link else "?"
    return f"{box_link}{sep}download=1"

def _ext(filename: str | None) -> str:
    if not filename:
        return ""
    name = str(filename)
    # Handle .tar.gz, .tar.bz2, etc
    lower = name.lower()
    if lower.endswith(".tar.gz"):
        return ".tar.gz"
    if lower.endswith(".tar.bz2"):
        return ".tar.bz2"
    return Path(lower).suffix

def _file_icon_from_ext(ext: str) -> str:
    # Minimal, readable emoji icon set; expand as you wish.
    mapping = {
        ".pdf": "📄",
        ".doc": "📝",
        ".docx": "📝",
        ".rtf": "📝",
        ".txt": "🗒️",
        ".csv": "🧾",
        ".tsv": "🧾",
        ".json": "🧾",
        ".yaml": "🧾",
        ".yml": "🧾",
        ".xls": "📊",
        ".xlsx": "📊",
        ".xlsm": "📊",
        ".ppt": "📽️",
        ".pptx": "📽️",
        ".zip": "📦",
        ".7z": "📦",
        ".rar": "📦",
        ".tar": "📦",
        ".tar.gz": "📦",
        ".tar.bz2": "📦",
    }
    return mapping.get(ext, "🗂️")

def _file_icon_for_item(item: Dict[str, Any]) -> str:
    ext = _ext(item.get("filename"))
    return _file_icon_from_ext(ext)

# -----------------------------------------------------------------------------
# Data loading
# -----------------------------------------------------------------------------
def load_manifest(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        # Fallback sample so page renders even if manifest is missing
        data = [
            {
                "title": "DCR 2025 – Modeling Assumptions (Appendix A)",
                "description": "Reference document used by the team.",
                "category": "Reference",
                "tags": ["DCR 2025", "Assumptions"],
                "box_link": "https://box.com/s/EXAMPLE_REF_ID",
                "filename": "DCR2025_AppendixA.pdf",
                "size": "12 MB",
                "updated": "2025-07-25",
            },
            {
                "title": "CalSim3 – SJC Study Model Package",
                "description": "Zipped model inputs/outputs for the San Joaquin Conveyance study.",
                "category": "Model",
                "tags": ["CalSim3", "SJC"],
                "box_link": "https://box.com/s/EXAMPLE_MODEL_ID",
                "filename": "SJC_CalSim3_Model_2025-08-15.zip",
                "size": "1.2 GB",
                "updated": "2025-08-15",
            },
        ]
        df = pd.DataFrame(data)
    else:
        if p.suffix.lower() in (".yaml", ".yml"):
            import yaml
            content = yaml.safe_load(p.read_text(encoding="utf-8"))
            rows = list(content.values()) if isinstance(content, dict) else content
            df = pd.DataFrame(rows)
        elif p.suffix.lower() == ".csv":
            df = pd.read_csv(p)
        else:
            raise ValueError("Manifest must be .yaml/.yml or .csv")

    # Normalize columns
    for col in ["title", "description", "category", "filename", "size", "box_link"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")

    # Tags to list[str]
    if "tags" not in df.columns:
        df["tags"] = [[] for _ in range(len(df))]
    else:
        df["tags"] = df["tags"].apply(_coerce_tags)

    # Updated -> datetime (keep original for display later)
    df["updated"] = pd.to_datetime(df.get("updated", pd.NaT), errors="coerce")

    # Download URL
    df["download_url"] = df["box_link"].apply(_to_download_url)

    return df

DF = load_manifest(MANIFEST_PATH)

def _all_tags(df: pd.DataFrame) -> List[str]:
    tags = set()
    for ts in df["tags"]:
        tags.update(ts)
    return sorted(t for t in tags if t)

# -----------------------------------------------------------------------------
# Layout
# -----------------------------------------------------------------------------
def layout():
    categories = ["All"] + sorted([c for c in DF["category"].dropna().unique().tolist() if c])
    tag_options = [{"label": t, "value": t} for t in _all_tags(DF)]

    return html.Div(
        className="p-4",
        children=[
            html.H1("Downloads", className="text-2xl mb-2"),
            html.P(
                "Browse and download references and model packages stored in our Box repository.",
                className="mb-4",
            ),

            # Controls
            html.Div(
                className="grid gap-3 md:grid-cols-4 mb-4",
                children=[
                    dcc.Input(
                        id="dl-search",
                        type="text",
                        placeholder="Search title, description, filename…",
                        debounce=True,
                        className="w-full",
                    ),
                    dcc.Dropdown(
                        id="dl-category",
                        options=[{"label": c, "value": c} for c in categories],
                        value="All",
                        clearable=False,
                        className="w-full",
                    ),
                    dcc.Dropdown(
                        id="dl-tags",
                        options=tag_options,
                        multi=True,
                        placeholder="Filter by tags",
                        className="w-full",
                    ),
                    dcc.Dropdown(
                        id="dl-sort",
                        options=[
                            {"label": "Newest", "value": "newest"},
                            {"label": "Oldest", "value": "oldest"},
                            {"label": "Title A–Z", "value": "title_az"},
                            {"label": "Title Z–A", "value": "title_za"},
                        ],
                        value="newest",
                        clearable=False,
                        className="w-full",
                    ),
                ],
            ),

            dcc.Tabs(
                id="dl-view-mode",
                value="cards",
                children=[
                    dcc.Tab(label="Card view", value="cards"),
                    dcc.Tab(label="Table view", value="table"),
                ],
            ),

            html.Div(id="dl-content", className="mt-4"),

            # Hidden store of raw data (strings only for serialization)
            dcc.Store(
                id="dl-store",
                data=DF.assign(
                    updated=DF["updated"].dt.strftime("%Y-%m-%d").fillna(""),
                ).to_dict("records"),
            ),
        ],
    )

layout = layout  # Dash expects a callable or object

# -----------------------------------------------------------------------------
# Rendering helpers
# -----------------------------------------------------------------------------
def _filter_sort_records(records: List[Dict[str, Any]], q: str, category: str, tags: List[str], sort: str):
    df = pd.DataFrame(records)

    # Filter: search
    if q:
        qlow = q.strip().lower()
        mask = (
            df["title"].str.lower().str.contains(qlow, na=False)
            | df["description"].str.lower().str.contains(qlow, na=False)
            | df["filename"].str.lower().str.contains(qlow, na=False)
        )
        df = df[mask]

    # Filter: category
    if category and category != "All":
        df = df[df["category"] == category]

    # Filter: tags (AND)
    if tags:
        df = df[df["tags"].apply(lambda ts: all(t in ts for t in tags))]

    # Sort
    if sort == "newest":
        df["_udt"] = pd.to_datetime(df["updated"], errors="coerce")
        df = df.sort_values(by=["_udt", "title"], ascending=[False, True])
    elif sort == "oldest":
        df["_udt"] = pd.to_datetime(df["updated"], errors="coerce")
        df = df.sort_values(by=["_udt", "title"], ascending=[True, True])
    elif sort == "title_az":
        df = df.sort_values(by="title", ascending=True)
    elif sort == "title_za":
        df = df.sort_values(by="title", ascending=False)

    return df.drop(columns=[c for c in ["_udt"] if c in df.columns])

def _category_badge(category: str) -> html.Span:
    return html.Span(
        category or "Uncategorized",
        className="px-2 py-0.5 text-xs rounded bg-gray-100 border mr-2",
    )

def _card(item: Dict[str, Any]) -> html.Div:
    icon = _file_icon_for_item(item)
    subtitle_bits = []
    if item.get("filename"):
        subtitle_bits.append(item["filename"])
    if item.get("size"):
        subtitle_bits.append(item["size"])
    if item.get("updated"):
        subtitle_bits.append(f"Updated {item['updated']}")
    subtitle = " • ".join(subtitle_bits)

    return html.Div(
        className="rounded-2xl shadow p-4 border",
        children=[
            html.Div(
                className="flex items-start justify-between gap-3",
                children=[
                    html.Div(
                        children=[
                            html.H3(
                                className="text-lg font-semibold mb-1 flex items-center gap-2",
                                children=[html.Span(icon, className="text-xl"), item.get("title", "(Untitled)")]
                            ),
                            html.Div(
                                className="text-sm text-gray-600 mb-1 flex items-center gap-2",
                                children=[_category_badge(item.get("category", "")), subtitle],
                            ),
                            html.Div(
                                className="text-sm mb-3",
                                children=item.get("description", ""),
                            ),
                        ]
                    ),
                    html.Div(
                        className="flex flex-col gap-2 min-w-[140px]",
                        children=[
                            html.A(
                                "Download",
                                href=item["download_url"],
                                target="_blank",
                                className="px-3 py-2 rounded-xl bg-blue-600 text-center hover:bg-blue-700",
                            ),
                        ],
                    ),
                ],
            )
        ],
    )

def _cards_grid(df: pd.DataFrame) -> html.Div:
    cards = [_card(dict(r)) for _, r in df.iterrows()]
    return html.Div(className="grid gap-4 md:grid-cols-2 xl:grid-cols-3", children=cards or [html.Div("No results.")])

def _table(df: pd.DataFrame) -> html.Div:
    tdf = df.copy()
    # Flatten tags and compute icon+title label
    tdf["tags"] = tdf["tags"].apply(lambda ts: ", ".join(ts))
    # Emoji + title combined column
    def title_with_icon(row):
        icon = _file_icon_from_ext(_ext(row.get("filename", "")))
        return f"{icon} {row.get('title','(Untitled)')}"
    tdf["Title"] = tdf.apply(title_with_icon, axis=1)

    tdf = tdf[[
        "Title", "category", "tags", "filename", "size", "updated", "download_url"
    ]].rename(columns={
        "category": "Category",
        "tags": "Tags",
        "filename": "File",
        "size": "Size",
        "updated": "Updated",
        "download_url": "Download",
    })

    # Convert the download URL into markdown link
    tdf["Download"] = tdf["Download"].apply(lambda u: f"[Download]({u})")

    return html.Div([
        dash_table.DataTable(
            id="dl-table",
            data=tdf.to_dict("records"),
            columns=[
                {"name": c, "id": c, "presentation": "markdown" if c in ["Download"] else "input"}
                for c in tdf.columns
            ],
            page_size=12,
            sort_action="native",
            filter_action="native",
            style_cell={"textAlign": "left", "whiteSpace": "normal", "height": "auto"},
            style_table={"overflowX": "auto"},
            markdown_options={"link_target": "_blank"},
        )
    ])

# -----------------------------------------------------------------------------
# Callback
# -----------------------------------------------------------------------------
@callback(
    Output("dl-content", "children"),
    Input("dl-store", "data"),
    Input("dl-search", "value"),
    Input("dl-category", "value"),
    Input("dl-tags", "value"),
    Input("dl-sort", "value"),
    Input("dl-view-mode", "value"),
)
def render_content(records, q, category, tags, sort, view_mode):
    df = _filter_sort_records(records, q or "", category or "All", tags or [], sort or "newest")

    if view_mode == "table":
        return _table(df)

    # Card view (uses raw URLs)
    return _cards_grid(df)
