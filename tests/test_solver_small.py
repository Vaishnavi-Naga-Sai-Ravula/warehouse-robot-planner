"""Tiny correctness checks; callback stops search after the first complete plan."""
import sys
import unittest
from pathlib import Path
from random import Random
from types import MappingProxyType

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE / "bench-warehouse"))

from data import Instance
import validator
from adapters.myteam import Planner


def fixture(starts, goals, width=3, height=2, blocked=()):
    return Instance(
        name="tiny-audit", seed=0, profile=MappingProxyType({}),
        width=width, height=height, blocked=tuple(blocked),
        passable=tuple(c not in blocked for c in range(width * height)),
        starts=tuple(starts), goals=tuple(goals), horizon=40,
        lb_makespan=1, lb_sum_of_costs=1,
        corridor_cells=tuple(c for c in range(width * height) if c not in blocked),
        congestion_scale=2,
    )


class SmallSolverAudit(unittest.TestCase):
    def run_fixture(self, inst):
        before = (inst.compute_digest(), inst.passable, inst.corridor_cells, inst.congestion_scale)
        offers = []
        planner = Planner()

        def submit(paths):
            cost, reason = validator.evaluate(inst, paths)
            offers.append((cost, reason, [list(p) for p in paths]))
            return {"accepted": cost is not None, "reason": reason, "cost": cost,
                    "best": cost, "elapsed_s": 0.0, "remaining_s": 0.01}

        result = planner.solve(inst, submit)
        self.assertTrue(offers, "solver produced no complete candidate")
        self.assertTrue(all(cost is not None for cost, _, _ in offers), offers)
        self.assertIsNotNone(result)
        cost, reason = validator.evaluate(inst, result)
        self.assertIsNone(reason)
        self.assertEqual(cost, planner._cost(result))
        for robot, path in enumerate(result):
            self.assertTrue(len(path) == 1 or path[-2] != inst.goals[robot],
                            "arrival-by-path-length assumes no final goal padding")
        self.assertEqual(before, (inst.compute_digest(), inst.passable,
                                  inst.corridor_cells, inst.congestion_scale))

    def test_two_robots_swap_goals_with_detour(self):
        self.run_fixture(fixture((0, 2), (2, 0)))

    def test_already_parked_goal_forces_other_robot_detour(self):
        self.run_fixture(fixture((1, 0), (1, 2)))

    def test_three_robot_rotation(self):
        self.run_fixture(fixture((0, 1, 2), (1, 2, 0)))

    def test_obstacle_detour(self):
        self.run_fixture(fixture((0, 2), (2, 0), width=3, height=3, blocked=(1,)))

    def test_eight_open_grid_assignments(self):
        rng = Random(99)
        for case in range(8):
            starts = rng.sample(range(25), 4)
            goals = rng.sample(range(25), 4)
            with self.subTest(case=case):
                self.run_fixture(fixture(starts, goals, width=5, height=5))


if __name__ == "__main__":
    unittest.main(verbosity=2)
