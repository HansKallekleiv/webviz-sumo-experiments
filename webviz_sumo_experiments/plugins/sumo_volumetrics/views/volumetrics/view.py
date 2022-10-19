from typing import List

import flask
from dash.development.base_component import Component
from dash import html, callback, Input, Output, no_update, State, MATCH, ALL
import numpy as np
import pandas as pd
import webviz_core_components as wcc
import plotly.graph_objects as go
import plotly.express as px
from fmu.sumo.explorer import Explorer
from ...sumo_requests import (
    get_volumetrics_names_for_case_uuid,
    get_ensemble_volumetrics,
)
from webviz_config.utils import StrEnum
from webviz_config.webviz_plugin_subclasses import ViewABC, ViewElementABC
from .volumetric_settings import VolumetricsSettings
from .case_settings import CaseSettings


class VolumetricsPlot(ViewElementABC):
    class Ids(StrEnum):
        GRAPH = "graph"

    def __init__(self) -> None:
        super().__init__(flex_grow=8)

    def inner_layout(self):
        return html.Div(
            style={"height": "90vh"},
            children=[
                wcc.Graph(
                    id=self.register_component_unique_id(VolumetricsPlot.Ids.GRAPH),
                    config={
                        "responsive": True,
                    },
                )
            ],
        )


class VolumetricsView(ViewABC):
    class Ids(StrEnum):
        PLOT = "volumetrics-plot"
        CASESETTINGS = "case-settings"
        VOLSETTINGS = "volumetrics-settings"

    def __init__(
        self,
        env: str,
        initial_case_name: str,
        interactive: bool,
    ) -> None:
        super().__init__("Vol")
        self.add_settings_group(
            CaseSettings(
                env=env, initial_case_name=initial_case_name, interactive=interactive
            ),
            VolumetricsView.Ids.CASESETTINGS,
        )
        self.add_settings_group(VolumetricsSettings(), VolumetricsView.Ids.VOLSETTINGS)
        self.add_view_element(VolumetricsPlot(), VolumetricsView.Ids.PLOT)
        self.initial_case_name = initial_case_name
        self.env = env
        self.interactive = interactive
        self.set_callbacks()

    def layout(self) -> List[Component]:
        return [
            html.Div(
                children=[
                    html.Div(
                        id=self.register_component_unique_id(VolumetricsView.Ids.PLOT)
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

        def vol_settings_id(**kwargs):
            comp_id = {
                "id": self.settings_groups()[1].get_unique_id().to_string(),
            }
            comp_id.update(kwargs)
            return comp_id

        def view_comp_id(comp: str):
            return self.view_elements()[0].component_unique_id(comp).to_string()

        @callback(
            Output(
                vol_settings_id(case=MATCH, comp="name"),
                "options",
            ),
            Output(
                vol_settings_id(case=MATCH, comp="name"),
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
                vol_settings_id(case=MATCH, comp="name"),
                "value",
            ),
        )
        def _get_vol_names(case, iteration, current_volname):
            if self.interactive:
                explorer = Explorer(env=self.env, interactive=self.interactive)
            else:
                explorer = Explorer(
                    env=self.env,
                    token=flask.request.headers["X-Auth-Request-Access-Token"],
                )

            volnames = get_volumetrics_names_for_case_uuid(
                explorer, case_uuid=case, iteration_id=iteration
            )

            if volnames:
                opts = [{"label": volname, "value": volname} for volname in volnames]
                val = current_volname if current_volname in volnames else volnames[0]
            else:
                opts = []
                val = None

            return (opts, val)

        @callback(
            Output(
                vol_settings_id(case=MATCH, comp="response"),
                "options",
            ),
            Output(
                vol_settings_id(case=MATCH, comp="response"),
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
            Input(
                vol_settings_id(case=MATCH, comp="name"),
                "value",
            ),
            State(
                vol_settings_id(case=MATCH, comp="response"),
                "value",
            ),
        )
        def _get_vol_responses(
            case,
            iteration,
            volname,
            current_volresponse,
        ):
            if self.interactive:
                explorer = Explorer(env=self.env, interactive=self.interactive)
            else:
                explorer = Explorer(
                    env=self.env,
                    token=flask.request.headers["X-Auth-Request-Access-Token"],
                )
            vol_df = get_ensemble_volumetrics(
                explorer=explorer,
                case_uuid=case,
                iteration_id=iteration,
                volumetric_name=volname,
            )
            if vol_df is None:
                return [], None
            responses = [
                col
                for col in vol_df.columns
                if col not in ["ZONE", "REGION", "LICENSE", "FACIES", "REAL"]
            ]
            if current_volresponse in responses:
                response = current_volresponse
            elif "STOIIP_OIL" in responses:
                response = "STOIIP_OIL"
            else:
                response = responses[0]
            return [{"label": resp, "value": resp} for resp in responses], response

        @callback(
            Output(view_comp_id(VolumetricsPlot.Ids.GRAPH), "figure"),
            Input(
                case_settings_id(case=ALL, comp="case"),
                "value",
            ),
            Input(
                case_settings_id(case=ALL, comp="iteration"),
                "value",
            ),
            Input(
                vol_settings_id(case=ALL, comp="name"),
                "value",
            ),
            Input(
                vol_settings_id(case=ALL, comp="response"),
                "value",
            ),
        )
        def _get_vectors(
            cases,
            iterations,
            volnames,
            volresponses,
        ):
            if self.interactive:
                explorer = Explorer(env=self.env, interactive=self.interactive)
            else:
                explorer = Explorer(
                    env=self.env,
                    token=flask.request.headers["X-Auth-Request-Access-Token"],
                )
            if not cases or not iterations or not volnames or not volresponses:
                return no_update

            dfs = []
            for case, iteration, volname, volresponse in zip(
                cases, iterations, volnames, volresponses
            ):
                vol_df = get_ensemble_volumetrics(
                    explorer=explorer,
                    case_uuid=case,
                    iteration_id=iteration,
                    volumetric_name=volname,
                )
                case_name = explorer.get_case_by_id(case).case_name
                vol_df["CASE"] = case_name
                vol_df["value"] = vol_df[volresponse]
                vol_df[
                    "response_name"
                ] = f"{case_name}-{iteration}-{volname}-{volresponse}"
                dfs.append(vol_df)

            df = pd.concat(dfs)
            return px.histogram(df, x="value", color="response_name")
