from typing import List

from dash.development.base_component import Component
from dash import html

import webviz_core_components as wcc

from webviz_config.utils import StrEnum
from webviz_config.webviz_plugin_subclasses import ViewABC


class PlotView(ViewABC):
    class Ids(StrEnum):
        GRAPH = "graph"

    def __init__(self) -> None:
        super().__init__("Shared settings")

    def layout(self) -> List[Component]:
        return [
            html.Div(
                children=[
                    html.Div(id=self.register_component_unique_id(PlotView.Ids.GRAPH))
                ]
            )
        ]
