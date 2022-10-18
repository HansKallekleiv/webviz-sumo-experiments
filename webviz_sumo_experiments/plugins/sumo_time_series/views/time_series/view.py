from typing import List

from dash.development.base_component import Component
from dash import html, callback, Input, Output, no_update
import pandas as pd
import webviz_core_components as wcc
import plotly.graph_objects as go
import plotly.express as px
from fmu.sumo.explorer import Explorer
from ._requests import get_smry_vector_names, get_vector_data
from webviz_config.utils import StrEnum
from webviz_config.webviz_plugin_subclasses import ViewABC, ViewElementABC
from .settings import TimeSeriesSettings


class TimeSeriesPlot(ViewElementABC):
    class Ids(StrEnum):
        GRAPH = "graph"

    def __init__(self) -> None:
        super().__init__(flex_grow=8)

    def inner_layout(self):
        return html.Div(
            style={"height": "90vh"},
            children=[
                wcc.Graph(
                    id=self.register_component_unique_id(TimeSeriesPlot.Ids.GRAPH),
                    config={
                        "responsive": True,
                    },
                )
            ],
        )


class TimeSeriesView(ViewABC):
    class Ids(StrEnum):
        PLOT = "plot"
        SETTINGS = "settings"

    def __init__(self, case_a_selector, case_b_selector) -> None:
        super().__init__("Shared settings")
        self.add_settings_group(TimeSeriesSettings(), TimeSeriesView.Ids.SETTINGS)
        self.add_view_element(TimeSeriesPlot(), TimeSeriesView.Ids.PLOT)
        self.case_a_selector = case_a_selector
        self.case_b_selector = case_b_selector
        self.set_callbacks()

    def layout(self) -> List[Component]:
        return [
            html.Div(
                children=[
                    html.Div(
                        id=self.register_component_unique_id(TimeSeriesView.Ids.PLOT)
                    )
                ]
            )
        ]

    def set_callbacks(self) -> None:
        def settings_comp_id(comp: str):
            return (
                self.settings_group(TimeSeriesView.Ids.SETTINGS)
                .component_unique_id(comp)
                .to_string()
            )

        def view_comp_id(comp: str):
            return (
                self.view_element(TimeSeriesView.Ids.PLOT)
                .component_unique_id(comp)
                .to_string()
            )

        @callback(
            Output(settings_comp_id(TimeSeriesSettings.Ids.VECTOR_A), "options"),
            Output(settings_comp_id(TimeSeriesSettings.Ids.VECTOR_A), "value"),
            Output(settings_comp_id(TimeSeriesSettings.Ids.VECTOR_B), "options"),
            Output(settings_comp_id(TimeSeriesSettings.Ids.VECTOR_B), "value"),
            Input(self.case_a_selector, "value"),
            Input(self.case_b_selector, "value"),
        )
        def _get_vectors(case_a, case_b):
            explorer = Explorer(env="dev", interactive=True)

            vectors_a = get_smry_vector_names(explorer=explorer, case_uuid=case_a)
            vectors_b = get_smry_vector_names(explorer=explorer, case_uuid=case_b)

            return (
                [{"label": vector, "value": vector} for vector in vectors_a],
                vectors_a[0],
                [{"label": vector, "value": vector} for vector in vectors_b],
                vectors_b[0],
            )

        @callback(
            Output(view_comp_id(TimeSeriesPlot.Ids.GRAPH), "figure"),
            Input(self.case_a_selector, "value"),
            Input(self.case_b_selector, "value"),
            Input(settings_comp_id(TimeSeriesSettings.Ids.VECTOR_A), "value"),
            Input(settings_comp_id(TimeSeriesSettings.Ids.VECTOR_B), "value"),
        )
        def _get_vectors(case_a, case_b, vector_a, vector_b):
            explorer = Explorer(env="dev", interactive=True)
            # if not case_a or case_b or vector_a or vector_b:
            #     return no_update
            name_a = f"{explorer.get_case_by_id(case_a).case_name}-{vector_a}"
            name_b = f"{explorer.get_case_by_id(case_b).case_name}-{vector_b}"

            df = get_vector_data(explorer, case_a, "DATE")
            df[name_a] = get_vector_data(explorer, case_a, vector_a)[vector_a]
            df[name_b] = get_vector_data(explorer, case_b, vector_b)[vector_b]

            fig = go.Figure()
            for idx, (real, real_df) in enumerate(df.groupby("REAL")):
                fig.add_trace(
                    go.Scatter(
                        x=real_df["DATE"],
                        y=real_df[name_a],
                        mode="lines",
                        name=f"{real}-{name_a}",
                        line={"color": "red"},
                        legendgroup=name_a,
                        showlegend=idx == 0,
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=real_df["DATE"],
                        y=real_df[name_b],
                        mode="lines",
                        name=f"{real}-{name_b}",
                        line={"color": "blue"},
                        legendgroup=name_b,
                        showlegend=idx == 0,
                    )
                )
            # fig_a = px.line(veca_df, x="DATE", y=vector_a, height=800, color="REAL")
            # fig_b = px.line(vecb_df, x="DATE", y=vector_b, height=800, color="REAL")
            # fig.add_traces(fig_a["data"])
            # fig.add_traces(fig_b["data"])
            return fig
