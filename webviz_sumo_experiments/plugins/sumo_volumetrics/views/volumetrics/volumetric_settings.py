from typing import List

from dash.development.base_component import Component
from dash import html, dcc, callback, Input, Output, State
from fmu.sumo.explorer import Explorer, Case
import webviz_core_components as wcc

from webviz_config.utils import StrEnum
from webviz_config.webviz_plugin_subclasses import SettingsGroupABC


class VolumetricsSettings(SettingsGroupABC):
    class Ids(StrEnum):
        VOL_NAME = "sumo-volname"

        VOL_RESPONSE = "sumo-volresponse"

    def __init__(self) -> None:
        super().__init__("Volumetrics")

    def layout(self) -> List[Component]:
        return [
            html.Div(
                children=[
                    wcc.Dropdown(
                        clearable=False,
                        label="Volumetric table Case A",
                        id={
                            "case": "A",
                            "comp": "name",
                            "id": self.get_unique_id().to_string(),
                        },
                        placeholder="No tables found",
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Volumetric response Case A",
                        id={
                            "case": "A",
                            "comp": "response",
                            "id": self.get_unique_id().to_string(),
                        },
                        placeholder="No responses found",
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Volumetric table Case B",
                        id={
                            "case": "B",
                            "comp": "name",
                            "id": self.get_unique_id().to_string(),
                        },
                        placeholder="No tables found'",
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Volumetric response Case B",
                        id={
                            "case": "B",
                            "comp": "response",
                            "id": self.get_unique_id().to_string(),
                        },
                        placeholder="No responses found'",
                    ),
                ]
            )
        ]
