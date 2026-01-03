import matplotlib
matplotlib.use('Agg')  # Set backend before any pyplot imports

from .line import generate_line_chart
from .area import generate_area_chart
from .bar import generate_bar_chart
from .boxplot import generate_boxplot_chart
from .column import generate_column_chart
from .funnel import generate_funnel_chart
from .histogram import generate_histogram_chart
from .liquid import generate_liquid_chart
from .network_graph import generate_network_graph_chart
from .pie import generate_pie_chart
from .radar import generate_radar_chart
from .scatter import generate_scatter_chart
from .treemap import generate_treemap_chart
from .venn import generate_venn_chart
from .waterfall import generate_waterfall_chart
from .word_cloud import generate_word_cloud_chart

__all__ = [
    "generate_line_chart",
    "generate_area_chart",
    "generate_bar_chart",
    "generate_boxplot_chart",
    "generate_column_chart",
    "generate_funnel_chart",
    "generate_histogram_chart",
    "generate_liquid_chart",
    "generate_network_graph_chart",
    "generate_pie_chart",
    "generate_radar_chart",
    "generate_scatter_chart",
    "generate_treemap_chart",
    "generate_venn_chart",
    "generate_waterfall_chart",
    "generate_word_cloud_chart",
]
