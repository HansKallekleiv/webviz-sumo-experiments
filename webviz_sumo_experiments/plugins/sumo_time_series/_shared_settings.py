from typing import List

import flask
from dash.development.base_component import Component
from dash import html, dcc, callback, Input, Output, State
from fmu.sumo.explorer import Explorer, Case
import webviz_core_components as wcc

from webviz_config.utils import StrEnum
from webviz_config.webviz_plugin_subclasses import SettingsGroupABC


class SharedSettingsGroup(SettingsGroupABC):
    class Ids(StrEnum):
        DUMMY_TRIGGER = "dummy-trigger"
        FIELD = "sumo-field"
        CASE_A = "sumo-casea"
        CASE_B = "sumo-caseb"

    def __init__(
        self, env: str, valid_case_names: List[str], interactive: bool
    ) -> None:
        super().__init__("Sumo cases")
        self.env = env
        self.valid_case_names = valid_case_names
        self.interactive = interactive

    @property
    def case_a_selector(self):
        return self.component_unique_id(SharedSettingsGroup.Ids.CASE_A).to_string()

    @property
    def case_b_selector(self):
        return self.component_unique_id(SharedSettingsGroup.Ids.CASE_B).to_string()

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
                        label="Case B",
                        id=self.register_component_unique_id(
                            SharedSettingsGroup.Ids.CASE_B
                        ),
                        placeholder="No valid cases",
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

            cases: List[Case] = [
                case for case in explorer.get_cases() if case.field_name == field
            ]
            if self.valid_case_names is not None:
                cases = [
                    case for case in cases if case.case_name in self.valid_case_names
                ]
            if cases:
                return (
                    [
                        {"label": case.case_name, "value": case.sumo_id}
                        for case in cases
                    ],
                    cases[0].sumo_id,
                    [
                        {"label": case.case_name, "value": case.sumo_id}
                        for case in cases
                    ],
                    cases[0].sumo_id,
                )
            return [], None, [], None
