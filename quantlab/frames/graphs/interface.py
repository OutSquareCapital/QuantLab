from abc import ABC, abstractmethod
from quantlab.frames.graphs.design import FigureSetup, Colors
import plotly.graph_objects as go  # type: ignore
from quantlab.frames.main import FrameBase

class Graph(ABC):
    def __init__(self, formatted_data: FrameBase) -> None:
        self.figure = go.Figure()
        self.setup_figure(formatted_data=formatted_data)
        self._setup_general_design()
        self._setup_axes()
        self.figure.show()  # type: ignore

    @abstractmethod
    def setup_figure(self, formatted_data: FrameBase) -> None:
        raise NotImplementedError

    def _setup_general_design(self) -> None:
        self.figure.update_layout(  # type: ignore
            font=FigureSetup.TEXT_FONT.value,
            autosize=True,
            margin=dict(l=30, r=30, t=40, b=30),
            paper_bgcolor=Colors.BLACK,
            plot_bgcolor=Colors.BLACK,
            legend={
                "title_font": FigureSetup.LEGEND_TITLE_FONT.value,
            },
        )

    def _setup_axes(self) -> None:
        self.figure.update_yaxes(  # type: ignore
            showgrid=False, automargin=True
        )

        self.figure.update_xaxes(  # type: ignore
            showgrid=False, automargin=True
        )
