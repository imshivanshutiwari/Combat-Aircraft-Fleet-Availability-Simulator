"""Gauge charts and Plotly dark template."""

import plotly.graph_objects as go


def get_dark_template():
    """
    Return a Plotly layout dict for dark military theme.

    Apply to every figure: fig.update_layout(**get_dark_template())
    """
    return {
        'paper_bgcolor': '#0A0F1A',
        'plot_bgcolor': '#0D1520',
        'font': {'color': '#E0E8FF', 'family': 'Courier New, monospace'},
        'title_font': {'color': '#E0E8FF', 'size': 16},
        'xaxis': {
            'gridcolor': '#1A2A40',
            'linecolor': '#1A3A5C',
            'tickcolor': '#7A9CC0',
            'tickfont': {'color': '#7A9CC0'},
        },
        'yaxis': {
            'gridcolor': '#1A2A40',
            'linecolor': '#1A3A5C',
            'tickcolor': '#7A9CC0',
            'tickfont': {'color': '#7A9CC0'},
        },
        'legend': {
            'bgcolor': 'rgba(13, 27, 42, 0.8)',
            'bordercolor': '#1A3A5C',
            'font': {'color': '#E0E8FF'},
        },
        'margin': {'l': 60, 'r': 20, 't': 50, 'b': 50},
    }


def create_gauge_chart(value, title, min_val=0, max_val=100,
                       green=75, amber=60):
    """
    Create a Plotly gauge chart.

    Parameters
    ----------
    value : float
        Current value to display.
    title : str
        Gauge title.
    min_val, max_val : float
        Range.
    green, amber : float
        Color thresholds.

    Returns
    -------
    go.Figure
        Plotly gauge figure.
    """
    color = '#00FF88' if value >= green else ('#FFB800' if value >= amber else '#FF3B3B')

    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=value,
        title={'text': title, 'font': {'color': '#7A9CC0', 'size': 14}},
        number={'font': {'color': color, 'size': 28, 'family': 'Courier New'},
                'suffix': '%'},
        gauge={
            'axis': {'range': [min_val, max_val], 'tickcolor': '#7A9CC0',
                     'tickfont': {'color': '#7A9CC0'}},
            'bar': {'color': color},
            'bgcolor': '#0D1520',
            'bordercolor': '#1A3A5C',
            'steps': [
                {'range': [min_val, amber], 'color': 'rgba(255,59,59,0.15)'},
                {'range': [amber, green], 'color': 'rgba(255,184,0,0.15)'},
                {'range': [green, max_val], 'color': 'rgba(0,255,136,0.15)'},
            ],
            'threshold': {
                'line': {'color': '#FFB800', 'width': 3},
                'thickness': 0.8,
                'value': 75,
            },
        },
    ))

    fig.update_layout(
        paper_bgcolor='#0A0F1A',
        font={'color': '#E0E8FF', 'family': 'Courier New'},
        height=200,
        margin={'l': 20, 'r': 20, 't': 40, 'b': 10},
    )

    return fig
