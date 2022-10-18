from typing import List
from dash import callback, Input, Output, State
from webviz_config import WebvizPluginABC
from webviz_config.utils import StrEnum
from webviz_config.webviz_instance_info import WEBVIZ_INSTANCE_INFO, WebvizRunMode
from fmu.sumo.explorer import Explorer, Case
from .views.time_series.view import TimeSeriesView
from ._shared_settings import SharedSettingsGroup


class SumoTimeSeries(WebvizPluginABC):
    class Ids(StrEnum):
        PLOT_VIEW = "plot-view"
        SHARED_SETTINGS = "shared-settings"

    def __init__(self, env: str = "dev", initial_case_name: List[str] = None):
        super().__init__(stretch=True)
        self.interactive = WEBVIZ_INSTANCE_INFO.run_mode != WebvizRunMode.PORTABLE
        self.settings_group = SharedSettingsGroup(
            env=env, initial_case_name=initial_case_name, interactive=self.interactive
        )
        self.add_shared_settings_group(
            self.settings_group, SumoTimeSeries.Ids.SHARED_SETTINGS
        )

        self.add_view(
            TimeSeriesView(
                env=env,
                interactive=self.interactive,
                case_a_selector=self.settings_group.case_a_selector,
                case_b_selector=self.settings_group.case_b_selector,
            ),
            SumoTimeSeries.Ids.PLOT_VIEW,
        )
