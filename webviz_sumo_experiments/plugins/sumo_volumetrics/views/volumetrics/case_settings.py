from typing import List

import flask
from dash.development.base_component import Component
from dash import html, dcc, callback, Input, Output, State, MATCH, ALL
from fmu.sumo.explorer import Explorer, Case
import webviz_core_components as wcc

from webviz_config.utils import StrEnum
from webviz_config.webviz_plugin_subclasses import SettingsGroupABC
from webviz_sumo_experiments import PerfTimer
from ...sumo_requests import get_case_uuids_with_volumetrics


class CaseSettings(SettingsGroupABC):
    class Ids(StrEnum):
        DUMMY_TRIGGER = "dummy-trigger"
        FIELD = "sumo-field"
        CASE = "sumo-case"
        ITERATION = "sumo-iteration"

    def __init__(
        self, env: str, initial_case_name: List[str], interactive: bool, logger
    ) -> None:
        super().__init__("Sumo cases")
        self.logger = logger
        self.env = env
        self.initial_case_name = initial_case_name
        self.interactive = interactive

    def layout(self) -> List[Component]:
        return [
            html.Div(
                children=[
                    html.Div(
                        style={"display": "none"},
                        id=self.register_component_unique_id(
                            CaseSettings.Ids.DUMMY_TRIGGER
                        ),
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Field",
                        id=self.register_component_unique_id(CaseSettings.Ids.FIELD),
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Case A",
                        id={
                            "case": "A",
                            "comp": "case",
                            "id": self.get_unique_id().to_string(),
                        },
                        placeholder="No valid cases",
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Iteration A",
                        id={
                            "case": "A",
                            "comp": "iteration",
                            "id": self.get_unique_id().to_string(),
                        },
                        placeholder="No valid iterations",
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Case B",
                        id={
                            "case": "B",
                            "comp": "case",
                            "id": self.get_unique_id().to_string(),
                        },
                        placeholder="No valid cases",
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Iteration B",
                        id={
                            "case": "B",
                            "comp": "iteration",
                            "id": self.get_unique_id().to_string(),
                        },
                        placeholder="No valid iterations",
                    ),
                ]
            )
        ]

    def set_callbacks(self):
        def comp_id(**kwargs):
            comp_id = {
                "id": self.get_unique_id().to_string(),
            }
            comp_id.update(kwargs)
            return comp_id

        @callback(
            Output(
                self.component_unique_id(CaseSettings.Ids.FIELD).to_string(),
                "options",
            ),
            Output(
                self.component_unique_id(CaseSettings.Ids.FIELD).to_string(),
                "value",
            ),
            Input(
                self.component_unique_id(CaseSettings.Ids.DUMMY_TRIGGER).to_string(),
                "children",
            ),
        )
        def _set_field(_):
            if self.interactive:
                explorer = Explorer(env=self.env, interactive=self.interactive)
            else:
                explorer = Explorer(
                    env=self.env,
                    token=flask.request.headers["X-Auth-Request-Access-Token"],
                )
            timer = PerfTimer()
            fields = explorer.get_fields()
            self.logger.info(f"Got Sumo fields in {timer.lap_s()}s")
            return [
                {"label": field, "value": field} for field in list(fields.keys())
            ], list(fields.keys())[0]

        @callback(
            Output(
                comp_id(comp="case", case=ALL),
                "options",
            ),
            Output(
                comp_id(comp="case", case=ALL),
                "value",
            ),
            Input(
                self.component_unique_id(CaseSettings.Ids.FIELD).to_string(),
                "value",
            ),
        )
        def _set_cases(field: str):
            if self.interactive:
                explorer = Explorer(env=self.env, interactive=self.interactive)
            else:
                explorer = Explorer(
                    env=self.env,
                    token=flask.request.headers["X-Auth-Request-Access-Token"],
                )
            timer = PerfTimer()
            case_ids = get_case_uuids_with_volumetrics(explorer, field)
            self.logger.info(f"Got Sumo cases with volumetrics in {timer.lap_s()}")
            cases = [explorer.get_case_by_id(case_id) for case_id in case_ids]

            if cases:
                initial_case_id = cases[0].sumo_id
                if self.initial_case_name is not None:
                    for case in cases:
                        if self.initial_case_name in case.case_name:
                            initial_case_id = case.sumo_id
                            break
                return (
                    [
                        [
                            {"label": case.case_name, "value": case.sumo_id}
                            for case in cases
                        ],
                        [
                            {"label": case.case_name, "value": case.sumo_id}
                            for case in cases
                        ],
                    ],
                    [
                        initial_case_id,
                        initial_case_id,
                    ],
                )
            return [[], []], [None, None]

        @callback(
            Output(
                comp_id(comp="iteration", case=MATCH),
                "options",
            ),
            Output(
                comp_id(comp="iteration", case=MATCH),
                "value",
            ),
            Input(
                comp_id(comp="case", case=MATCH),
                "value",
            ),
        )
        def _set_iterations(case_id: str):
            if self.interactive:
                explorer = Explorer(env=self.env, interactive=self.interactive)
            else:
                explorer = Explorer(
                    env=self.env,
                    token=flask.request.headers["X-Auth-Request-Access-Token"],
                )
            timer = PerfTimer()
            iterations = (
                explorer.get_case_by_id(case_id).get_iterations() if case_id else None
            )
            self.logger.info(f"Got Sumo iterations in {timer.lap_s()}")
            iteration_opts = (
                [
                    {"label": iteration["name"], "value": iteration["id"]}
                    for iteration in iterations
                ]
                if iterations
                else []
            )
            iteration_val = iterations[0]["id"] if iterations else None

            return iteration_opts, iteration_val
