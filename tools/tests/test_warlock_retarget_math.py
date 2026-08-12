#!/usr/bin/env python3
"""Offline regression tests for the scale-100 Warlock retarget formula.

The engine implementation uses Stingray row matrices. These tests preserve the
two essential compiled-rest facts without requiring Blender or a game process:
target world calibration must be continuous at handoff, and converting back
through the target parent must normalize world motion into the parent's 100x
local space. A raw native-local hips copy must remain an explicit failing
counterexample.
"""

from __future__ import annotations

import math
import unittest


Matrix = list[list[float]]


def identity() -> Matrix:
    return [[1.0 if row == column else 0.0 for column in range(4)] for row in range(4)]


def multiply(left: Matrix, right: Matrix) -> Matrix:
    return [
        [sum(left[row][k] * right[k][column] for k in range(4)) for column in range(4)]
        for row in range(4)
    ]


def translation(x: float, y: float, z: float) -> Matrix:
    result = identity()
    result[3][0:3] = [x, y, z]
    return result


def uniform_scale(value: float) -> Matrix:
    result = identity()
    result[0][0] = result[1][1] = result[2][2] = value
    return result


def translation_of(matrix: Matrix) -> tuple[float, float, float]:
    return tuple(matrix[3][0:3])  # type: ignore[return-value]


def normalized_axis_volume(matrix: Matrix) -> float:
    x, y, z = (matrix[index][0:3] for index in range(3))

    def cross(a: list[float], b: list[float]) -> list[float]:
        return [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        ]

    def dot(a: list[float], b: list[float]) -> float:
        return sum(left * right for left, right in zip(a, b))

    lengths = [math.sqrt(dot(axis, axis)) for axis in (x, y, z)]
    if min(lengths) < 1e-6:
        return 0.0
    return abs(dot(x, cross(y, z))) / math.prod(lengths)


def assert_matrix_close(case: unittest.TestCase, actual: Matrix, expected: Matrix) -> None:
    for row in range(4):
        for column in range(4):
            case.assertAlmostEqual(actual[row][column], expected[row][column], places=9)


class WarlockRetargetMathTests(unittest.TestCase):
    # Values measured from the current compiled resources.
    custom_hips_local = (-0.001729736, 0.007580467, 0.000036322)
    native_hips_local = (-0.851529062, -0.176265016, 0.0)

    def setUp(self) -> None:
        self.target_parent_world = uniform_scale(100.0)
        self.target_parent_inverse = uniform_scale(0.01)
        self.target_local_at_handoff = translation(*self.custom_hips_local)
        self.target_world_at_handoff = multiply(
            self.target_local_at_handoff, self.target_parent_world
        )
        self.source_world_at_handoff = translation(*self.native_hips_local)

    def corrected_local(self, source_world: Matrix) -> Matrix:
        # For translation-only rigid matrices, inverse(S0) is translation(-S0).
        inverse_source = translation(*(-value for value in self.native_hips_local))
        source_delta = multiply(inverse_source, source_world)
        desired_world = multiply(self.target_world_at_handoff, source_delta)
        return multiply(desired_world, self.target_parent_inverse)

    def test_calibration_is_exactly_continuous(self) -> None:
        corrected = self.corrected_local(self.source_world_at_handoff)
        assert_matrix_close(self, corrected, self.target_local_at_handoff)

    def test_world_motion_is_normalized_by_scale_100_parent(self) -> None:
        source_after_world_motion = multiply(
            self.source_world_at_handoff, translation(0.05, 0.0, 0.0)
        )
        corrected = self.corrected_local(source_after_world_motion)
        x, y, z = translation_of(corrected)
        self.assertAlmostEqual(x, self.custom_hips_local[0] + 0.0005, places=9)
        self.assertAlmostEqual(y, self.custom_hips_local[1], places=9)
        self.assertAlmostEqual(z, self.custom_hips_local[2], places=9)

    def test_raw_native_local_copy_reproduces_v48_escape_class(self) -> None:
        valid_world = translation_of(self.target_world_at_handoff)
        raw_copy_world = translation_of(
            multiply(translation(*self.native_hips_local), self.target_parent_world)
        )
        displacement = math.dist(valid_world, raw_copy_world)
        self.assertGreater(displacement, 80.0)

    def test_collinear_nonzero_axes_are_rejected_before_inverse(self) -> None:
        matrix = identity()
        matrix[0][0:3] = [1.0, 0.0, 0.0]
        matrix[1][0:3] = [2.0, 0.0, 0.0]
        matrix[2][0:3] = [0.0, 0.0, 1.0]
        self.assertEqual(normalized_axis_volume(matrix), 0.0)

    def test_near_singular_axes_are_rejected_scale_independently(self) -> None:
        matrix = uniform_scale(100.0)
        matrix[1][0:3] = [100.0, 0.0000001, 0.0]
        self.assertLess(normalized_axis_volume(matrix), 0.00001)
        self.assertGreater(normalized_axis_volume(uniform_scale(100.0)), 0.99999)


if __name__ == "__main__":
    unittest.main(verbosity=2)
