"""Read-only audit of the unmodified Warehouse validator and scoring curve."""
import sys
import unittest
from pathlib import Path
from types import MappingProxyType

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE / "bench-warehouse"))

from data import Instance
import validator
from benchkit.scoring import normalised, checkpoint_score, AxisScore


def instance(starts=(0, 2), goals=(2, 0), width=3, height=2,
             horizon=8, blocked=(), corridors=(1, 4)):
    return Instance(
        name="audit", seed=0, profile=MappingProxyType({}),
        width=width, height=height, blocked=tuple(blocked),
        passable=tuple(c not in blocked for c in range(width * height)),
        starts=tuple(starts), goals=tuple(goals), horizon=horizon,
        lb_makespan=2, lb_sum_of_costs=4,
        corridor_cells=tuple(corridors), congestion_scale=2,
    )


class ValidatorContract(unittest.TestCase):
    def test_collision_free_detour_cost(self):
        inst = instance()
        paths = [[0, 1, 2], [2, 5, 4, 3, 0]]
        self.assertEqual(validator.evaluate(inst, paths), (1725000, None))
        self.assertEqual(validator.evaluate(inst, {"paths": paths}), (1725000, None))

    def test_vertex_collision_rejected(self):
        cost, reason = validator.evaluate(instance(), [[0, 1, 2], [2, 1, 0]])
        self.assertIsNone(cost)
        self.assertIn("both occupy", reason)

    def test_edge_swap_rejected(self):
        inst = instance(starts=(0, 1), goals=(1, 0))
        cost, reason = validator.evaluate(inst, [[0, 1], [1, 0]])
        self.assertIsNone(cost)
        self.assertIn("swap", reason)

    def test_finished_goal_still_blocks_later_robot(self):
        inst = instance(goals=(1, 0))
        cost, reason = validator.evaluate(inst, [[0, 1], [2, 2, 1, 0]])
        self.assertIsNone(cost)
        self.assertIn("both occupy", reason)

    def test_arrival_is_final_goal_suffix(self):
        inst = instance(starts=(0,), goals=(1,), corridors=())
        measured = validator.measure(inst, [[0, 1, 2, 1, 1]])
        self.assertEqual(measured["arrival"], [3])
        self.assertEqual(measured["makespan"], 3)

    def test_row_wrap_is_not_cardinal_move(self):
        inst = instance(starts=(2,), goals=(3,))
        cost, reason = validator.evaluate(inst, [[2, 3]])
        self.assertIsNone(cost)
        self.assertIn("jumps", reason)

    def test_bool_cells_not_integers(self):
        inst = instance(starts=(0,), goals=(1,))
        cost, reason = validator.evaluate(inst, [[False, True]])
        self.assertIsNone(cost)
        self.assertIn("non-integer", reason)

    def test_blocked_cell_rejected(self):
        inst = instance(starts=(0,), goals=(2,), blocked=(1,))
        cost, reason = validator.evaluate(inst, [[0, 1, 2]])
        self.assertIsNone(cost)
        self.assertIn("blocked", reason)

    def test_length_limit_applies_even_to_goal_padding(self):
        inst = instance(starts=(0,), goals=(1,), horizon=2)
        cost, reason = validator.evaluate(inst, [[0, 1, 1, 1]])
        self.assertIsNone(cost)
        self.assertIn("horizon", reason)

    def test_congestion_counts_unique_robots_per_cell(self):
        inst = instance(starts=(0, 2), goals=(2, 0), corridors=(1,))
        paths = [[0, 1, 2], [2, 5, 4, 1, 0]]
        measured = validator.measure(inst, paths)
        self.assertEqual(measured["congestion"], 1)


class ScoringContract(unittest.TestCase):
    def test_reference_baseline_and_missing(self):
        self.assertEqual(normalised(100, 100, 80), 0.25)
        self.assertEqual(normalised(80, 100, 80), 1.0)
        self.assertEqual(normalised(None, 100, 80), 0.0)

    def test_missing_first_checkpoint_caps_instance_at_seventy_percent(self):
        self.assertAlmostEqual(checkpoint_score([None, 80, 80, 80], 100, 80), 0.7)

    def test_engineering_is_multiplier_not_extra_points(self):
        self.assertEqual(AxisScore(70, 30).total(0.25, 0.25, 1)["total"], 25)
        self.assertEqual(AxisScore(70, 30).total(1, 1, 0)["total"], 70)


if __name__ == "__main__":
    unittest.main(verbosity=2)

