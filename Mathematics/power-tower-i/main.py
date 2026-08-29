# | Visualization Test |
# Visualization testing only.
# Results are not mathematically validated and should not be treated as authoritative.

'''
Originally, it looked like this:

import numpy as np
import matplotlib.pyplot as plt

WIDTH = 1600
HEIGHT = 1600

MAX_ITER = 100
ESCAPE_RADIUS = 100.0
TOLERANCE = 1e-10

X_MIN = -2.0
X_MAX = 2.0
Y_MIN = -2.0
Y_MAX = 2.0

x = np.linspace(X_MIN, X_MAX, WIDTH)
y = np.linspace(Y_MIN, Y_MAX, HEIGHT)

X, Y = np.meshgrid(x, y)
Z = X + 1j * Y

w = Z.copy()

convergence = np.full(
    Z.shape,
    MAX_ITER,
    dtype=np.float64
)

escape = np.full(
    Z.shape,
    MAX_ITER,
    dtype=np.float64
)

active = np.ones(
    Z.shape,
    dtype=bool
)

with np.errstate(
    divide="ignore",
    invalid="ignore"
):
    log_z = np.log(Z)

for iteration in range(1, MAX_ITER + 1):

    old_w = w

    with np.errstate(
        over="ignore",
        invalid="ignore",
        divide="ignore"
    ):
        w = np.exp(old_w * log_z)

    finite = (
        np.isfinite(w.real) &
        np.isfinite(w.imag)
    )

    magnitude = np.abs(w)

    escaped = (
        finite &
        (magnitude > ESCAPE_RADIUS)
    )

    difference = np.abs(w - old_w)

    converged = (
        finite &
        (difference < TOLERANCE)
    )

    newly_converged = (
        active &
        converged
    )

    newly_escaped = (
        active &
        escaped
    )

    convergence[newly_converged] = iteration
    escape[newly_escaped] = iteration

    active &= ~(
        newly_converged |
        newly_escaped
    )

    if not active.any():
        break

    if iteration % 10 == 0:
        print(
            f"Iteration {iteration:3d} | "
            f"Active: {active.sum():,}"
        )

image = np.zeros(
    Z.shape,
    dtype=np.float64
)

conv_mask = convergence < MAX_ITER

image[conv_mask] = np.sqrt(
    convergence[conv_mask] / MAX_ITER
)

escape_mask = escape < MAX_ITER

image[escape_mask] = -np.sqrt(
    escape[escape_mask] / MAX_ITER
)

undecided = (
    (convergence == MAX_ITER) &
    (escape == MAX_ITER)
)

image[undecided] = 0

plt.figure(
    figsize=(12, 12),
    dpi=120
)

plt.imshow(
    image,
    extent=[
        X_MIN,
        X_MAX,
        Y_MIN,
        Y_MAX
    ],
    origin="lower",
    interpolation="nearest",
    cmap="turbo"
)

plt.axhline(
    0,
    linewidth=0.4,
    alpha=0.35
)

plt.axvline(
    0,
    linewidth=0.4,
    alpha=0.35
)

plt.scatter(
    [0],
    [1],
    s=50,
    facecolors="none",
    edgecolors="white",
    linewidths=1.2,
    label="i"
)

plt.scatter(
    [0.7834305107],
    [0],
    s=30,
    facecolors="none",
    edgecolors="white",
    linewidths=1.0
)

plt.xlabel(
    "Re(z)",
    fontsize=12
)

plt.ylabel(
    "Im(z)",
    fontsize=12
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "power_tower_fractal.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

Now:
'''

import numpy as np
import matplotlib.pyplot as plt
import json
import csv
import cmath
import math
import time
from dataclasses import dataclass


@dataclass
class TowerConfig:
    width: int = 1200
    height: int = 1200
    max_iter: int = 100
    tolerance: float = 1e-10
    escape_radius: float = 100.0
    x_min: float = -2.0
    x_max: float = 2.0
    y_min: float = -2.0
    y_max: float = 2.0


@dataclass
class TowerPoint:
    z: complex
    value: complex
    iterations: int
    state: str
    distance: float
    derivative: complex
    stable: bool


class PowerTower:

    def __init__(self, config=None):
        self.config = config or TowerConfig()
        self.Z = None
        self.log_Z = None
        self.W = None
        self.convergence = None
        self.escape = None
        self.distance = None
        self.derivative = None
        self.stability = None
        self.state = None
        self.iterations = None
        self.image = None
        self.elapsed = 0.0

    def validate(self):
        c = self.config

        if c.width < 1:
            raise ValueError("width must be positive")

        if c.height < 1:
            raise ValueError("height must be positive")

        if c.max_iter < 1:
            raise ValueError("max_iter must be positive")

        if c.tolerance <= 0:
            raise ValueError("tolerance must be positive")

        if c.escape_radius <= 0:
            raise ValueError("escape_radius must be positive")

        if c.x_min >= c.x_max:
            raise ValueError("invalid x range")

        if c.y_min >= c.y_max:
            raise ValueError("invalid y range")

    def create_grid(self):
        c = self.config

        x = np.linspace(
            c.x_min,
            c.x_max,
            c.width,
            dtype=np.float64
        )

        y = np.linspace(
            c.y_min,
            c.y_max,
            c.height,
            dtype=np.float64
        )

        X, Y = np.meshgrid(x, y)

        self.Z = X + 1j * Y

        with np.errstate(
            divide="ignore",
            invalid="ignore"
        ):
            self.log_Z = np.log(self.Z)

    def allocate(self):
        shape = self.Z.shape
        c = self.config

        self.W = self.Z.copy()

        self.convergence = np.zeros(
            shape,
            dtype=np.int16
        )

        self.escape = np.zeros(
            shape,
            dtype=np.int16
        )

        self.distance = np.full(
            shape,
            np.inf,
            dtype=np.float64
        )

        self.derivative = np.zeros(
            shape,
            dtype=np.complex128
        )

        self.stability = np.zeros(
            shape,
            dtype=np.float64
        )

        self.state = np.zeros(
            shape,
            dtype=np.int8
        )

        self.iterations = np.zeros(
            shape,
            dtype=np.int16
        )

    def iterate(self):
        c = self.config
        active = np.ones(
            self.Z.shape,
            dtype=bool
        )

        escape_sq = c.escape_radius ** 2
        tolerance_sq = c.tolerance ** 2

        for iteration in range(1, c.max_iter + 1):
            if not active.any():
                break

            idx = active

            old = self.W[idx]
            base = self.Z[idx]
            logs = self.log_Z[idx]

            with np.errstate(
                over="ignore",
                invalid="ignore",
                divide="ignore"
            ):
                new = np.exp(old * logs)

            finite = (
                np.isfinite(new.real) &
                np.isfinite(new.imag)
            )

            magnitude_sq = (
                new.real * new.real +
                new.imag * new.imag
            )

            escaped = (
                ~finite |
                (magnitude_sq > escape_sq)
            )

            valid = finite & ~escaped

            delta_sq = np.full(
                new.shape,
                np.inf,
                dtype=np.float64
            )

            if valid.any():
                dr = (
                    new.real[valid] -
                    old.real[valid]
                )

                di = (
                    new.imag[valid] -
                    old.imag[valid]
                )

                delta_sq[valid] = (
                    dr * dr +
                    di * di
                )

            converged = (
                valid &
                (delta_sq < tolerance_sq)
            )

            positions = np.flatnonzero(
                active
            )

            escaped_positions = positions[
                escaped
            ]

            converged_positions = positions[
                converged
            ]

            self.W[idx] = new

            self.iterations.flat[
                escaped_positions
            ] = iteration

            self.iterations.flat[
                converged_positions
            ] = iteration

            self.escape.flat[
                escaped_positions
            ] = iteration

            self.convergence.flat[
                converged_positions
            ] = iteration

            if escaped_positions.size:
                active.flat[
                    escaped_positions
                ] = False

            if converged_positions.size:
                active.flat[
                    converged_positions
                ] = False

            valid_positions = positions[
                valid
            ]

            if valid_positions.size:
                self.distance.flat[
                    valid_positions
                ] = np.sqrt(
                    delta_sq[valid]
                )

        self.state[
            self.convergence > 0
        ] = 1

        self.state[
            self.escape > 0
        ] = 2

    def compute_derivative(self):
        c = self.config

        derivative = np.zeros(
            self.Z.shape,
            dtype=np.complex128
        )

        active = np.ones(
            self.Z.shape,
            dtype=bool
        )

        w = self.Z.copy()

        with np.errstate(
            divide="ignore",
            invalid="ignore"
        ):
            log_z = np.log(self.Z)

        for _ in range(c.max_iter):
            if not active.any():
                break

            idx = active

            old_w = w[idx]
            old_d = derivative[idx]
            z = self.Z[idx]
            log_z_idx = log_z[idx]

            with np.errstate(
                over="ignore",
                invalid="ignore",
                divide="ignore"
            ):
                new_w = np.exp(
                    old_w * log_z_idx
                )

            derivative_term = (
                old_d * log_z_idx
                + old_w / z
            )

            with np.errstate(
                over="ignore",
                invalid="ignore",
                divide="ignore"
            ):
                new_d = (
                    new_w *
                    derivative_term
                )

            finite = (
                np.isfinite(new_w.real) &
                np.isfinite(new_w.imag) &
                np.isfinite(new_d.real) &
                np.isfinite(new_d.imag)
            )

            magnitude_sq = (
                new_w.real * new_w.real +
                new_w.imag * new_w.imag
            )

            escaped = (
                ~finite |
                (magnitude_sq >
                 c.escape_radius ** 2)
            )

            delta = np.abs(
                new_w - old_w
            )

            converged = (
                finite &
                ~escaped &
                (delta < c.tolerance)
            )

            positions = np.flatnonzero(
                active
            )

            escaped_positions = positions[
                escaped
            ]

            converged_positions = positions[
                converged
            ]

            valid_positions = positions[
                finite & ~escaped
            ]

            w[idx] = new_w

            derivative[idx] = new_d

            if valid_positions.size:
                derivative.flat[
                    valid_positions
                ] = new_d[
                    finite & ~escaped
                ]

            active.flat[
                escaped_positions
            ] = False

            active.flat[
                converged_positions
            ] = False

        self.derivative = derivative

        self.stability = np.abs(
            derivative
        )

    def run(self):
        self.validate()

        start = time.perf_counter()

        self.create_grid()
        self.allocate()
        self.iterate()

        self.compute_derivative()

        self.elapsed = (
            time.perf_counter() - start
        )

        self.image = self.build_image()

        return self.image

    def build_image(self):
        c = self.config

        image = np.zeros(
            (
                c.height,
                c.width,
                3
            ),
            dtype=np.float32
        )

        convergence = (
            self.convergence
        )

        escape = self.escape

        conv = convergence > 0
        esc = escape > 0
        undecided = ~(conv | esc)

        if conv.any():
            t = (
                convergence[conv]
                / c.max_iter
            )

            hue = (
                0.58 +
                0.20 * t
            )

            saturation = (
                0.85 -
                0.20 * t
            )

            value = (
                0.95 -
                0.75 * t
            )

            hsv = np.stack(
                [
                    hue,
                    saturation,
                    value
                ],
                axis=-1
            )

            image[conv] = self.hsv_rgb(
                hsv
            )

        if esc.any():
            t = (
                escape[esc]
                / c.max_iter
            )

            hue = (
                0.02 +
                0.15 * t
            )

            saturation = (
                0.95 -
                0.15 * t
            )

            value = (
                0.95 -
                0.75 * t
            )

            hsv = np.stack(
                [
                    hue,
                    saturation,
                    value
                ],
                axis=-1
            )

            image[esc] = self.hsv_rgb(
                hsv
            )

        if undecided.any():
            d = self.distance[
                undecided
            ]

            finite = np.isfinite(d)

            if finite.any():
                v = np.zeros_like(
                    d,
                    dtype=np.float32
                )

                v[finite] = (
                    1.0 /
                    (
                        1.0 +
                        25.0 * d[finite]
                    )
                )

                image[undecided] = np.stack(
                    [
                        v * 0.10,
                        v * 0.14,
                        v * 0.25
                    ],
                    axis=-1
                )

        return image

    @staticmethod
    def hsv_rgb(hsv):
        h = hsv[:, 0]
        s = hsv[:, 1]
        v = hsv[:, 2]

        h6 = h * 6.0

        i = np.floor(h6).astype(
            np.int32
        )

        f = h6 - i

        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (
            1.0 -
            s * (1.0 - f)
        )

        i %= 6

        result = np.empty(
            (h.size, 3),
            dtype=np.float32
        )

        m0 = i == 0
        m1 = i == 1
        m2 = i == 2
        m3 = i == 3
        m4 = i == 4
        m5 = i == 5

        result[m0] = np.stack(
            [v[m0], t[m0], p[m0]],
            axis=1
        )

        result[m1] = np.stack(
            [q[m1], v[m1], p[m1]],
            axis=1
        )

        result[m2] = np.stack(
            [p[m2], v[m2], t[m2]],
            axis=1
        )

        result[m3] = np.stack(
            [p[m3], q[m3], v[m3]],
            axis=1
        )

        result[m4] = np.stack(
            [t[m4], p[m4], v[m4]],
            axis=1
        )

        result[m5] = np.stack(
            [v[m5], p[m5], q[m5]],
            axis=1
        )

        return result

    def point(self, z):
        if not isinstance(z, complex):
            z = complex(z)

        w = z
        derivative = 0j

        for iteration in range(
            1,
            self.config.max_iter + 1
        ):
            old = w

            try:
                with np.errstate(
                    over="ignore",
                    invalid="ignore"
                ):
                    w = z ** old

            except (
                OverflowError,
                ZeroDivisionError,
                ValueError
            ):
                return TowerPoint(
                    z,
                    w,
                    iteration,
                    "escaped",
                    math.inf,
                    derivative,
                    False
                )

            if not (
                math.isfinite(w.real)
                and
                math.isfinite(w.imag)
            ):
                return TowerPoint(
                    z,
                    w,
                    iteration,
                    "escaped",
                    math.inf,
                    derivative,
                    False
                )

            magnitude = abs(w)

            if (
                magnitude >
                self.config.escape_radius
            ):
                return TowerPoint(
                    z,
                    w,
                    iteration,
                    "escaped",
                    magnitude,
                    derivative,
                    False
                )

            delta = abs(
                w - old
            )

            if (
                delta <
                self.config.tolerance
            ):
                stable = (
                    abs(derivative) < 1.0
                )

                return TowerPoint(
                    z,
                    w,
                    iteration,
                    "converged",
                    delta,
                    derivative,
                    stable
                )

        return TowerPoint(
            z,
            w,
            self.config.max_iter,
            "bounded",
            abs(w),
            derivative,
            False
        )

    def orbit(self, z, count=50):
        z = complex(z)

        values = [z]
        w = z

        for _ in range(count):
            try:
                w = z ** w
            except (
                OverflowError,
                ZeroDivisionError,
                ValueError
            ):
                break

            if not (
                math.isfinite(w.real)
                and
                math.isfinite(w.imag)
            ):
                break

            values.append(w)

            if (
                abs(w) >
                self.config.escape_radius
            ):
                break

        return values

    def fixed_point(self, z, initial=None):
        z = complex(z)

        if initial is None:
            initial = z

        w = complex(initial)

        for iteration in range(
            1,
            self.config.max_iter + 1
        ):
            old = w

            try:
                w = z ** w
            except (
                OverflowError,
                ZeroDivisionError,
                ValueError
            ):
                return None

            if not (
                math.isfinite(w.real)
                and
                math.isfinite(w.imag)
            ):
                return None

            if (
                abs(w - old)
                <
                self.config.tolerance
            ):
                return {
                    "point": w,
                    "iterations": iteration,
                    "residual": abs(
                        w - z ** w
                    )
                }

        return None

    def fixed_point_from_w(self, w):
        w = complex(w)

        if w == 0:
            return None

        try:
            return np.exp(
                np.log(w) / w
            )
        except (
            OverflowError,
            ZeroDivisionError,
            ValueError
        ):
            return None

    def stability_multiplier(
        self,
        z,
        fixed_point
    ):
        z = complex(z)
        w = complex(fixed_point)

        if z == 0:
            return math.inf

        try:
            multiplier = (
                w *
                np.log(z)
            )
        except (
            OverflowError,
            ValueError
        ):
            return math.inf

        return abs(
            multiplier
        )

    def classify_point(self, z):
        result = self.point(z)

        if result.state == "converged":

            multiplier = (
                self.stability_multiplier(
                    z,
                    result.value
                )
            )

            if multiplier < 1:
                stability = "stable"
            elif multiplier == 1:
                stability = "neutral"
            else:
                stability = "unstable"

        else:
            multiplier = math.inf
            stability = "unknown"

        return {
            "z": result.z,
            "value": result.value,
            "iterations": result.iterations,
            "state": result.state,
            "distance": result.distance,
            "multiplier": multiplier,
            "stability": stability
        }

    def statistics(self):
        total = self.Z.size

        converged = np.count_nonzero(
            self.convergence
        )

        escaped = np.count_nonzero(
            self.escape
        )

        bounded = total - (
            converged + escaped
        )

        return {
            "pixels": int(total),
            "converged": int(converged),
            "escaped": int(escaped),
            "bounded": int(bounded),
            "convergence_ratio":
                float(converged / total),
            "escape_ratio":
                float(escaped / total),
            "bounded_ratio":
                float(bounded / total),
            "elapsed":
                float(self.elapsed),
            "width":
                self.config.width,
            "height":
                self.config.height,
            "max_iter":
                self.config.max_iter,
            "tolerance":
                self.config.tolerance,
            "escape_radius":
                self.config.escape_radius
        }

    def save_image(self, filename):
        if self.image is None:
            raise RuntimeError(
                "run() first"
            )

        plt.imsave(
            filename,
            self.image
        )

    def save_statistics(self, filename):
        data = self.statistics()

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                data,
                f,
                indent=2
            )

    def save_point(
        self,
        filename,
        z
    ):
        data = self.classify_point(
            complex(z)
        )

        clean = {
            "z_real":
                data["z"].real,
            "z_imag":
                data["z"].imag,
            "value_real":
                data["value"].real,
            "value_imag":
                data["value"].imag,
            "iterations":
                data["iterations"],
            "state":
                data["state"],
            "distance":
                data["distance"],
            "multiplier":
                data["multiplier"],
            "stability":
                data["stability"]
        }

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                clean,
                f,
                indent=2
            )

    def plot(self):
        if self.image is None:
            raise RuntimeError(
                "run() first"
            )

        c = self.config

        fig, ax = plt.subplots(
            figsize=(11, 11),
            dpi=120
        )

        ax.imshow(
            self.image,
            extent=[
                c.x_min,
                c.x_max,
                c.y_min,
                c.y_max
            ],
            origin="lower",
            interpolation="nearest",
            aspect="equal"
        )

        ax.axhline(
            0,
            linewidth=0.35,
            alpha=0.3
        )

        ax.axvline(
            0,
            linewidth=0.35,
            alpha=0.3
        )

        if (
            c.x_min <= 0 <= c.x_max
            and
            c.y_min <= 1 <= c.y_max
        ):
            ax.scatter(
                [0],
                [1],
                s=55,
                facecolors="none",
                edgecolors="white",
                linewidths=1.2
            )

            ax.text(
                0,
                1,
                " i",
                color="white",
                fontsize=11
            )

        ax.set_xlabel(
            "Re(z)"
        )

        ax.set_ylabel(
            "Im(z)"
        )

        plt.tight_layout()

        return fig, ax

    def plot_orbit(
        self,
        z,
        count=50
    ):
        values = self.orbit(
            z,
            count
        )

        if not values:
            return

        real = [
            v.real
            for v in values
        ]

        imag = [
            v.imag
            for v in values
        ]

        fig, ax = plt.subplots(
            figsize=(8, 8)
        )

        ax.plot(
            real,
            imag,
            linewidth=1
        )

        ax.scatter(
            real,
            imag,
            s=15
        )

        ax.scatter(
            [real[0]],
            [imag[0]],
            s=70,
            facecolors="none",
            edgecolors="black"
        )

        ax.set_xlabel(
            "Re(w)"
        )

        ax.set_ylabel(
            "Im(w)"
        )

        ax.set_title(
            f"Power Tower Orbit: z={z}"
        )

        ax.grid(
            alpha=0.25
        )

        ax.set_aspect(
            "equal",
            adjustable="box"
        )

        plt.tight_layout()

        return fig, ax

    def print_statistics(self):
        data = self.statistics()

        print()
        print(
            "Power Tower Statistics"
        )
        print(
            "----------------------"
        )

        for key, value in data.items():
            print(
                f"{key}: {value}"
            )

    def inspect(self, z):
        result = self.classify_point(
            complex(z)
        )

        print()
        print(
            f"z = {result['z']}"
        )

        print(
            f"state = {result['state']}"
        )

        print(
            f"value = {result['value']}"
        )

        print(
            f"iterations = "
            f"{result['iterations']}"
        )

        print(
            f"distance = "
            f"{result['distance']}"
        )

        print(
            f"multiplier = "
            f"{result['multiplier']}"
        )

        print(
            f"stability = "
            f"{result['stability']}"
        )

        return result


def main():
    config = TowerConfig(
        width=1200,
        height=1200,
        max_iter=100,
        tolerance=1e-10,
        escape_radius=100.0,
        x_min=-2.0,
        x_max=2.0,
        y_min=-2.0,
        y_max=2.0
    )

    fractal = PowerTower(
        config
    )

    fractal.run()

    fractal.print_statistics()

    fractal.inspect(
        1j
    )

    fractal.save_image(
        "power_tower_fractal.png"
    )

    fractal.save_statistics(
        "power_tower_statistics.json"
    )

    fractal.plot()

    plt.show()


if __name__ == "__main__":
    main()
