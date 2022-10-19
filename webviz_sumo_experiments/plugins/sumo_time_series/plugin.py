from typing import List
from dash import callback, Input, Output, State
from webviz_config import WebvizPluginABC
from webviz_config.utils import StrEnum
from webviz_config.webviz_instance_info import WEBVIZ_INSTANCE_INFO, WebvizRunMode
from fmu.sumo.explorer import Explorer, Case
from .views.time_series.view import TimeSeriesView


class SumoTimeSeries(WebvizPluginABC):
    class Ids(StrEnum):
        PLOT_VIEW = "plot-view"

    def __init__(self, app, env: str = "dev", initial_case_name: str = None):
        super().__init__(stretch=True)
        self.interactive = WEBVIZ_INSTANCE_INFO.run_mode != WebvizRunMode.PORTABLE

        self.add_view(
            TimeSeriesView(
                env=env,
                interactive=self.interactive,
                initial_case_name=initial_case_name,
            ),
            SumoTimeSeries.Ids.PLOT_VIEW,
        )
