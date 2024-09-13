from .base import BaseRenderer
from ..primitives import Entity, Relation

from itertools import cycle
from pyecharts import options as opts
from pyecharts.charts import Graph
import json


class PyechartsRenderer(BaseRenderer):
    """
    PyechartsRenderer is a renderer that uses Pyecharts to visualize the entity-relationship graph.

    Args:
        repulsion (int): The repulsion force between nodes. Defaults to 2000.
        title (str): The title of the graph. Defaults to "Entity-Relationship Graph".

    Returns:
        Graph: A Pyecharts Graph object representing the entity-relationship graph.
    """

    def __init__(self, repulsion: int = 2000, title: str = "Entity-Relationship Graph"):
        self.repulsion = repulsion
        self.title = title
        self.color_palette = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
        ]  # List of colors
        self.color_cycle = cycle(self.color_palette)  # Create a cycle of colors for reuse

    def assign_colors(self, entities: list[Entity]) -> dict:
        """Assign colors to each unique entity type dynamically."""
        type_to_color = {}
        for entity in entities:
            if entity.type not in type_to_color:
                type_to_color[entity.type] = next(self.color_cycle)  # Assign a new color
        return type_to_color

    def extract_tooltip_info(self, attributes: dict) -> str:
        """Extract information for the tooltip. Convert nested attributes to a readable JSON format."""
        return json.dumps(attributes, indent=2)  # Formats attributes as a pretty JSON string

    def render(self, entities: list[Entity], relations: list[Relation], output_path: str = None) -> Graph:
        # Assign colors dynamically based on the entity type
        type_to_color = self.assign_colors(entities)

        # Prepare nodes as dictionaries, with labels showing only the entity ID and tooltips showing detailed info
        nodes = [
            {
                "name": entity.id,
                "symbolSize": 50,  # Adjust node size
                "label": {
                    "formatter": f"{entity.id}"  # Show only the entity id on the node
                },
                "value": entity.type,  # Use entity type as the value
                "tooltip": {
                    "formatter": f"Type: {entity.type}\n{self.extract_tooltip_info(entity.attributes)}"
                },  # Tooltip shows detailed attributes (nested data as JSON)
                "itemStyle": {"color": type_to_color[entity.type]},  # Use dynamically assigned color
            }
            for entity in entities
        ]

        # Prepare links based only on actual relations, with tooltips disabled
        links = [
            {"source": relation.source, "target": relation.target, "tooltip": {"show": False}}
            for relation in relations
        ]

        # Create the graph
        graph = (
            Graph()
            .add(
                "",
                nodes,
                links,
                layout="force",  # Use force-directed layout to allow drag-and-drop
                repulsion=self.repulsion,  # Controls the repulsion force between nodes
                is_roam=True,  # Allow zooming and panning
                is_draggable=True,  # Enable dragging of nodes
                edge_symbol=["none", "arrow"],  # Add arrows to the links
                edge_symbol_size=[10, 10],  # Size of the arrow
                linestyle_opts=opts.LineStyleOpts(width=1, curve=0.2, opacity=0.7),  # Customize the lines
                label_opts=opts.LabelOpts(is_show=True, position="right"),  # Show labels for the nodes
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title=self.title),
                toolbox_opts=opts.ToolboxOpts(
                    is_show=True,
                    feature=opts.ToolBoxFeatureOpts(
                        save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(
                            title="Save as Image",  # Set label to English
                            name="graph_image",
                        ),
                        restore=opts.ToolBoxFeatureRestoreOpts(
                            title="Restore",  # Set label to English
                        ),
                        data_view=opts.ToolBoxFeatureDataViewOpts(
                            title="Data View",
                            lang=["Data View", "Close", "Refresh"],  # Set language to English
                        ),
                        magic_type=None,  # Remove the magic type icons (the graph switching icons)
                        data_zoom=None,  # Remove the zoom icon
                        brush=None,  # Remove brush icon
                    ),
                ),
            )
            .set_series_opts(
                label_opts=opts.LabelOpts(is_show=True),
            )
        )

        # Set the chart to fill the screen
        graph.width = "100%"
        graph.height = "100%"

        # Save the graph to the output path
        if output_path:
            graph.render(output_path)

        # Add the full-screen CSS after rendering
        with open(output_path, "r") as file:
            html_content = file.read()

        full_screen_css = """
        <style>
            body, html {
                height: 100%;
                margin: 0;
            }

            .chart-container {
                width: 100%;
                height: 100%;
                position: absolute;
                top: 0;
                left: 0;
            }

            canvas {
                width: 100% !important;
                height: 100% !important;
            }
        </style>
        """

        # Insert the CSS before closing the head tag
        html_content = html_content.replace("</head>", full_screen_css + "</head>")

        # Write the updated content back to the file
        with open(output_path, "w") as file:
            file.write(html_content)

        return graph