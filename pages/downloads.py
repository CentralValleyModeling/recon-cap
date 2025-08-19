# pages/downloads.py
# Dash multipage "Downloads" page listing references and model packages stored on Box.
# - Uses a YAML/CSV manifest
# - Card and Table views
# - Search, category filter
# - Download-only links (no preview)
# - Filetype icons based on filename extension
# - Compact meta line on cards: "YYYY • LoC 50% • SLR 15cm • Maintain"
# - No sorting dropdown

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import dash
from dash import html, dcc, dash_table, Input, Output, callback

dash.register_page(__name__, path="/downloads", name="Downloads")

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
MANIFEST_PATH = os.environ.get("DOWNLOADS_MANIFEST", "data/downloads_manifest.yaml")

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _to_download_url(box_link: str) -> str:
    sep = "&" if isinstance(box_link, str) and "?" in box_link else "?"
    return f"{box_link}{sep}download=1" if box_link else ""

def _ext(filename: str | None) -> str:
    if not filename:
        return ""
    lower = str(filename).lower()
    if lower.endswith(".tar.gz"):
        return ".tar.gz"
    if lower.endswith(".tar.bz2"):
        return ".tar.bz2"
    return Path(lower).suffix

def _file_icon_from_ext(ext: str) -> str:
    mapping = {
        ".pdf": "📄", ".doc": "📝", ".docx": "📝", ".rtf": "📝", ".txt": "🗒️",
        ".csv": "🧾", ".tsv": "🧾", ".json": "🧾", ".yaml": "🧾", ".yml": "🧾",
        ".xls": "📊", ".xlsx": "📊", ".xlsm": "📊",
        ".ppt": "📽️", ".pptx": "📽️",
        ".zip": "📦", ".7z": "📦", ".rar": "📦", ".tar": "📦", ".tar.gz": "📦", ".tar.bz2": "📦",
    }
    return mapping.get(ext, "🗂️")

def _file_icon_for_item(item: Dict[str, Any]) -> str:
    return _file_icon_from_ext(_ext(item.get("filename")))

def _meta_line(item: Dict[str, Any]) -> str:
    bits: List[str] = []
    yr = (item.get("planning_horizon") or "").strip()
    loc = (item.get("loc") or "").strip()
    slr = (item.get("slr") or "").strip()
    asm = (item.get("assumptions") or "").strip()
    if yr:
        bits.append(yr)
    if loc:
        bits.append(f"LoC {loc}%") if loc.replace("%", "").isdigit() else bits.append(f"LoC {loc}")
    if slr:
        bits.append(f"SLR {slr}")
    if asm:
        bits.append(asm)
    return " • ".join(bits)

# -----------------------------------------------------------------------------
# Data loading
# -----------------------------------------------------------------------------
def load_manifest(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        data = [
            {
                "title": "Modeling Assumptions",
                "description": "Reference document",
                "category": "Reference",
                "box_link": "https://box.com/s/EXAMPLE_REF_ID",
                "filename": "Appendix.pdf",
                "size": "12 MB",
                "updated": "2025-07-25",
            },
            {
                "title": "Study Model Package",
                "description": "Zipped model inputs/outputs.",
                "category": "Model",
                "box_link": "https://box.com/s/EXAMPLE_MODEL_ID",
                "filename": "Model.zip",
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

    for col in [
        "title", "description", "category", "box_link",
        "filename", "size", "id", "planning_horizon", "loc", "slr", "assumptions"
    ]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)

    df["updated"] = pd.to_datetime(df.get("updated", pd.NaT), errors="coerce")
    df["download_url"] = df["box_link"].apply(_to_download_url)
    return df

DF = load_manifest(MANIFEST_PATH)

# -----------------------------------------------------------------------------
# Layout
# -----------------------------------------------------------------------------
def layout():
    categories = ["All"] + sorted([c for c in DF["category"].dropna().unique().tolist() if c])

    return html.Div(
        className="p-4",
        children=[
            html.H1("Downloads", className="text-2xl mb-2"),
            html.P(
                "Browse and download reports, supporting documents and model packages stored in our Box repository.",
                className="mb-4",
            ),

            html.Div(
                className="grid gap-3 md:grid-cols-2 mb-4",
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

            dcc.Store(
                id="dl-store",
                data=DF.assign(
                    updated=DF["updated"].dt.strftime("%Y-%m-%d").fillna(""),
                ).to_dict("records"),
            ),
        ],
    )

layout = layout

# -----------------------------------------------------------------------------
# Rendering helpers
# -----------------------------------------------------------------------------
def _filter_records(records: List[Dict[str, Any]], q: str, category: str):
    df = pd.DataFrame(records)

    if q:
        qlow = q.strip().lower()
        mask = (
            df["title"].str.lower().str.contains(qlow, na=False)
            | df["description"].str.lower().str.contains(qlow, na=False)
            | df["filename"].str.lower().str.contains(qlow, na=False)
        )
        df = df[mask]

    if category and category != "All":
        df = df[df["category"] == category]

    return df

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

    meta = _meta_line(item)

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
                            html.Div(item.get("description", ""), className="text-sm mb-2"),
                            html.Div(meta, className="text-sm text-gray-700 mb-3") if meta else html.Div(),
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

    def title_with_icon(row):
        icon = _file_icon_from_ext(_ext(row.get("filename", "")))
        return f"{icon} {row.get('title','(Untitled)')}"
    tdf["Title"] = tdf.apply(title_with_icon, axis=1)

    tdf = tdf[[
        "Title", "id", "category", "planning_horizon", "loc", "slr",
        "assumptions", "download_url"
    ]].rename(columns={
        "id": "ID",
        "category": "Category",
        "planning_horizon": "Planning Horizon",
        "loc": "Level of Concern",
        "slr": "SLR",
        "assumptions": "Assumptions",
        "download_url": "Download",
    })

    tdf["Download"] = tdf["Download"].apply(lambda u: f"[Download]({u})")

    return html.Div([
        dash_table.DataTable(
            id="dl-table",
            data=tdf.to_dict("records"),
            columns=[
                {"name": c, "id": c, "presentation": "markdown" if c in ["Download"] else "input"}
                for c in tdf.columns
            ],
            page_size=9999,
            sort_action="native",
            filter_action="native",
            style_cell={"textAlign": "left", "whiteSpace": "normal", "height": "auto"},
            style_table={"overflowX": "auto", "overflowY": "auto"},
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
    Input("dl-view-mode", "value"),
)
def render_content(records, q, category, view_mode):
    df = _filter_records(records, q or "", category or "All")
    if view_mode == "table":
        return _table(df)
    return _cards_grid(df)
