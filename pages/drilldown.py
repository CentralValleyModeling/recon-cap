# Imports
from collections import defaultdict, namedtuple

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import (
    Input, Output, State, callback, dcc, html, register_page,
    ALL, ctx  # pattern-matching + triggered context
)

from charts.chart_layouts import ann_exc_plot, mon_exc_plot
from pages.styles import PLOT_COLORS, ASSUMPTION_ORDER, SCENARIO_COLORS, CLIMATE_ORDER
from utils.query_data import date_map, df_dv, scen_aliases, var_dict
from data import load_markdown
from utils.tools import (
    cfs_taf,
    convert_wyt_nums,
    list_files,
    load_data_mult,
    make_ressum_df,
    make_summary_df,
    month_list,
    monthfilter,
    month_map,
    wyt_list,
    get_unit_descriptions,
)

# ---- Page registration ----
register_page(
    __name__,
    name="Drilldown",
    top_nav=True,
    path="/drilldown",
    order=6,
)

# ---- Static text ----
# NOTE: load_markdown in your codebase returns a dcc.Markdown component
drilldown_text = load_markdown("page_text/drilldown.md")

# ---- Build mappings / groupings ----
B_PARTS = list(var_dict.keys())

def alias_label(b: str) -> str:
    """Label = 'Alias — B_PART' (falls back to B_PART if alias missing)."""
    a = var_dict.get(b, {}).get("alias", "")
    a_str = (str(a).strip() if a is not None else "")
    return f"{a_str} — {b}" if a_str else b

# Group B-parts by "type" from YAML, skipping type=='hide'
_type_groups = defaultdict(list)
for b in B_PARTS:
    _type = var_dict[b].get("type", "Other")
    if str(_type).lower() == "hide":  # <-- skip hidden types
        continue
    _type_groups[_type].append(b)

# Sort groups by type name; sort B-parts within group by alias then name
TYPE_GROUPS = {
    t: sorted(blist, key=lambda bb: (str(var_dict[bb].get("alias", "")), bb))
    for t, blist in sorted(_type_groups.items(), key=lambda kv: kv[0])
}


# ---- Layout ----
def layout(**kwargs):
    b_default = kwargs.get("type", "C_CAA003")

    # Left: filter pane (sticky, full height) with grouped radios
    group_sections = []
    for t, blist in TYPE_GROUPS.items():
        # One RadioItems per type-group
        group_sections.extend([
            html.H6(t, className="mt-3 mb-2 fw-bold"),
            dcc.RadioItems(
                id={"type": "alias-group-radio", "group": t},
                options=[{"label": alias_label(b), "value": b} for b in blist],
                value=b_default if b_default in blist else None,
                labelStyle={"display": "block", "marginBottom": "6px"},
                inputStyle={"marginRight": "8px"},
                style={"marginLeft": "2px"},
            ),
        ])

    filter_pane = dbc.Col(
        [
            html.Label("Select variable (by Alias):", className="fw-semibold"),
            html.Div(
                group_sections,
                style={
                    "maxHeight": "calc(100vh - 220px)", 
                    "overflowY": "auto",
                    "paddingRight": "6px",
                },
            ),
            html.Hr(),
            html.Label("Climate (filter for all charts):"),
            dcc.Dropdown(
                options=[{"label": c, "value": c} for c in CLIMATE_ORDER],
                id="climate-filter",
                value="2043_CC50",
                style={"width": "100%"},
                persistence=True,
                persistence_type="session",
            ),
        ],
        md=4,
        class_name="bg-light p-3",
        style={
            "position": "sticky",
            "top": "0",             
            "height": "100vh",
            "overflow": "hidden",   
            "borderRight": "1px solid #e9ecef",
        },
    )

    # Right: view pane (unchanged content; scrolls)
    view_pane = dbc.Col(
        [
            drilldown_text,
            html.Br(),
            html.Div(id="my-output"),

            dbc.Row([dcc.Markdown("**Monthly timeseries**"), dcc.Graph(id="timeseries-plot")]),

            dbc.Row(
                [
                    dcc.Markdown("**Annual timeseries**"),
                    dbc.Col(
                        [
                            html.P("Year type for annual timeseries plot", className="text-muted mt-1 m-0"),
                            dcc.Dropdown(
                                options=["Calendar Year", "Water Year"],
                                id="year-type-annual-timeseries",
                                style={"width": "50%"},
                                value="Water Year",
                            ),
                            html.P("Aggregation method for annual timeseries plot", className="text-muted mt-1 m-0"),
                            dcc.Dropdown(
                                options=["Mean", "Max", "Min", "Sum"],
                                id="agg-annual-timeseries",
                                style={"width": "50%"},
                                value="Mean",
                            ),
                        ]
                    ),
                    dcc.Graph(id="annual-timeseries-plot"),
                ]
            ),

            dbc.Row(
                [
                    dbc.Col(
                        [
                            dcc.Markdown("**Monthly exceedance**"),
                            dcc.Checklist(
                                options=month_list,
                                value=month_list,
                                inline=True,
                                id="monthchecklist-exc",
                                inputStyle={"marginRight": "5px", "marginLeft": "5px"},
                            ),
                            dcc.Graph(id="exceedance-plot"),
                        ],
                        align="center",
                    ),
                    dbc.Col(
                        [
                            dcc.Markdown("**Monthly average**"),
                            dcc.Checklist(
                                options=wyt_list,
                                value=wyt_list,
                                inline=True,
                                id="wytchecklist-bar",
                                inputStyle={"marginRight": "5px", "marginLeft": "30px"},
                            ),
                            dcc.Graph(id="bar-plot"),
                        ]
                    ),
                ]
            ),

            dbc.Row(
                [
                    dbc.Col(
                        [
                            dcc.Markdown("**Annual exceedance**"),
                            dcc.Dropdown(
                                options=["Calendar Year", "Water Year"],
                                id="yearwindow",
                                style={"width": "50%"},
                                value="Water Year",
                            ),
                            dcc.Graph(id="exceedance-plot-annual"),
                        ]
                    ),
                    dbc.Col(
                        [
                            dcc.Markdown("**Annual average**"),
                            dcc.Dropdown(
                                options=["Calendar Year", "Water Year"],
                                id="yearwindow-repeater",
                                style={"width": "50%"},
                                value="Water Year",
                                disabled=True,
                            ),
                            dcc.Graph(id="bar-plot-annual"),
                        ]
                    ),
                ]
            ),

            dcc.RangeSlider(
                1922,
                2021,
                1,
                value=[1922, 2021],
                marks={i: f"{i}" for i in range(1922, 2021, 5)},
                pushable=False,
                id="slider-yr-range",
            ),
            html.Div(id="output-container-range-slider"),
        ],
        md=8,
        class_name="py-3",
        style={"minHeight": "100vh", "overflow": "auto"},
    )

    # Single source of truth for selected B-Part
    store = dcc.Store(id="b-part-store", data=b_default, storage_type="memory")

    return dbc.Container(
        [store, dbc.Row([filter_pane, view_pane], class_name="g-0")],
        fluid=True,
        class_name="p-0",
        style={"minHeight": "100vh"},
    )


# =======================
# CALLBACKS
# =======================

# Enforce single-selection across ALL group radios and expose the selected B-Part
@callback(
    Output({"type": "alias-group-radio", "group": ALL}, "value"),
    Output("b-part-store", "data"),
    Input({"type": "alias-group-radio", "group": ALL}, "value"),
    prevent_initial_call=False,
)
def exclusive_radio_selection(values):
    """
    values: list of current values from each group radio (one per group; value is B-Part or None).
    Ensure only one group holds a non-None value at a time.
    """
    # If no trigger (initial call), keep what's provided; pick the first non-None as selected
    triggered = ctx.triggered_id if ctx.triggered_id is not None else None

    # Identify which index triggered (by matching group key)
    trig_index = None
    if triggered and isinstance(triggered, dict) and triggered.get("type") == "alias-group-radio":
        # The ALL input order matches the order components were created in layout (TYPE_GROUPS iteration).
        groups_order = list(TYPE_GROUPS.keys())
        try:
            trig_index = groups_order.index(triggered.get("group"))
        except ValueError:
            trig_index = None

    selected = None

    # If user clicked something, prefer that group's value as the sole selection
    if trig_index is not None and values[trig_index] is not None:
        selected = values[trig_index]
        new_values = [None] * len(values)
        new_values[trig_index] = selected
        return new_values, selected

    # Otherwise, on initial render or if user de-selected, keep the first non-None (if any)
    for v in values:
        if v is not None:
            selected = v
            break

    # If none selected, fall back to first B-Part in first group
    if selected is None:
        first_group = next(iter(TYPE_GROUPS.values()))
        selected = first_group[0] if first_group else None

    # Normalize: ensure only the first non-None remains set
    new_values = [None] * len(values)
    if selected is not None:
        # set it on whichever group currently has it (or the first group's default)
        for i, v in enumerate(values):
            if v == selected:
                new_values[i] = selected
                break
        else:
            # not found; set on group 0
            new_values[0] = selected

    return new_values, selected


# Mirror yearwindow into the disabled dropdown so it reflects the choice
@callback(Output("yearwindow-repeater", "value"), Input("yearwindow", "value"))
def mirror_yearwindow(v):
    return v


# Timeseries Plot
@callback(
    Output("timeseries-plot", "figure"),
    Input("b-part-store", "data"),
    Input("climate-filter", "value"),
)
def update_timeseries(b_part, climate_filter):
    df_plot = df_dv.loc[df_dv["Climate"] == climate_filter]
    alias = var_dict[b_part]["alias"]
    units = get_unit_descriptions(var_dict, b_part)

    fig = px.line(
        df_plot,
        x=df_plot.index,
        y=b_part,
        color="Assumption",
        color_discrete_map=SCENARIO_COLORS,
        category_orders={"Assumption": ASSUMPTION_ORDER},
    )
    fig.update_layout(
        title=f"{alias} ({b_part})",
        plot_bgcolor="white",
        legend_title="Adaptation Portfolio",
        xaxis=dict(gridcolor="LightGray"),
        xaxis_title="CalSim 3 simulation period (monthly timestep)",
        yaxis=dict(gridcolor="LightGray"),
        yaxis_title=units,
        yaxis_tickformat=",d",
    )
    return fig


# Annual Timeseries Plot
@callback(
    Output("annual-timeseries-plot", "figure"),
    Input("b-part-store", "data"),
    Input("year-type-annual-timeseries", "value"),
    Input("agg-annual-timeseries", "value"),
    Input("climate-filter", "value"),
)
def update_annual_timeseries(
    b_part,
    year_type: str = "Calendar Year",
    agg_method: str = "Mean",
    climate_filter: str = "2043_CC50",
):
    offsets = {"Calendar Year": 1, "Water Year": 10}
    units = get_unit_descriptions(var_dict, b_part)
    df_plot = df_dv.loc[df_dv["Climate"] == climate_filter]

    df_agg = (
        df_plot.loc[:, [b_part, "Assumption"]]
        .groupby("Assumption")
        .resample(rule=pd.offsets.YearBegin(month=offsets[year_type]))
        .agg({b_part: [agg_method.lower(), "count"]})
        .rename_axis(index=["Assumption", year_type])
        .reset_index()
    )
    df_agg.columns = [
        "-".join(c).strip("- ") if isinstance(c, tuple) else c for c in df_agg.columns
    ]
    count_col = f"{b_part}-count"
    df_agg = df_agg.loc[df_agg[count_col] == 12, :]
    df_agg[b_part] = df_agg[f"{b_part}-{agg_method.lower()}"]

    fig = px.line(
        df_agg,
        x=year_type,
        y=b_part,
        color="Assumption",
        color_discrete_map=SCENARIO_COLORS,
        category_orders={"Assumption": ASSUMPTION_ORDER},
    )
    fig.update_layout(
        plot_bgcolor="white",
        legend_title="Adaptation Portfolio",
        xaxis=dict(gridcolor="LightGray"),
        yaxis=dict(gridcolor="LightGray"),
        yaxis_title=f"{units} (annual {agg_method.lower()})",
        yaxis_tickformat=",d",
    )
    return fig


# Monthly Exceedance Plot
@callback(
    Output("exceedance-plot", "figure"),
    Input("b-part-store", "data"),
    Input("monthchecklist-exc", "value"),
    Input("climate-filter", "value"),
)
def update_exceedance(b_part, monthchecklist, climate_filter):
    df_plot = df_dv.loc[df_dv["Climate"] == climate_filter]
    units = get_unit_descriptions(var_dict, b_part)

    fig = mon_exc_plot(df_plot, b_part, monthchecklist, climate_filter)
    fig.update_layout(
        plot_bgcolor="white",
        legend_title="Adaptation Portfolio",
        xaxis=dict(gridcolor="LightGray"),
        yaxis=dict(gridcolor="LightGray"),
        yaxis_title=units,
        yaxis_tickformat=",d",
    )
    return fig


# Annual Exceedance Plot
@callback(
    Output("exceedance-plot-annual", "figure"),
    Input("b-part-store", "data"),
    Input("monthchecklist-exc", "value"),
    Input("yearwindow", "value"),
    Input("climate-filter", "value"),
)
def update_annual_exceedance(b_part, monthchecklist, yearwindow, climate_filter):
    if var_dict[b_part]["table_convert"] == "cfs_taf":
        df_plot = df_dv.loc[df_dv["Climate"] == climate_filter]
        fig = ann_exc_plot(df_plot, b_part, yearwindow)
        fig.update_layout(
            plot_bgcolor="white",
            legend_title="Adaptation Portfolio",
            xaxis=dict(showgrid=True, gridcolor="LightGray"),
            yaxis=dict(showgrid=True, gridcolor="LightGray"),
            yaxis_title="Thousand acre-feet per year",
            yaxis_tickformat=",d",
        )
    else:
        fig = px.line()
        fig.update_layout(
            plot_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor="LightGray"),
            yaxis=dict(showgrid=True, gridcolor="LightGray"),
            annotations=[
                dict(
                    text="⚠️ Variable not suitable for annual exceedance plot",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=18, color="red"),
                    align="center",
                )
            ],
        )
    return fig


# Monthly Average Plot
@callback(
    Output("bar-plot", "figure"),
    Input("b-part-store", "data"),
    Input("wytchecklist-bar", "value"),
    Input("slider-yr-range", "value"),
    Input("climate-filter", "value"),
)
def update_monthly(b_part, wytchecklist, slider_yr_range, climate_filter):
    startyr, endyr = slider_yr_range
    df = df_dv.loc[
        df_dv["WYT_SAC_MAY"].isin(convert_wyt_nums(wytchecklist))
        & (df_dv["iwy"] >= startyr)
        & (df_dv["iwy"] <= endyr)
        & (df_dv["Climate"] == climate_filter)
    ]

    df = cfs_taf(df, var_dict)
    df = round(df.groupby(["Assumption", "iwm"]).mean(numeric_only=True))
    df = df.reindex(ASSUMPTION_ORDER, level="Assumption")

    if var_dict[b_part]["table_convert"] == "cfs_taf":
        units = "Thousand acre-feet per month"
    else:
        units = get_unit_descriptions(var_dict, b_part)

    fig = px.line(
        df,
        x=df.index.get_level_values(1),
        y=b_part,
        color=df.index.get_level_values(0),
        labels={"color": "Assumption"},
        color_discrete_map=SCENARIO_COLORS,
    )
    fig.update_layout(
        plot_bgcolor="white",
        legend_title="Adaptation Portfolio",
        xaxis=dict(
            tickmode="array",
            tickvals=monthfilter,
            ticktext=month_list,
            showgrid=True,
            gridcolor="LightGray",
        ),
        yaxis=dict(showgrid=True, gridcolor="LightGray", title=units),
        yaxis_tickformat=",d",
        xaxis_title="Month",
    )
    return fig


# Annual Bar Plot
@callback(
    Output("bar-plot-annual", "figure"),
    Input("b-part-store", "data"),
    Input("wytchecklist-bar", "value"),
    Input("slider-yr-range", "value"),
    Input("climate-filter", "value"),
)
def update_bar_annual(b_part, wytchecklist, slider_yr_range, climate_filter):
    startyr, endyr = slider_yr_range
    df_filtered = df_dv.loc[
        df_dv["WYT_SAC_MAY"].isin(convert_wyt_nums(wytchecklist))
        & (df_dv["iwy"] >= startyr)
        & (df_dv["iwy"] <= endyr)
        & (df_dv["Climate"] == climate_filter)
    ]

    df_filtered = cfs_taf(df_filtered, var_dict)  # Convert
    df_monthly = df_filtered.groupby(["Assumption", "iwm"]).mean(numeric_only=True)
    df_annual = df_monthly.groupby(["Assumption"]).sum(numeric_only=True)
    df_annual = df_annual.reindex(ASSUMPTION_ORDER, level="Assumption")
    df_annual = df_annual.dropna(how="all", subset=None)

    if var_dict[b_part]["table_convert"] == "cfs_taf":
        units = "Thousand acre-feet per year"
        alias = var_dict[b_part]["alias"]

        fig = px.bar(
            df_annual,
            x=df_annual.index.get_level_values(0),
            y=b_part,
            color=df_annual.index.get_level_values(0),
            text_auto=True,
            color_discrete_map=SCENARIO_COLORS,
            custom_data=df_annual[[b_part]],
        )
        fig.update_layout(
            title=f"Annual average {alias} ({climate_filter})",
            legend_title="Adaptation Portfolio",
            barmode="relative",
            plot_bgcolor="white",
            yaxis_title=units,
            yaxis_tickformat=",d",
        )
        fig.update_traces(hovertemplate="<b>Value:</b> %{customdata[0]:.2f}<br>")
    else:
        fig = px.line()
        fig.update_layout(
            plot_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor="LightGray"),
            yaxis=dict(showgrid=True, gridcolor="LightGray"),
            annotations=[
                dict(
                    text="⚠️ Variable not suitable for annual bar plot",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=18, color="red"),
                    align="center",
                )
            ],
        )
    return fig


# Flow Summary tables
@callback(
    Output("sum_tbl", "data"),
    Input("slider-yr-range", "value"),
    Input("monthchecklist-exc", "value"),
)
def update_table(slider_yr_range, monthchecklist):
    monthfilter_local = [month_map[v] for v in monthchecklist]
    df_tbl = make_summary_df(
        scen_aliases,
        df_dv,
        var_dict,
        start_yr=slider_yr_range[0],
        end_yr=slider_yr_range[1],
        monthfilter=monthfilter_local,
    )
    return df_tbl.to_dict(orient="records")


# Reservoir Summary tables
@callback(
    Output("sum_tbl_res", "data"),
    Input("slider-yr-range", "value"),
    Input("monthradio", "value"),
)
def update_table2(slider_yr_range, monthradio):
    monthradio_vals = [month_map[monthradio]]
    df_tbl = make_ressum_df(
        scen_aliases,
        df_dv,
        var_dict,
        start_yr=slider_yr_range[0],
        end_yr=slider_yr_range[1],
        monthfilter=monthradio_vals,
    )
    return df_tbl.to_dict(orient="records")


@callback(Output("output-container-range-slider", "children"), Input("slider-yr-range", "value"))
def set_slider(value):
    return value[0], str("-"), value[1]


@callback(
    Output("dummy-div1", "children"),
    Input("load-studies", "n_clicks"),
    State("file-table", "data"),
    prevent_initial_call=True,
)
def load(n_clicks, full_scen_table):
    scen_dict = {}
    for s in full_scen_table:
        if s["alias"].strip() != "":
            scen_dict[s["alias"]] = s["pathname"]
    load_data_mult(scen_dict, var_dict, date_map)
    print(scen_dict)
    return "Loading"


# Populate the ledger
@callback(Output("file-table", "data"), Input("populate-table", "n_clicks"))
def populate_table(n_clicks):
    scenarios = list_files("uploads")
    for s in scenarios:
        new_entries = [
            {"pathname": scenarios[s], "filename": s, "alias": ""} for s in scenarios
        ]
    return new_entries


# Return a scenario dictionary with the aliases that user entered
@callback(Output("table-update-output", "children"), Input("file-table", "data"))
def display_updated_data(full_scen_table):
    if full_scen_table is None:
        return "No data in the table."
    # Build dict as side-effect/validation step if you want
    scen_dict = {}
    for s in full_scen_table:
        if s.get("alias", "").strip() != "":
            scen_dict[s["alias"]] = s["pathname"]
    return ""
