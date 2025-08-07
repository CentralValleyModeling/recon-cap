# Imports
from collections import namedtuple

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, callback, dcc, html, register_page

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
    get_unit_descriptions
)

register_page(
    __name__,
    name="Drilldown",
    top_nav=True,
    path="/drilldown",
    order=6,
)

drilldown_text = load_markdown("page_text/drilldown.md")

bparts = []
aliases = []

for var in var_dict:
    bparts.append(var)
    aliases.append(var_dict[var]["alias"])

# Layout Starts Here
def layout(**kwargs):
    b = kwargs.get("type", "C_CAA003")
    print(b)
    layout = dbc.Container(
        class_name="my-3",
        children=[
            dbc.Row(
                [
                    html.A(drilldown_text),
                    dbc.Col(
                        [
                            "Climate (filter for all charts): ",
                            dcc.Dropdown(
                                CLIMATE_ORDER, id="climate-filter", value="2043_CC50", style={"width": "100%"}
                            ),
                            "CalSim variable name (B-Part): ",
                            dcc.Dropdown(
                                bparts, id="b-part", value=b, style={"width": "100%"}
                            ),
                            "Search by common description: ",
                            dcc.Dropdown(
                                options=aliases,
                                id="alias",
                                value=var_dict[b]["alias"],
                                style={"width": "100%"},
                            ),
                        ],
                        width=6,
                    ),
                ]
            ),
            html.Br(),
            html.Div(id="my-output"),
            dbc.Row(
                [
                    dcc.Markdown("**Monthly timeseries**"),
                    dcc.Graph(id="timeseries-plot"),
                ]
            ),
            dbc.Row(
                [
                    dcc.Markdown("**Annual timeseries**"),
                    dbc.Col(
                        [
                            html.P(
                                "Year type for annual timeseries plot",
                                className="text-muted mt-1 m-0",
                            ),
                            dcc.Dropdown(
                                options=["Calendar Year", "Water Year"],
                                id="year-type-annual-timeseries",
                                style={"width": "50%"},
                                value="Water Year",
                            ),
                            html.P(
                                "Aggregation method for annual timeseries plot",
                                className="text-muted mt-1 m-0",
                            ),
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
                                inputStyle={
                                    "margin-right": "5px",
                                    "margin-left": "5px",
                                },
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
                                inputStyle={
                                    "margin-right": "5px",
                                    "margin-left": "30px",
                                },
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
                marks={i: "{}".format(i) for i in range(1922, 2021, 5)},
                pushable=False,
                id="slider-yr-range",
            ),
            html.Div(id="output-container-range-slider"),
        ],
        fluid=False,
    )
    return layout


# CALLBACKS Start Here


# Return B Part based on alias search
@callback(
    Output(component_id="b-part", component_property="value"),
    Input(component_id="alias", component_property="value"),
)
def update_b_part(alias):
    i = aliases.index(str(alias))
    b = bparts[i]
    return b

# Timeseries Plot
@callback(
    Output(component_id="timeseries-plot", component_property="figure"),
    Input(component_id="b-part", component_property="value"),
    Input(component_id="climate-filter", component_property="value"),
)
def update_timeseries(b_part, climate_filter):
    df_plot = df_dv.loc[df_dv['Climate'] == climate_filter]

    alias = var_dict[b_part]["alias"]
    units = get_unit_descriptions(var_dict, b_part)

    fig = px.line(
        df_plot,
        x=df_plot.index,
        y=b_part,
        color="Assumption",
        color_discrete_map=SCENARIO_COLORS,
        category_orders={"Assumption": ASSUMPTION_ORDER}
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
    Output(component_id="annual-timeseries-plot", component_property="figure"),
    Input(component_id="b-part", component_property="value"),
    Input(component_id="year-type-annual-timeseries", component_property="value"),
    Input(component_id="agg-annual-timeseries", component_property="value"),
    Input(component_id="climate-filter", component_property="value"),
)
def update_annual_timeseries(
    b_part,
    year_type: str = "Calendar Year",
    agg_method: str = "Mean",
    climate_filter: str = "2043_CC50"
):
    offsets = {
        "Calendar Year": 1,
        "Water Year": 10,
    }
    units = get_unit_descriptions(var_dict, b_part)
    df_plot = df_dv.loc[df_dv['Climate'] == climate_filter]

    df_agg = (
        df_plot.loc[:, [b_part, "Assumption"]]
        .groupby("Assumption")
        .resample(rule=pd.offsets.YearBegin(month=offsets[year_type]))
        .agg({b_part: [agg_method.lower(), "count"]})
        .reset_index()
    )

    df_agg.columns = ["-".join(c).strip("- ") for c in df_agg.columns]
    count = df_agg[f"{b_part}-count"]
    df_agg[year_type] = df_agg["level_1"]
    df_agg[b_part] = df_agg[f"{b_part}-{agg_method.lower()}"]  # Clean name of agg
    df_agg = df_agg.loc[count == 12, :]  # Filter to only show full years of data
    fig = px.line(
        df_agg,
        x=year_type,
        y=b_part,
        color="Assumption",
        color_discrete_map=SCENARIO_COLORS,
        category_orders={"Assumption": ASSUMPTION_ORDER}
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
    Output(component_id="exceedance-plot", component_property="figure"),
    Input(component_id="b-part", component_property="value"),
    Input(component_id="monthchecklist-exc", component_property="value"),
    Input(component_id="climate-filter", component_property="value"),
)
def update_exceedance(b_part, monthchecklist, climate_filter):
    
    df_plot = df_dv.loc[df_dv['Climate'] == climate_filter]
    units = get_unit_descriptions(var_dict, b_part)
    #print(df_plot)
    
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
    Output(component_id="exceedance-plot-annual", component_property="figure"),
    Input(component_id="b-part", component_property="value"),
    Input(component_id="monthchecklist-exc", component_property="value"),
    Input(component_id="yearwindow", component_property="value"),
    Input(component_id="climate-filter", component_property="value"),
)
def update_annual_exceedance(b_part, monthchecklist, yearwindow, climate_filter):
    if var_dict[b_part]["table_convert"] == "cfs_taf":
        df_plot = df_dv.loc[df_dv['Climate'] == climate_filter]
        fig = ann_exc_plot(df_plot, b_part, yearwindow)
        fig.update_layout(
            plot_bgcolor="white",
            legend_title="Adaptation Portfolio",
            xaxis=dict(gridcolor="LightGray"),
            yaxis=dict(gridcolor="LightGray"),
            yaxis_title="Thousand acre-feet per year",
            yaxis_tickformat=",d",
        )

    else:
        fig = px.line()
        fig.update_layout(
            annotations=[
                dict(
                    text="⚠️ Variable not suitable for annual exceedance plot",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=18, color="red"),
                    align="center"
                )
            ],
        )
    return fig


# Monthly Average Plot
@callback(
    Output(component_id="bar-plot", component_property="figure"),
    Input(component_id="b-part", component_property="value"),
    Input(component_id="wytchecklist-bar", component_property="value"),
    Input(component_id="slider-yr-range", component_property="value"),
    Input(component_id="climate-filter", component_property="value"),
)
def update_monthly(b_part, wytchecklist, slider_yr_range, climate_filter):
    startyr = slider_yr_range[0]
    endyr = slider_yr_range[1]

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
        yaxis=dict(
            showgrid=True,
            gridcolor="LightGray",
            title=units
        ),
        yaxis_tickformat=",d",
        xaxis_title="Month"
    )

    return fig


# Annual Bar Plot
@callback(
    Output(component_id="bar-plot-annual", component_property="figure"),
    Input(component_id="b-part", component_property="value"),
    Input(component_id="wytchecklist-bar", component_property="value"),
    Input(component_id="slider-yr-range", component_property="value"),
    Input(component_id="climate-filter", component_property="value"),
)
def update_bar_annual(b_part, wytchecklist, slider_yr_range, climate_filter):
    startyr = slider_yr_range[0]
    endyr = slider_yr_range[1]
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
            custom_data=df_annual[[b_part]]
        )

        fig.update_layout(
            title=f"Annual average {alias} ({climate_filter})",
            legend_title="Adaptation Portfolio",
            barmode="relative",
            plot_bgcolor="white",
            yaxis_title=units,
            yaxis_tickformat=",d",
        )

        fig.update_traces(
            hovertemplate="<b>Value:</b> %{customdata[0]:.2f}<br>"
        )
    else:
        fig = px.line()
        fig.update_layout(
            annotations=[
                dict(
                    text="⚠️ Variable not suitable for annual bar plot",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=18, color="red"),
                    align="center"
                )
            ],
        )
    return fig


# Flow Summary tables
@callback(
    Output(component_id="sum_tbl", component_property="data"),
    Input(component_id="slider-yr-range", component_property="value"),
    Input(component_id="monthchecklist", component_property="value"),
)
def update_table(slider_yr_range, monthchecklist):
    monthfilter = []
    for v in monthchecklist:
        monthfilter.append(month_map[v])

    df_tbl = make_summary_df(
        scen_aliases,
        df_dv,
        var_dict,
        start_yr=slider_yr_range[0],
        end_yr=slider_yr_range[1],
        monthfilter=monthfilter,
    )
    data = df_tbl.to_dict(orient="records")
    return data


# Reservoir Summary tables
@callback(
    Output(component_id="sum_tbl_res", component_property="data"),
    Input(component_id="slider-yr-range", component_property="value"),
    Input(component_id="monthradio", component_property="value"),
)
def update_table2(slider_yr_range, monthradio):
    monthradio = [month_map[monthradio]]

    df_tbl = make_ressum_df(
        scen_aliases,
        df_dv,
        var_dict,
        start_yr=slider_yr_range[0],
        end_yr=slider_yr_range[1],
        monthfilter=monthradio,
    )
    data = df_tbl.to_dict(orient="records")
    return data


@callback(
    Output(component_id="output-container-range-slider", component_property="children"),
    Input(component_id="slider-yr-range", component_property="value"),
)
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


# Callback to populate the ledger
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
    else:
        pass

    scen_dict = {}
    for s in full_scen_table:
        if s["alias"].strip() != "":
            scen_dict[s["alias"]] = s["pathname"]
