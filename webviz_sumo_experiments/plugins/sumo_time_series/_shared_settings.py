from typing import List

from dash.development.base_component import Component
from dash import html, dcc, callback, Input, Output, State
from fmu.sumo.explorer import Explorer, Case
import webviz_core_components as wcc

from webviz_config.utils import StrEnum
from webviz_config.webviz_plugin_subclasses import SettingsGroupABC


class SharedSettingsGroup(SettingsGroupABC):
    class Ids(StrEnum):
        FIELD = "sumo-field"
        CASE_A = "sumo-casea"
        CASE_B = "sumo-caseb"

    def __init__(self, env: str) -> None:
        super().__init__("Shared settings")
        self.env = env

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
                    wcc.Dropdown(
                        label="Field",
                        id=self.register_component_unique_id(
                            SharedSettingsGroup.Ids.FIELD
                        ),
                    ),
                    wcc.Dropdown(
                        label="Case A",
                        id=self.register_component_unique_id(
                            SharedSettingsGroup.Ids.CASE_A
                        ),
                    ),
                    wcc.Dropdown(
                        label="Case B",
                        id=self.register_component_unique_id(
                            SharedSettingsGroup.Ids.CASE_B
                        ),
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
                    SharedSettingsGroup.Ids.ENVIRONMENT
                ).to_string(),
                "data",
            ),
        )
        def _set_field(environment):
            explorer = Explorer(env=environment, interactive=True)
            fields = explorer.get_fields()
            print(fields)
            cases: List[Case] = explorer.get_cases()
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
        def _set_field(field: str, environment: str):
            explorer = Explorer(env=environment, interactive=True)

            cases: List[Case] = [
                case for case in explorer.get_cases() if case.field_name == field
            ]
            print(cases[0].fmu_id)

            return (
                [{"label": case.case_name, "value": case.sumo_id} for case in cases],
                cases[0].sumo_id,
                [{"label": case.case_name, "value": case.sumo_id} for case in cases],
                cases[0].sumo_id,
            )
