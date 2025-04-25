# Imports
from collections import namedtuple

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, callback, dcc, html, register_page

#from charts.chart_layouts import ann_exc_plot, mon_exc_plot
from pages.styles import ASSUMPTION_ORDER, CLIMATE_ORDER, PLOT_COLORS, SCENARIO_COLORS
from utils.query_data import date_map, df_dv, scen_aliases, var_dict
from utils.tools import (
    cfs_taf,
    common_pers,
)
from data import load_markdown


per_of_interest_text = load_markdown("page_text/pers_of_interest.md")

register_page(
    __name__,
    name="Dry/Wet Periods",
    top_nav=True,
    path="/dry_wet_periods",
    order=2,
)

def create_button_filter(
    label: str,
    filter_id: str,
    options: list[str],
    value: list[str],
) -> html.Div:
    return html.Div(
        children=[
            dbc.Label(label),
            dbc.Checklist(
                id=filter_id,
                value=value,
                options=[{"label": v, "value": v} for v in options],
            ),
        ],
        className="m-1 p-2 border-top",
    )


def create_radio_filter(
    label: str,
    filter_id: str,
    options: list[str],
    value: str
) -> html.Div:
    return html.Div(
        children=[
            dbc.Label(label),
            dbc.RadioItems(
                id=filter_id,
                value=value,
                options=[{"label": v, "value": v} for v in options],
            ),
        ],
        className="m-1 p-2 border-top",
    )


def create_dropdown(
    label: str,
    filter_id: str,
    options: list[str],
    value: str,
) -> html.Div:
    return html.Div(
        children=[
            dbc.Label(label),
            dbc.Select(
                id=filter_id,
                options=[{"label": v, "value": v} for v in options],
                value=value
            ),
        ],
        className="m-1 p-2 border-top",
    )


def layout():
    filter_pane = dbc.Col(
        id="filter_pane",
        children=[
            html.H4("Data Filters"),
            create_button_filter(
                label="Adaptation Portfolio",
                filter_id="filter-assumption",
                options=ASSUMPTION_ORDER,
                value=ASSUMPTION_ORDER,
            ),
            create_radio_filter(
                label="Climate",
                filter_id="filter-climate",
                options=CLIMATE_ORDER,
                value=CLIMATE_ORDER[1],
            ),
            create_radio_filter(
                label="Averaging Windows",
                filter_id="filter-average-windows",
                options=common_pers.keys(),
                value=list(common_pers.keys())[0],
            ),
            create_dropdown(
                label="Variable",
                filter_id="filter-variable",
                options=var_dict.keys(),
                value="SWP_TA_CO_SOD"
            ),
        ],
        class_name="col-4 col-md-3 bg-light py-3",
    )

    view_pane = dbc.Col(
        id="view_pane",
        children=[
                html.A(per_of_interest_text),
                dcc.Graph(id="graph-annual"),  
        ],
        class_name="bg-transparent py-3",
    )

    return dbc.Row(
        children=[
            filter_pane,
            view_pane,
        ],
        class_name="h-100",
    )


@callback(
    Output("graph-annual", "figure"),
    Input("filter-assumption", "value"),
    Input("filter-climate", "value"),
    Input("filter-variable", "value"),
    Input("filter-average-windows", "value"),
)
def update_annual(assumption, climate, variable, avg_window):
    endyr = int(common_pers[avg_window].split("-")[1])
    startyr = int(common_pers[avg_window].split("-")[0])

    df_dv['iwy'] = df_dv['iwy'].astype(int)
    
    if var_dict[variable]["table_convert"] == "cfs_taf":
        units = "TAF/year"
    else:
        units = ""

    mask = (
        df_dv["Assumption"].isin(list(assumption)) &
        (df_dv["Climate"] == climate) &
        (df_dv["iwy"].between(startyr, endyr))#&
        #[df_dv["WYT_SAC_"].isin([1,2,3,4,5])]
    )

    df = df_dv.loc[mask, :]
    df = cfs_taf(df, var_dict)  # Convert

    df: pd.DataFrame = df.groupby(["Assumption"]).sum(numeric_only=True) / (endyr - startyr + 1)

    df = df.reindex(ASSUMPTION_ORDER, level="Assumption")

    df["denominator"] = df.loc["Maintain", variable]
    df["vol_change"] = ((df.loc[:, variable]-df["denominator"]))
    df["percent_change"] = ((df.loc[:, variable]-df["denominator"])/df["denominator"])*100

    fig = px.bar(
        df,
        x=df.index.get_level_values(0),
        y=variable,
        color=df.index.get_level_values(0),
        color_discrete_map=SCENARIO_COLORS,
        custom_data=df[["percent_change", "vol_change"]],
        text_auto=True
    )
    fig.update_layout(
        title=f"{(var_dict[variable]['alias'])} ({variable})",
        legend_title="Scenario",
        barmode="relative",
        plot_bgcolor="white",
        yaxis_tickformat=",d",
        yaxis_title=f"{units}"
    )

    fig.update_traces(
        hovertemplate="<b>Change vs Maintain:</b> %{customdata[0]:.2f}% (%{customdata[1]:,d} TAF)<br>"
    )
    return fig
