from io import StringIO
import logging
from typing import List

import flask
from dash.development.base_component import Component
from dash import html, dcc, callback, Input, Output, no_update, State, MATCH, ALL
import numpy as np
import pandas as pd
import webviz_core_components as wcc
import plotly.graph_objects as go
import plotly.express as px
from fmu.sumo.explorer import Explorer
from webviz_config.utils import StrEnum
from webviz_config.webviz_plugin_subclasses import ViewABC, ViewElementABC

from webviz_sumo_experiments import PerfTimer
from .time_series_settings import TimeSeriesSettings
from .case_settings import CaseSettings
from ...sumo_requests import get_smry_vector_names, get_vector_data


class TimeSeriesPlot(ViewElementABC):
    class Ids(StrEnum):
        GRAPH = "graph"
        INTERVAL = "interval"
        LOG = "log"
        CLEARLOG = "clearlog"

    def __init__(self) -> None:
        super().__init__(flex_grow=8)

    def inner_layout(self):
        return html.Div(
            children=[
                html.Div(
                    style={"height": "50vh"},
                    children=wcc.Graph(
                        id=self.register_component_unique_id(TimeSeriesPlot.Ids.GRAPH),
                        config={
                            "responsive": True,
                        },
                    ),
                ),
                dcc.Interval(
                    id=self.register_component_unique_id(TimeSeriesPlot.Ids.INTERVAL),
                    interval=1000,
                    n_intervals=0,
                ),
                html.Pre(
                    style={"height": "40vh", "overflow": "scroll"},
                    id=self.register_component_unique_id(TimeSeriesPlot.Ids.LOG),
                ),
                html.Button(
                    children="Clear",
                    id=self.register_component_unique_id(TimeSeriesPlot.Ids.CLEARLOG),
                ),
            ],
        )


class TimeSeriesView(ViewABC):
    class Ids(StrEnum):
        PLOT = "plot"
        TIMESETTINGS = "timeseries-settings"
        CASESETTINGS = "case-settings"

    def __init__(
        self,
        env: str,
        interactive: bool,
        initial_case_name: str = None,
    ) -> None:
        super().__init__("Shared settings")
        logFormatter = logging.Formatter(
            fmt="%(asctime)s:\t%(name)s:\t%(levelname)s:\t%(message)s"
        )
        self.log_stream = StringIO()
        self.logger = logging.getLogger("TimeSeries")
        self.logger.setLevel(logging.INFO)
        stream_handler = logging.StreamHandler(self.log_stream)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(logFormatter)
        self.logger.addHandler(stream_handler)
        self.add_settings_group(
            CaseSettings(
                env=env,
                initial_case_name=initial_case_name,
                interactive=interactive,
                logger=self.logger,
            ),
            TimeSeriesView.Ids.CASESETTINGS,
        )
        self.add_settings_group(TimeSeriesSettings(), TimeSeriesView.Ids.TIMESETTINGS)
        self.add_view_element(TimeSeriesPlot(), TimeSeriesView.Ids.PLOT)

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
        def case_settings_id(**kwargs):
            comp_id = {
                "id": self.settings_groups()[0].get_unique_id().to_string(),
            }
            comp_id.update(kwargs)
            return comp_id

        def vector_settings(**kwargs):
            comp_id = {
                "id": self.settings_groups()[1].get_unique_id().to_string(),
            }
            comp_id.update(kwargs)
            return comp_id

        def view_comp_id(comp: str):
            return (
                self.view_element(TimeSeriesView.Ids.PLOT)
                .component_unique_id(comp)
                .to_string()
            )

        @callback(
            Output(
                vector_settings(case=MATCH, comp="vector"),
                "options",
            ),
            Output(
                vector_settings(case=MATCH, comp="vector"),
                "value",
            ),
            Input(
                case_settings_id(case=MATCH, comp="case"),
                "value",
            ),
            Input(
                case_settings_id(case=MATCH, comp="iteration"),
                "value",
            ),
            State(
                vector_settings(case=MATCH, comp="vector"),
                "value",
            ),
        )
        def _get_vectors(case_uuid, iteration_id, current_vector):
            if self.interactive:
                explorer = Explorer(env=self.env, interactive=self.interactive)
            else:
                explorer = Explorer(
                    env=self.env,
                    token=flask.request.headers["X-Auth-Request-Access-Token"],
                )
            timer = PerfTimer()

            vectors = get_smry_vector_names(
                explorer=explorer, case_uuid=case_uuid, iteration_id=iteration_id
            )
            self.logger.info(f"get_smry_vector_names: {timer.lap_s()}")
            if vectors:
                vec_opts = [{"label": vector, "value": vector} for vector in vectors]
                vec_val = current_vector if current_vector in vectors else vectors[0]
            else:
                vec_opts = []
                vec_val = None

            return (vec_opts, vec_val)

        @callback(
            Output(view_comp_id(TimeSeriesPlot.Ids.GRAPH), "figure"),
            Input(
                case_settings_id(case=ALL, comp="case"),
                "value",
            ),
            Input(
                case_settings_id(case=ALL, comp="iteration"),
                "value",
            ),
            Input(
                vector_settings(case=ALL, comp="vector"),
                "value",
            ),
            Input(
                self.settings_groups()[1]
                .component_unique_id(TimeSeriesSettings.Ids.AGGREGATION)
                .to_string(),
                "value",
            ),
        )
        def _get_vectors(
            cases,
            iterations,
            vectors,
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
            if not cases or not iterations or not vectors:
                return no_update
            timer = PerfTimer()
            try:
                for case, iteration, vector, color in zip(
                    cases, iterations, vectors, ["red", "blue"]
                ):

                    if (
                        case is not None
                        and iteration is not None
                        and vector is not None
                    ):
                        df = get_vector_data(
                            explorer,
                            case_uuid=case,
                            iteration_id=iteration,
                            vector_name="DATE",
                        )
                        self.logger.info(f"got date data : {timer.lap_s()}")
                        df[vector] = get_vector_data(
                            explorer,
                            case_uuid=case,
                            vector_name=vector,
                            iteration_id=iteration,
                        )[vector]
                        self.logger.info(f"got vector data : {timer.lap_s()}")
                        if aggregation == "aggregation":
                            fig.add_traces(
                                plotly_aggregation_traces_for_vector(
                                    df,
                                    case_id=explorer.get_case_by_id(case).case_name,
                                    vector_name=vector,
                                    iteration_id=iteration,
                                    color=color,
                                )
                            )
                        else:
                            fig.add_traces(
                                plotly_realization_traces_for_vector(
                                    df,
                                    case_id=explorer.get_case_by_id(case).case_name,
                                    vector_name=vector,
                                    iteration_id=iteration,
                                    color=color,
                                )
                            )

            except TypeError:
                self.logger.info(
                    f"Failed to get vector data for case {case} : {timer.lap_s()}"
                )
                return no_update

            return fig

        @callback(
            Output(view_comp_id(TimeSeriesPlot.Ids.LOG), "children"),
            Input(view_comp_id(TimeSeriesPlot.Ids.INTERVAL), "n_intervals"),
        )
        def _update_log(_):
            logstring = self.log_stream.getvalue()
            logstring = logstring.split("\n")
            logstring.reverse()
            logstring = ("\n").join(logstring)
            return logstring

        @callback(
            Output(view_comp_id(TimeSeriesPlot.Ids.LOG), "id"),
            Input(view_comp_id(TimeSeriesPlot.Ids.CLEARLOG), "n_clicks"),
            prevent_initial_call=True,
        )
        def _update_log(_):
            self.log_stream.truncate(0)
            self.log_stream.seek(0)
            return no_update


def plotly_realization_traces_for_vector(
    df: pd.DataFrame, case_name: str, iteration_id: str, vector_name: str, color: str
):

    name = f"{case_name}-{iteration_id}-{vector_name}"
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
    df: pd.DataFrame, case_name: str, iteration_id: str, vector_name: str, color: str
) -> dict:
    case_name = f"{case_name}-{iteration_id}"

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
