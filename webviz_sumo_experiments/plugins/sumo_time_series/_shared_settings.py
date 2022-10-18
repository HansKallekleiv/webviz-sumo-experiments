from typing import List

import flask
from dash.development.base_component import Component
from dash import html, dcc, callback, Input, Output, State
from fmu.sumo.explorer import Explorer, Case
import webviz_core_components as wcc

from webviz_config.utils import StrEnum
from webviz_config.webviz_plugin_subclasses import SettingsGroupABC
from .sumo_requests import get_cases_with_smry_data


class SharedSettingsGroup(SettingsGroupABC):
    class Ids(StrEnum):
        DUMMY_TRIGGER = "dummy-trigger"
        FIELD = "sumo-field"
        CASE_A = "sumo-casea"
        CASE_B = "sumo-caseb"
        ITERATION_A = "sumo-iterationa"
        ITERATION_B = "sumo-iterationb"

    def __init__(
        self, env: str, initial_case_name: List[str], interactive: bool
    ) -> None:
        super().__init__("Sumo cases")
        self.env = env
        self.initial_case_name = initial_case_name
        self.interactive = interactive

    @property
    def case_a_selector(self):
        return self.component_unique_id(SharedSettingsGroup.Ids.CASE_A).to_string()

    @property
    def case_b_selector(self):
        return self.component_unique_id(SharedSettingsGroup.Ids.CASE_B).to_string()

    @property
    def iteration_a_selector(self):
        return self.component_unique_id(SharedSettingsGroup.Ids.ITERATION_A).to_string()

    @property
    def iteration_b_selector(self):
        return self.component_unique_id(SharedSettingsGroup.Ids.ITERATION_B).to_string()

    def layout(self) -> List[Component]:
        return [
            html.Div(
                children=[
                    html.Div(
                        style={"display": "none"},
                        id=self.register_component_unique_id(
                            SharedSettingsGroup.Ids.DUMMY_TRIGGER
                        ),
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Field",
                        id=self.register_component_unique_id(
                            SharedSettingsGroup.Ids.FIELD
                        ),
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Case A",
                        id=self.register_component_unique_id(
                            SharedSettingsGroup.Ids.CASE_A
                        ),
                        placeholder="No valid cases",
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Iteration A",
                        id=self.register_component_unique_id(
                            SharedSettingsGroup.Ids.ITERATION_A
                        ),
                        placeholder="No valid iterations",
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Case B",
                        id=self.register_component_unique_id(
                            SharedSettingsGroup.Ids.CASE_B
                        ),
                        placeholder="No valid cases",
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Iteration B",
                        id=self.register_component_unique_id(
                            SharedSettingsGroup.Ids.ITERATION_B
                        ),
                        placeholder="No valid iterations",
                    ),
                ]
            )
        ]

    def set_callbacks(self):
        @callback(
            Output(
                self.component_unique_id(SharedSettingsGroup.Ids.FIELD).to_string(),
                "options",
            ),
            Output(
                self.component_unique_id(SharedSettingsGroup.Ids.FIELD).to_string(),
                "value",
            ),
            Input(
                self.component_unique_id(
                    SharedSettingsGroup.Ids.DUMMY_TRIGGER
                ).to_string(),
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
            fields = explorer.get_fields()

            return [
                {"label": field, "value": field} for field in list(fields.keys())
            ], list(fields.keys())[0]

        @callback(
            Output(
                self.component_unique_id(SharedSettingsGroup.Ids.CASE_A).to_string(),
                "options",
            ),
            Output(
                self.component_unique_id(SharedSettingsGroup.Ids.CASE_A).to_string(),
                "value",
            ),
            Output(
                self.component_unique_id(SharedSettingsGroup.Ids.CASE_B).to_string(),
                "options",
            ),
            Output(
                self.component_unique_id(SharedSettingsGroup.Ids.CASE_B).to_string(),
                "value",
            ),
            Input(
                self.component_unique_id(SharedSettingsGroup.Ids.FIELD).to_string(),
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
            case_ids = get_cases_with_smry_data(explorer, field)
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
                        {"label": case.case_name, "value": case.sumo_id}
                        for case in cases
                    ],
                    initial_case_id,
                    [
                        {"label": case.case_name, "value": case.sumo_id}
                        for case in cases
                    ],
                    initial_case_id,
                )
            return [], None, [], None

        @callback(
            Output(
                self.component_unique_id(
                    SharedSettingsGroup.Ids.ITERATION_A
                ).to_string(),
                "options",
            ),
            Output(
                self.component_unique_id(
                    SharedSettingsGroup.Ids.ITERATION_A
                ).to_string(),
                "value",
            ),
            Output(
                self.component_unique_id(
                    SharedSettingsGroup.Ids.ITERATION_B
                ).to_string(),
                "options",
            ),
            Output(
                self.component_unique_id(
                    SharedSettingsGroup.Ids.ITERATION_B
                ).to_string(),
                "value",
            ),
            Input(
                self.component_unique_id(SharedSettingsGroup.Ids.CASE_A).to_string(),
                "value",
            ),
            Input(
                self.component_unique_id(SharedSettingsGroup.Ids.CASE_B).to_string(),
                "value",
            ),
        )
        def _set_iterations(case_a_id: str, case_b_id: str):
            if self.interactive:
                explorer = Explorer(env=self.env, interactive=self.interactive)
            else:
                explorer = Explorer(
                    env=self.env,
                    token=flask.request.headers["X-Auth-Request-Access-Token"],
                )
            iterations_a = (
                explorer.get_case_by_id(case_a_id).get_iterations()
                if case_a_id
                else None
            )
            iterations_b = (
                explorer.get_case_by_id(case_b_id).get_iterations()
                if case_b_id
                else None
            )
            iteration_a_opts = (
                [
                    {"label": iteration["name"], "value": iteration["id"]}
                    for iteration in iterations_a
                ]
                if iterations_a
                else []
            )
            iteration_a_val = iterations_a[0]["id"] if iterations_a else None

            iteration_b_opts = (
                [
                    {"label": iteration["name"], "value": iteration["id"]}
                    for iteration in iterations_b
                ]
                if iterations_a
                else []
            )
            iteration_b_val = iterations_b[0]["id"] if iterations_b else None
            return iteration_a_opts, iteration_a_val, iteration_b_opts, iteration_b_val
