import os
from typing import TypedDict

import matplotlib.pyplot as plt

# Monkey-patch matplotlib style before importing pypfopt to fix seaborn style issue
original_style_use = plt.style.use


def patched_style_use(style: str | list[str]) -> None:
    """Patch matplotlib style.use to handle old seaborn style names"""
    if style == "seaborn-deep":
        style = "seaborn-v0_8-deep"
    elif isinstance(style, str) and style.startswith("seaborn-") and not style.startswith(
        "seaborn-v0_8"
    ):
        # Convert old seaborn style names to new format
        style = style.replace("seaborn-", "seaborn-v0_8-")
    return original_style_use(style)


plt.style.use = patched_style_use

# Import pypfopt after patching matplotlib to avoid seaborn style issues
from pypfopt.cla import CLA  # noqa: E402
from pypfopt.efficient_frontier import EfficientFrontier  # noqa: E402
from pypfopt.plotting import plot_efficient_frontier, plot_weights  # noqa: E402


class PlotKwargs(TypedDict, total=False):
    show_assets: bool
    risk_free_rate: float
    show_tangency: bool


def plot_portfolio(
    opt: EfficientFrontier | CLA, plot_type: str, save_path: str | None = None, show: bool = False, **kwargs: PlotKwargs
) -> plt.Figure:
    """
    Plot portfolio data using matplotlib.

    :param opt: Optimizer object (EfficientFrontier, CLA, etc.)
    :param plot_type: Type of plot ('efficient_frontier' or 'weights')
    :param save_path: Path to save the plot (if None, plot is not saved)
    :param show: Whether to display the plot
    :param **kwargs: Additional arguments passed to the plotting function
    :return: matplotlib figure object
    """
    if plot_type == "efficient_frontier":
        ax = plot_efficient_frontier(opt, **kwargs)
    elif plot_type == "weights":
        ax = plot_weights(opt.weights, **kwargs)
    else:
        raise ValueError("plot_type must be 'efficient_frontier' or 'weights'")

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
    if show:
        plt.show()
    return ax.get_figure()
