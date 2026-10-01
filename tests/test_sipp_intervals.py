"""Focused SIPP timing, edge, parking, and cache tests against official A*."""
import sys
import unittest
from pathlib import Path
from time import perf_counter

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE / "bench-warehouse"))

from test_solver_small import fixture
from adapters.myteam import Planner
from adapter import Reservation, space_time_astar
import validator


def prepared(inst):
    p = Planner()
    p.instance, p.n, p.v = inst, inst.n_robots, len(inst.passable)
    p.deadline = perf_counter() + 1
    p.corridor = set(inst.corridor_cells)
    p.neighbours = [inst.neighbours(c) if inst.passable[c] else [] for c in range(p.v)]
    p.heuristics = [p._distances(goal) for goal in inst.goals]
    return p


class SafeIntervalAudit(unittest.TestCase):
    def compare(self, inst, fixed):
        p = prepared(inst)
        reservations = p._reserve([None, fixed])
        path = p._path(0, reservations, inst.horizon)
        original = Reservation(inst.horizon)
        original.block_path(1, fixed)
        astar = space_time_astar(inst, inst.starts[0], inst.goals[0], original,
                                 p.heuristics[0], inst.horizon)
        self.assertEqual(path is None, astar is None)
        if path is not None:
            self.assertEqual(len(path), len(astar))
            cost, reason = validator.evaluate(inst, [path, fixed])
            self.assertIsNone(reason)
        return p, path

    def test_wait_reconstruction(self):
        inst = fixture((0, 2), (1, 4), width=3, height=3)
        _, path = self.compare(inst, [2, 1, 4])
        self.assertEqual(path, [0, 0, 1])

    def test_future_goal_visit_prevents_early_settling(self):
        inst = fixture((0, 8), (1, 7), width=3, height=3)
        _, path = self.compare(inst, [8, 5, 2, 2, 2, 1, 4, 7])
        self.assertEqual(len(path) - 1, 6)
        self.assertEqual(path[-1], 1)

    def test_reverse_edge_forces_detour(self):
        inst = fixture((0, 1), (1, 3), width=3, height=2)
        _, path = self.compare(inst, [1, 0, 3])
        self.assertEqual(len(path) - 1, 3)
        self.assertNotEqual(path[1], 1)

    def test_wait_cannot_cross_source_occupied_interval(self):
        inst = fixture((0, 2), (2, 0), width=3, height=1)
        _, path = self.compare(inst, [2, 1, 0])
        self.assertIsNone(path)

    def test_cache_is_invalidated_when_new_path_blocks_cell(self):
        inst = fixture((0, 2), (1, 4), width=3, height=3)
        p = prepared(inst)
        reservations = p._reserve([None, None])
        self.assertEqual(p._safe_intervals(1, reservations), [(0, inst.horizon)])
        p._block([2, 1, 4], *reservations)
        self.assertEqual(p._safe_intervals(1, reservations), [(0, 0), (2, inst.horizon)])

    def test_all_small_one_step_fixed_routes_match_astar(self):
        width, height = 3, 3
        for fixed_start in range(9):
            for fixed_goal in range(9):
                if abs(fixed_start % width - fixed_goal % width) + abs(fixed_start // width - fixed_goal // width) != 1:
                    continue
                for start in range(9):
                    if start == fixed_start:
                        continue
                    for goal in range(9):
                        if goal == fixed_goal:
                            continue
                        inst = fixture((start, fixed_start), (goal, fixed_goal), width=width, height=height)
                        self.compare(inst, [fixed_start, fixed_goal])


if __name__ == "__main__":
    unittest.main(verbosity=2)
