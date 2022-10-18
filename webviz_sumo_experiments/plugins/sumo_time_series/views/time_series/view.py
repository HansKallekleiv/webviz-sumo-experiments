from typing import List

import flask
from dash.development.base_component import Component
from dash import html, callback, Input, Output, no_update, State
import numpy as np
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

    def __init__(
        self,
        env: str,
        case_a_selector,
        case_b_selector,
        iteration_a_selector,
        iteration_b_selector,
        interactive,
    ) -> None:
        super().__init__("Shared settings")
        self.add_settings_group(TimeSeriesSettings(), TimeSeriesView.Ids.SETTINGS)
        self.add_view_element(TimeSeriesPlot(), TimeSeriesView.Ids.PLOT)
        self.case_a_selector = case_a_selector
        self.iteration_a_selector = iteration_a_selector
        self.iteration_b_selector = iteration_b_selector
        self.case_b_selector = case_b_selector
        self.env = env
        self.interactive = interactive
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
            Input(self.iteration_a_selector, "value"),
            Input(self.iteration_b_selector, "value"),
            State(settings_comp_id(TimeSeriesSettings.Ids.VECTOR_A), "value"),
            State(settings_comp_id(TimeSeriesSettings.Ids.VECTOR_B), "value"),
        )
        def _get_vectors(
            case_a, case_b, iteration_a, iteration_b, current_vector_a, current_vector_b
        ):
            if self.interactive:
                explorer = Explorer(env=self.env, interactive=self.interactive)
            else:
                explorer = Explorer(
                    env=self.env,
                    token=flask.request.headers["X-Auth-Request-Access-Token"],
                )

            vectors_a = get_smry_vector_names(
                explorer=explorer, case_uuid=case_a, iteration_id=iteration_a
            )
            vectors_b = get_smry_vector_names(
                explorer=explorer, case_uuid=case_b, iteration_id=iteration_b
            )
            if vectors_a:
                veca_opts = [{"label": vector, "value": vector} for vector in vectors_a]
                veca_val = (
                    current_vector_a if current_vector_a in vectors_a else vectors_a[0]
                )
            else:
                veca_opts = []
                veca_val = None
            if vectors_b:
                vecb_opts = [{"label": vector, "value": vector} for vector in vectors_b]
                vecb_val = (
                    current_vector_b if current_vector_b in vectors_b else vectors_b[0]
                )
            else:
                vecb_opts = []
                vecb_val = None
            return (veca_opts, veca_val, vecb_opts, vecb_val)

        @callback(
            Output(view_comp_id(TimeSeriesPlot.Ids.GRAPH), "figure"),
            Input(self.case_a_selector, "value"),
            Input(self.case_b_selector, "value"),
            Input(self.iteration_a_selector, "value"),
            Input(self.iteration_b_selector, "value"),
            Input(settings_comp_id(TimeSeriesSettings.Ids.VECTOR_A), "value"),
            Input(settings_comp_id(TimeSeriesSettings.Ids.VECTOR_B), "value"),
            Input(settings_comp_id(TimeSeriesSettings.Ids.AGGREGATION), "value"),
        )
        def _get_vectors(
            case_a,
            case_b,
            iteration_a,
            iteration_b,
            vector_a,
            vector_b,
            aggregation: str,
        ):
            if self.interactive:
                explorer = Explorer(env=self.env, interactive=self.interactive)
            else:
                explorer = Explorer(
                    env=self.env,
                    token=flask.request.headers["X-Auth-Request-Access-Token"],
                )

            fig = go.Figure()
            if case_a and vector_a:
                if aggregation == "aggregation":
                    fig.add_traces(
                        plotly_aggregation_traces_for_vector(
                            explorer,
                            case_id=case_a,
                            vector_name=vector_a,
                            iteration_id=iteration_a,
                            color="red",
                        )
                    )
                else:
                    fig.add_traces(
                        plotly_realization_traces_for_vector(
                            explorer,
                            case_id=case_a,
                            vector_name=vector_a,
                            iteration_id=iteration_a,
                            color="red",
                        )
                    )
            if case_b and vector_b:
                if aggregation == "aggregation":
                    fig.add_traces(
                        plotly_aggregation_traces_for_vector(
                            explorer,
                            case_id=case_b,
                            vector_name=vector_b,
                            iteration_id=iteration_b,
                            color="blue",
                        )
                    )
                else:
                    fig.add_traces(
                        plotly_realization_traces_for_vector(
                            explorer,
                            case_id=case_b,
                            vector_name=vector_b,
                            iteration_id=iteration_b,
                            color="blue",
                        )
                    )

            return fig


def plotly_realization_traces_for_vector(
    explorer: Explorer, case_id: str, iteration_id: str, vector_name: str, color: str
):

    df = get_vector_data(
        explorer, case_uuid=case_id, iteration_id=iteration_id, vector_name="DATE"
    )
    df[vector_name] = get_vector_data(
        explorer, case_uuid=case_id, vector_name=vector_name, iteration_id=iteration_id
    )[vector_name]
    name = f"{explorer.get_case_by_id(case_id).case_name}-{iteration_id}-{vector_name}"
    return [
        go.Scatter(
            x=real_df["DATE"],
            y=real_df[vector_name],
            mode="lines",
            name=name,
            line={"color": color},
            legendgroup=name,
            hovertemplate=f"Realization: {real}",
            showlegend=idx == 0,
        )
        for idx, (real, real_df) in enumerate(df.groupby("REAL"))
    ]


def calc_series_statistics(
    df: pd.DataFrame, vector_name: str, refaxis: str = "DATE"
) -> pd.DataFrame:

    # Invert p10 and p90 due to oil industry convention.
    def p10(x: List[float]) -> np.floating:
        return np.nanpercentile(x, q=90)

    def p90(x: List[float]) -> np.floating:
        return np.nanpercentile(x, q=10)

    # Calculate statistics, ignoring NaNs.
    stat_df = (
        df[[refaxis, vector_name]]
        .groupby(refaxis)
        .agg([np.nanmean, np.nanmin, np.nanmax, p10, p90])
        .reset_index()  # level=["label", refaxis], col_level=0)
    )
    # Rename nanmin, nanmax and nanmean to min, max and mean.
    col_stat_label_map = {
        "nanmin": "min",
        "nanmax": "max",
        "nanmean": "mean",
        "p10": "high_p10",
        "p90": "low_p90",
    }
    stat_df.rename(columns=col_stat_label_map, level=1, inplace=True)

    return stat_df


def plotly_aggregation_traces_for_vector(
    explorer: Explorer, case_id: str, iteration_id: str, vector_name: str, color: str
) -> dict:
    case_name = f"{explorer.get_case_by_id(case_id).case_name}-{iteration_id}"
    df = get_vector_data(
        explorer, case_uuid=case_id, iteration_id=iteration_id, vector_name="DATE"
    )
    df[vector_name] = get_vector_data(
        explorer, case_uuid=case_id, vector_name=vector_name, iteration_id=iteration_id
    )[vector_name]
    stat_df = calc_series_statistics(df, vector_name)
    traces = [
        {
            "line": {"dash": "dot", "width": 3},
            "x": stat_df["DATE"],
            "y": stat_df[(vector_name, "max")],
            "hovertemplate": f"Calculation: {'max'},Case: {case_name}",
            "name": case_name,
            "legendgroup": case_name,
            "showlegend": False,
            "marker": {"color": color},
            "mode": "lines",
        },
        {
            "line": {"dash": "dash"},
            "x": stat_df["DATE"],
            "y": stat_df[(vector_name, "high_p10")],
            "hovertemplate": f"Calculation: {'high_p10'},Case: {case_name}",
            "name": case_name,
            "legendgroup": case_name,
            "showlegend": False,
            "marker": {"color": color},
            "mode": "lines",
        },
        {
            "x": stat_df["DATE"],
            "y": stat_df[(vector_name, "mean")],
            "hovertemplate": f"Calculation: {'mean'}, Case: {case_name}",
            "name": case_name,
            "legendgroup": case_name,
            # "fill": "tonexty",
            "marker": {"color": color},
            "mode": "lines",
            "line": {"width": 3},
        },
        {
            "line": {"dash": "dash"},
            "x": stat_df["DATE"],
            "y": stat_df[(vector_name, "low_p90")],
            "hovertemplate": f"Calculation: {'low_p90'}, Case: {case_name}",
            "name": case_name,
            "legendgroup": case_name,
            "showlegend": False,
            # "fill": "tonexty",
            "marker": {"color": color},
            "mode": "lines",
        },
        {
            "line": {"dash": "dot", "width": 1},
            "x": stat_df["DATE"],
            "y": stat_df[(vector_name, "min")],
            "hovertemplate": f"Calculation: {'min'}, Case: {case_name}",
            "name": case_name,
            "legendgroup": case_name,
            "showlegend": False,
            "marker": {"color": color},
            "mode": "lines",
        },
    ]
    return traces
