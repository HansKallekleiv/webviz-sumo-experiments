from typing import List

from dash.development.base_component import Component
from dash import html, dcc, callback, Input, Output, State
from fmu.sumo.explorer import Explorer, Case
import webviz_core_components as wcc

from webviz_config.utils import StrEnum
from webviz_config.webviz_plugin_subclasses import SettingsGroupABC


class TimeSeriesSettings(SettingsGroupABC):
    class Ids(StrEnum):
        VECTOR_A = "sumo-vectora"
        VECTOR_B = "sumo-vectorb"
        AGGREGATION = "sumo-aggregation"

    def __init__(self) -> None:
        super().__init__("Time Series")

    def layout(self) -> List[Component]:
        return [
            html.Div(
                children=[
                    wcc.Dropdown(
                        clearable=False,
                        label="Vector Case A",
                        id=self.register_component_unique_id(
                            TimeSeriesSettings.Ids.VECTOR_A
                        ),
                        placeholder="No vectors found",
                    ),
                    wcc.Dropdown(
                        clearable=False,
                        label="Vector Case B",
                        id=self.register_component_unique_id(
                            TimeSeriesSettings.Ids.VECTOR_B
                        ),
                        placeholder="Try '01_drogon_design_summary'",
                    ),
                    wcc.RadioItems(
                        label="Mode",
                        id=self.register_component_unique_id(
                            TimeSeriesSettings.Ids.AGGREGATION
                        ),
                        options=[
                            {"label": "Realization", "value": "realization"},
                            {"label": "Aggregation", "value": "aggregation"},
                        ],
                        value="realization",
                    ),
                ]
            )
        ]
