from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

@dataclass
class PointData:
    x: np.ndarray # Units um
    y: np.ndarray # Units um
    step: np.ndarray # Unitless

    @classmethod
    def from_csv(cls, path: str | Path) -> PointData:
        """Load X, Y, and optional Step columns from a CSV."""
        df = pd.read_csv(path)

        x = df["X"].to_numpy(dtype=float)
        y = df["Y"].to_numpy(dtype=float)

        if "Step" in df.columns:
            step = df["Step"].to_numpy(dtype=int)
        else:
            step = np.linspace(
                0, 300_000, len(df), dtype=int
            )

        return cls(x=x, y=y, step=step)

    
    #=========================
    # BEGINNING PLOTTING STUFF
    #=========================

    @staticmethod
    def configure_camera_axes(ax: Axes) -> None:
        """Set plot limits to the full camera sensor area."""
        pixel_pitch = 3.5
        ax.set_xlim(0, 1920*pixel_pitch)
        ax.set_ylim(0, 1440*pixel_pitch)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("X (µm)")
        ax.set_ylabel("Y (µm)")

    def plot_scatter(
    self,
    ax: Axes | None = None,
    connect: bool = False,
    color_by_step: bool = True) -> Axes:
        """Plot X/Y beam centroid positions in micrometers."""

        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 6))
        else:
            fig = ax.figure

        x, y = self.x, self.y
        if connect:
            ax.plot(x, y, color="gray", alpha=0.4, linewidth=1)

        if color_by_step:
            scatter = ax.scatter(
                x, y,
                c=self.step,
                cmap="turbo",
                s=12,
            )
            fig.colorbar(scatter, ax=ax, label="Motor step")
        else:
            ax.scatter(x, y, s=12)

        ax.set_xlabel("X (µm)")
        ax.set_ylabel("Y (µm)")
        ax.set_title("Beam Centroid Path")
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True, alpha=0.3)

        # add arrows
        for i in range(0, len(x) - 1, 30):
            ax.annotate(
                "",
                xy=(x[i + 1], y[i + 1]),
                xytext=(x[i], y[i]),
                arrowprops=dict(
                    arrowstyle="->",
                    color="black",
                    lw=1.5,
                ),
            )

        
        # Mark start
        ax.scatter(
            x[0], y[0],
            color="lime",
            marker="o",
            s=120,
            edgecolors="black",
            zorder=5,
            label="Start",
        )

        self.configure_camera_axes(ax)

        return ax


    def plot_vs_step(self) -> tuple[Axes, Axes]:
        """Plot X and Y positions against motor step."""

        fig, (ax1, ax2) = plt.subplots(
            2, 1,
            figsize=(10, 6),
            sharex=True,
            constrained_layout=True,
        )

        ax1.plot(self.step, self.x, linewidth=1)
        ax1.set_ylabel("X (µm)")
        ax1.set_title("Beam Position vs Motor Step")
        ax1.grid(True, alpha=0.3)

        ax2.plot(self.step, self.y, linewidth=1)
        ax2.set_xlabel("Motor step")
        ax2.set_ylabel("Y (µm)")
        ax2.grid(True, alpha=0.3)

        return ax1, ax2


    def plot_window(self, window: PointData, ax: Axes | None = None) -> Axes:
        """Show a selected window highlighted on the full path."""

        if ax is None:
            _, ax = plt.subplots(figsize=(8, 6))

        # Full path
        ax.plot(self.x, self.y, color="gray", alpha=0.4)
        ax.scatter(
            self.x, self.y,
            color="gray",
            s=8,
            alpha=0.4,
            label="Full rotation",
        )

        # Highlight selected region
        ax.plot(
            window.x, window.y,
            color="red",
            linewidth=2,
        )
        ax.scatter(
            window.x, window.y,
            color="red",
            s=18,
            label="Selected window",
        )
        ax.grid(True, alpha=0.3)
        ax.legend()

        self.configure_camera_axes(ax)
        return ax


    #=====================
    # END PLOTTING STUFF
    #=====================



    def get_x_divergence(self, distance: float) -> float:
        
        return (np.ptp(self.x)/ distance) * 1e3

    def get_y_divergence(self, distance: float) -> float:
        return (np.ptp(self.y) / distance) * 1e3
    
    def get_total_divergence(self, distance: float) -> float:
        return 0.5 * (self.get_x_divergence(distance) + self.get_y_divergence(distance))

    def get_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame({'X': self.x, 'Y': self.y, 'Step': self.step})

    def get_point_count(self) -> int:
        return len(self.x)

    def get_mean_x(self) -> float:
        return np.mean(self.x)

    def get_mean_y(self) -> float:
        return np.mean(self.y)

    def get_optimum_window(
        self,
        window_divider: int = 4,
        distance: float = 5200,
        full_rotation: int = 300_000,
    ) -> tuple[PointData, pd.Series]:

        from pandas.api.indexers import FixedForwardWindowIndexer

        # Remove duplicate endpoint
        n = len(self.step)
        if n > 1 and self.step[-1] - self.step[0] == full_rotation:
            n -= 1

        if window_divider < 1 or n < window_divider:
            raise ValueError("Invalid window_divider")

        df = self.get_dataframe().iloc[:n].copy()

        window_size = n // window_divider

        # Wrap the beginning onto the end
        wrapped = pd.concat(
            [df, df.head(window_size - 1)],
            ignore_index=True
        )

        # Continue motor steps into the next rotation
        wrapped.loc[n:, "Step"] += full_rotation

        indexer = FixedForwardWindowIndexer(
            window_size=window_size
        )

        dx = wrapped["X"].rolling(indexer).apply(
            np.ptp, raw=True
        ) * 1000 / distance

        dy = wrapped["Y"].rolling(indexer).apply(
            np.ptp, raw=True
        ) * 1000 / distance

        divergence = (dx + dy) / 2

        # Only consider starting positions in the first rotation
        best_start = divergence.iloc[:n].idxmin()

        optimum = wrapped.iloc[
            best_start:best_start + window_size
        ]

        return (
            PointData(
                x=optimum["X"].to_numpy(),
                y=optimum["Y"].to_numpy(),
                step=optimum["Step"].to_numpy(dtype=int),
            ),
            divergence.iloc[:n].copy(),
        )




    





    
    

