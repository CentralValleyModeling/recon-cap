from urllib.parse import urlencode

import dash_bootstrap_components as dbc
from dash import (
    ALL,
    Input,
    Output,
    callback,
    callback_context,
    dcc,
    html,
    register_page,
)

from charts.chart_layouts import (
    CardWidget,
    card_bar_plot_wy_vert,
    card_bar_plot_orovl_CAP,
)

from data import load_markdown, universal_data_download
from utils.query_data import df_dv
from pages.styles import CLIMATE_ORDER

register_page(
    __name__,
    name="Home",
    top_nav=True,
    path="/",
    title="Results Console",
    order=0,
)

exp_card = CardWidget(
    "Total Delta exports",
    button_id="EXPORTACTUALTDIF",
    button_label="Drilldown",
    popover_label="exp-info",
    popover_content=load_markdown("page_text/info-total-exports.md"),
    charts=card_bar_plot_wy_vert(df_dv, b_part="EXPORTACTUALTDIF", climate_order=CLIMATE_ORDER),
)

swp_exp_card = CardWidget(
    "SWP Banks Exports",
    button_id="C_CAA003_SWP",
    button_label="Drilldown",
    popover_label="swpexp-info",
    popover_content=load_markdown("page_text/info-swp-exports.md"),
    charts=card_bar_plot_wy_vert(df_dv, b_part="C_CAA003_SWP", climate_order=CLIMATE_ORDER),
)

ta_card = CardWidget(
    "SWP Table A deliveries",
    button_id="SWP_TA_CO_SOD",
    button_label="Drilldown",
    popover_label="ta-info",
    popover_content=load_markdown("page_text/info-table-a.md"),
    charts=card_bar_plot_wy_vert(df_dv, b_part="SWP_TA_CO_SOD", climate_order=CLIMATE_ORDER),
)

a21_card = CardWidget(
    "SWP Article 21 deliveries",
    button_id="SWP_IN_SOD",
    button_label="Drilldown",
    popover_label="a21-info",
    popover_content=load_markdown("page_text/info-article-21.md"),
    charts=card_bar_plot_wy_vert(df_dv, b_part="SWP_IN_SOD", climate_order=CLIMATE_ORDER),
)

ndoi_card = CardWidget(
    "Total Delta outflow",
    button_id="NDOI",
    button_label="Drilldown",
    popover_label="ndoi-info",
    popover_content=load_markdown("page_text/info-ndoi.md"),
    charts=card_bar_plot_wy_vert(df_dv, b_part="NDOI", climate_order=CLIMATE_ORDER),
)

orovl_sep_card = CardWidget(
    "Oroville September storage",
    button_id="S_OROVL",
    button_label="Drilldown",
    popover_label="orovl-info",
    popover_content=load_markdown("page_text/info-orovl.md"),
    charts=card_bar_plot_wy_vert(df_dv, b_part="S_OROVL", climate_order=CLIMATE_ORDER, cm=[9]),
)

orovl_sep_co_card = CardWidget(
    "Oroville carryover (percent of simulation period where Oroville September storage < 1.6 MAF)",
    button_id="S_OROVL",
    button_label="Drilldown",
    popover_label="orovl-co-info",
    popover_content=load_markdown("page_text/info-orovl-co.md"),
    charts=card_bar_plot_orovl_CAP(df_dv, b_part="S_OROVL", climate_order=CLIMATE_ORDER, cm=[9]),
)

def layout():
    layout = dbc.Container(
        id="home-container",
        class_name="my-3",
        children=[
            dcc.Download(id="download-response-home"),
            dbc.Row(),
            dbc.Col(
                id="home-cards",
                className="d-grid gap-2",
                children=[
                    dbc.Row(
                        id="intro-text",
                        children=[
                            dbc.Col(
                                class_name="col-md-8", children=[load_markdown("page_text/site-introduction.md")]
                            ),
                            dbc.Col(
                                class_name="col-md-4", children=[html.Img(src="/assets/1997_02_05_DK_09434-014_Aqueduct_web.jpg", style={"width": "100%"})]
                            ),
                            html.Hr(style={"margin": "0.5rem 0"}),
                        ],
                        
                    ),
                    dbc.Row(
                        id="home-cards-row-0",
                        children=[
                            dbc.Col(
                                class_name="col-md-12", children=[exp_card.create_card()]
                            ),
                            html.Hr(style={"margin": "0.5rem 0"}),
                        ],
                    ),
                    dbc.Row(
                        id="home-cards-row-0",
                        children=[
                            dbc.Col(
                                class_name="col-md-12", children=[swp_exp_card.create_card()]
                            ),
                            html.Hr(style={"margin": "0.5rem 0"}),
                        ],
                    ),
                    dbc.Row(
                        id="home-cards-row-0",
                        children=[
                            dbc.Col(
                                class_name="col-md-12", children=[ta_card.create_card()]
                            ),
                            html.Hr(style={"margin": "0.5rem 0"}),
                        ],
                    ),
                    dbc.Row(
                        id="home-cards-row-0",
                        children=[
                            dbc.Col(
                                class_name="col-md-12", children=[a21_card.create_card()]
                            ),
                            html.Hr(style={"margin": "0.5rem 0"}),
                        ],
                    ),
                    dbc.Row(
                        id="home-cards-row-0",
                        children=[
                            dbc.Col(
                                class_name="col-md-12", children=[ndoi_card.create_card()]
                            ),
                            html.Hr(style={"margin": "0.5rem 0"}),
                        ],
                    ),
                    dbc.Row(
                        id="home-cards-row-0",
                        children=[
                            dbc.Col(
                                class_name="col-md-12", children=[orovl_sep_card.create_card()]
                            ),
                            html.Hr(style={"margin": "0.5rem 0"}),
                        ],
                    ),
                    dbc.Row(
                        id="home-cards-row-0",
                        children=[
                            dbc.Col(
                                class_name="col-md-12", children=[orovl_sep_co_card.create_card()]
                            ),
                            html.Hr(style={"margin": "0.5rem 0"}),
                        ],
                    ),
                ],
            ),
        ],
    )
    return layout


@callback(
    Output("url", "href"),
    Output("url", "refresh"),
    Input({"type": "dynamic-btn", "index": ALL}, "n_clicks"),
)
def button_1_action(n_clicks):
    ctx = callback_context
    if not ctx.triggered or all(click is None for click in n_clicks):
        return "/", False
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        button_index = eval(button_id)["index"]
        url_params = urlencode({"type": button_index})

        #print(button_index)

        #if button_index == "ta_wet_dry":
        #    return "/dry_wet_periods", True

        #if button_index in ("EXPORTACTUALTDIF", "S_OROVL", "NDOI", "SWP_TA_CO_SOD", "C_CAA003_SWP"):
        return f"/drilldown?{url_params}", True
        #else:
        #    return f"/contractor_summary?{url_params}", True