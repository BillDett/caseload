"""Chart visualization implementations."""

import json
from typing import Any

import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

from analytics.visualizations.base import Visualization


class BarChart(Visualization):
    """Bar chart visualization."""

    @property
    def viz_type(self) -> str:
        return "bar"

    def render_json(self, data: Any, **options) -> str:
        """Render bar chart to Plotly JSON.

        Args:
            data: Dict with 'x' and 'y' keys, or DataFrame.
            **options: title, x_label, y_label, orientation ('v' or 'h').
        """
        if hasattr(data, "to_dict"):
            # DataFrame
            x_col = options.get("x_col", data.columns[0])
            y_col = options.get("y_col", data.columns[1])
            fig = px.bar(
                data,
                x=x_col,
                y=y_col,
                title=options.get("title", ""),
                orientation=options.get("orientation", "v"),
            )
        else:
            # Dict
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=data.get("x", []),
                        y=data.get("y", []),
                        orientation=options.get("orientation", "v"),
                    )
                ]
            )
            fig.update_layout(title=options.get("title", ""))

        fig.update_layout(
            xaxis_title=options.get("x_label", ""),
            yaxis_title=options.get("y_label", ""),
        )

        return json.dumps(fig, cls=PlotlyJSONEncoder)

    def render_html(self, data: Any, **options) -> str:
        """Render bar chart to HTML."""
        chart_json = self.render_json(data, **options)
        div_id = options.get("div_id", "chart")
        return f"""
        <div id="{div_id}"></div>
        <script>
            Plotly.newPlot('{div_id}', {chart_json}.data, {chart_json}.layout);
        </script>
        """


class LineChart(Visualization):
    """Line chart visualization."""

    @property
    def viz_type(self) -> str:
        return "line"

    def render_json(self, data: Any, **options) -> str:
        """Render line chart to Plotly JSON.

        Args:
            data: Dict with 'x' and 'y' keys (or list of y series), or DataFrame.
            **options: title, x_label, y_label, line_dashes (list of dash styles per series).
        """
        if hasattr(data, "to_dict"):
            x_col = options.get("x_col", data.columns[0])
            y_cols = options.get("y_cols", [data.columns[1]])
            fig = px.line(data, x=x_col, y=y_cols, title=options.get("title", ""))
        else:
            fig = go.Figure()
            x = data.get("x", [])
            y_series = data.get("y", [])
            line_dashes = options.get("line_dashes", [])
            if y_series and isinstance(y_series[0], (list, tuple)):
                for i, y in enumerate(y_series):
                    name = data.get("names", [f"Series {i+1}"])[i]
                    dash = line_dashes[i] if i < len(line_dashes) else "solid"
                    fig.add_trace(go.Scatter(
                        x=x, y=y, mode="lines", name=name,
                        line=dict(dash=dash)
                    ))
            else:
                fig.add_trace(go.Scatter(x=x, y=y_series, mode="lines"))
            fig.update_layout(title=options.get("title", ""))

        fig.update_layout(
            xaxis_title=options.get("x_label", ""),
            yaxis_title=options.get("y_label", ""),
        )

        return json.dumps(fig, cls=PlotlyJSONEncoder)

    def render_html(self, data: Any, **options) -> str:
        """Render line chart to HTML."""
        chart_json = self.render_json(data, **options)
        div_id = options.get("div_id", "chart")
        return f"""
        <div id="{div_id}"></div>
        <script>
            Plotly.newPlot('{div_id}', {chart_json}.data, {chart_json}.layout);
        </script>
        """


class PieChart(Visualization):
    """Pie chart visualization."""

    @property
    def viz_type(self) -> str:
        return "pie"

    def render_json(self, data: Any, **options) -> str:
        """Render pie chart to Plotly JSON.

        Args:
            data: Dict with 'labels' and 'values' keys.
            **options: title.
        """
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=data.get("labels", []),
                    values=data.get("values", []),
                )
            ]
        )
        fig.update_layout(title=options.get("title", ""))
        return json.dumps(fig, cls=PlotlyJSONEncoder)

    def render_html(self, data: Any, **options) -> str:
        """Render pie chart to HTML."""
        chart_json = self.render_json(data, **options)
        div_id = options.get("div_id", "chart")
        return f"""
        <div id="{div_id}"></div>
        <script>
            Plotly.newPlot('{div_id}', {chart_json}.data, {chart_json}.layout);
        </script>
        """


class SankeyDiagram(Visualization):
    """Sankey diagram visualization for flow relationships."""

    @property
    def viz_type(self) -> str:
        return "sankey"

    def render_json(self, data: Any, **options) -> str:
        """Render Sankey diagram to Plotly JSON.

        Args:
            data: Dict with 'labels', 'sources', 'targets', 'values', and optionally 'colors'.
            **options: title, height.
        """
        labels = data.get("labels", [])
        sources = data.get("sources", [])
        targets = data.get("targets", [])
        values = data.get("values", [])
        colors = data.get("colors", [])

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color=colors if colors else None,
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color="rgba(150, 150, 150, 0.4)",
            )
        )])

        fig.update_layout(
            title=dict(
                text=options.get("title", ""),
                font=dict(size=16),
            ),
            font=dict(size=12),
            height=options.get("height", 500),
        )

        return json.dumps(fig, cls=PlotlyJSONEncoder)

    def render_html(self, data: Any, **options) -> str:
        """Render Sankey diagram to HTML."""
        chart_json = self.render_json(data, **options)
        div_id = options.get("div_id", "chart")
        return f"""
        <div id="{div_id}"></div>
        <script>
            Plotly.newPlot('{div_id}', {chart_json}.data, {chart_json}.layout);
        </script>
        """


class NetworkGraph(Visualization):
    """Network graph visualization for dependencies."""

    @property
    def viz_type(self) -> str:
        return "network"

    def render_json(self, data: Any, **options) -> str:
        """Render network graph to Plotly JSON.

        Args:
            data: Dict with 'nodes' (list of {id, label}) and
                  'edges' (list of {source, target}).
            **options: title.
        """
        import networkx as nx

        G = nx.DiGraph()

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        for node in nodes:
            G.add_node(node["id"], label=node.get("label", node["id"]))

        for edge in edges:
            G.add_edge(edge["source"], edge["target"])

        pos = nx.spring_layout(G)

        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=1, color="#888"),
            hoverinfo="none",
            mode="lines",
        )

        node_x = []
        node_y = []
        node_text = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(G.nodes[node].get("label", node))

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            hoverinfo="text",
            text=node_text,
            textposition="top center",
            marker=dict(
                size=20,
                color="#1f77b4",
                line=dict(width=2, color="#fff"),
            ),
        )

        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=options.get("title", ""),
                showlegend=False,
                hovermode="closest",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            ),
        )

        return json.dumps(fig, cls=PlotlyJSONEncoder)

    def render_html(self, data: Any, **options) -> str:
        """Render network graph to HTML."""
        chart_json = self.render_json(data, **options)
        div_id = options.get("div_id", "chart")
        return f"""
        <div id="{div_id}"></div>
        <script>
            Plotly.newPlot('{div_id}', {chart_json}.data, {chart_json}.layout);
        </script>
        """
