"""Warehouse MAPF: safe-interval planning and collision-safe neighbourhood repair.

This one-file adapter uses only public instance fields and ordinary path search.
It never reads benchmark files, seeds, profiles, witnesses or scoring anchors.
"""
from collections import deque
from heapq import heappop, heappush
from random import Random
from time import perf_counter


class Planner:
    def solve(self, instance, submit_candidate):
        self.instance = instance
        self.submit = submit_candidate
        self.n = instance.n_robots
        self.v = len(instance.passable)
        self.started = perf_counter()
        self.deadline = self.started + round(4.0 + self.n / 12.0, 2) - 0.25
        self.rng = Random(43127)
        self.corridor = set(instance.corridor_cells)
        self.neighbours = [instance.neighbours(c) if instance.passable[c] else []
                           for c in range(self.v)]
        self.heuristics = [self._distances(goal) for goal in instance.goals]
        self.distance = [self.heuristics[r][instance.starts[r]] for r in range(self.n)]
        self.best = None
        self.best_cost = None
        longest = sorted(range(self.n), key=lambda r: -self.distance[r])
        tight = sorted(range(self.n), key=lambda r: (len(self.neighbours[instance.goals[r]]), -self.distance[r]))
        visit_count = [0] * self.v
        goal_owner = {goal: r for r, goal in enumerate(instance.goals)}
        before = []
        for robot in range(self.n):
            cell = instance.starts[robot]
            route = [cell]
            visit_count[cell] += 1
            while cell != instance.goals[robot]:
                cell = next(c for c in self.neighbours[cell]
                            if self.heuristics[robot][c] == self.heuristics[robot][cell] - 1)
                route.append(cell)
                visit_count[cell] += 1
            before.append(set(goal_owner[c] for c in route if c in goal_owner) - {robot})
        blocking = [visit_count[goal] for goal in instance.goals]
        parking = sorted(range(self.n), key=lambda r: (blocking[r], -self.distance[r]))
        dependencies = []
        for _ in range(3):
            incoming = [0] * self.n
            for successors in before:
                for robot in successors:
                    incoming[robot] += 1
            remaining = set(range(self.n))
            order = []
            while remaining:
                robot = min(remaining, key=lambda r: (incoming[r], -self.distance[r] + self.rng.random()))
                remaining.remove(robot)
                order.append(robot)
                for successor in before[robot]:
                    incoming[successor] -= 1
            dependencies.append(order)
        self.dependency_orders = dependencies
        self.seed_orders = [dependencies[0], longest, dependencies[1], dependencies[2],
                            tight, list(reversed(longest)), parking]
        orders = self.seed_orders
        lower = instance.lb_makespan
        limits = list(dict.fromkeys(min(instance.horizon, bound)
                      for bound in (lower + 4, lower + max(8, lower // 4),
                                    lower * 2 + 8, instance.horizon)))
        for bound in limits:
            for initial_order in orders:
                if self.best is not None or perf_counter() >= self.deadline:
                    break
                order = list(initial_order)
                for _ in range(4):
                    plan, failed = self._construct(order, limit_override=bound,
                                                   expansion_cap=8000)
                    if plan is not None:
                        self._offer(plan)
                        break
                    if failed is None or perf_counter() >= self.deadline:
                        break
                    order.remove(failed)
                    order.insert(0, failed)
            if self.best is not None:
                break
        attempt = 0
        while self.best is None and perf_counter() < self.deadline:
            order = list(orders[attempt % len(orders)])
            for _ in range(max(1, self.n // 8)):
                a, b = self.rng.randrange(self.n), self.rng.randrange(self.n)
                order[a], order[b] = order[b], order[a]
            for _ in range(4):
                plan, failed = self._construct(order, expansion_cap=32000)
                if plan is not None:
                    self._offer(plan)
                    break
                if failed is None:
                    break
                order.remove(failed)
                order.insert(0, failed)
            attempt += 1
        if self.best is None:
            return None
        # Early output is preserved while alternative parking orders are tried.
        # Fixed-work parking-order repairs are especially useful for a large
        # observed makespan gap. Work caps prevent one failed order dominating.
        for attempt in range(32):
            if (max(len(path) - 1 for path in self.best) <= lower + 1
                    or perf_counter() >= self.deadline):
                break
            order = list(dependencies[attempt % len(dependencies)])
            if attempt >= len(dependencies):
                for _ in range(max(1, self.n // 8)):
                    a, b = self.rng.randrange(self.n), self.rng.randrange(self.n)
                    order[a], order[b] = order[b], order[a]
            for _ in range(4):
                plan, failed = self._construct(order, expansion_cap=5000)
                if plan is not None:
                    self._offer(plan)
                    break
                if failed is None:
                    break
                order.remove(failed)
                order.insert(0, failed)
        self._improve()
        return self.best

    def _distances(self, source):
        distance = [-1] * self.v
        distance[source] = 0
        queue = deque([source])
        while queue:
            cell = queue.popleft()
            next_distance = distance[cell] + 1
            for following in self.neighbours[cell]:
                if distance[following] < 0:
                    distance[following] = next_distance
                    queue.append(following)
        return distance

    def _reserve(self, paths, excluded=()):
        occupied, edges, parked, last_use = {}, set(), {}, {}
        traffic = [0] * self.v
        intervals = {}
        excluded = set(excluded)
        for robot, path in enumerate(paths):
            if robot not in excluded and path is not None:
                self._block(path, occupied, edges, parked, last_use, traffic, intervals)
        return occupied, edges, parked, last_use, traffic, intervals

    def _block(self, path, occupied, edges, parked, last_use, traffic, intervals):
        previous = path[0]
        for t, cell in enumerate(path):
            occupied.setdefault(cell, set()).add(t)
            last_use[cell] = max(t, last_use.get(cell, -1))
            intervals.pop(cell, None)
            if t:
                edges.add((t * self.v + previous) * self.v + cell)
            previous = cell
        parked[path[-1]] = len(path) - 1
        for cell in set(path) & self.corridor:
            traffic[cell] += 1

    def _safe_intervals(self, cell, reservations):
        occupied, edges, parked, last_use, traffic, cache = reservations
        if cell in cache:
            return cache[cell]
        end = min(self.instance.horizon, parked.get(cell, self.instance.horizon + 1) - 1)
        intervals = []
        begin = 0
        for t in sorted(occupied.get(cell, ())):
            if t > end:
                break
            if begin < t:
                intervals.append((begin, t - 1))
            begin = t + 1
        if begin <= end:
            intervals.append((begin, end))
        cache[cell] = intervals
        return intervals

    def _path(self, robot, reservations, limit, balanced=False, cutoff=None,
              expansion_cap=None):
        # SIPP is fast for minimum-arrival paths. Weighted congestion search
        # needs full (cell,time) states, because time and traffic trade off.
        if balanced:
            return self._path_astar(robot, reservations, limit, balanced=True,
                                    cutoff=cutoff, expansion_cap=expansion_cap)
        return self._path_sipp(robot, reservations, limit, cutoff=cutoff,
                               expansion_cap=expansion_cap)

    def _path_sipp(self, robot, reservations, limit, cutoff=None, expansion_cap=None):
        # Safe Interval Path Planning compresses all legal waiting times in
        # each cell into intervals. Earliest arrival dominates later arrivals
        # in the same interval because the robot can safely wait there.
        occupied, edges, parked, last_use, traffic, cache = reservations
        start, goal = self.instance.starts[robot], self.instance.goals[robot]
        heuristic = self.heuristics[robot]
        if heuristic[start] < 0 or heuristic[start] > limit:
            return None
        if last_use.get(goal, -1) > limit or goal in parked:
            return None
        start_intervals = self._safe_intervals(start, reservations)
        if not start_intervals or start_intervals[0][0] != 0:
            return None
        initial = (start, 0)
        best = {initial: (0, 0)}
        parent = {initial: None}
        queue = [(heuristic[start], 0, 0, start, 0)]
        search_deadline = self.deadline if cutoff is None else min(self.deadline, cutoff)
        pops = 0
        while queue:
            _, penalty, negative_t, cell, interval_id = heappop(queue)
            t = -negative_t
            state = (cell, interval_id)
            if best.get(state) != (t, penalty):
                continue
            pops += 1
            if expansion_cap is not None and pops > expansion_cap:
                return None
            if pops % 64 == 0 and perf_counter() >= search_deadline:
                return None
            source_end = self._safe_intervals(cell, reservations)[interval_id][1]
            if (cell == goal and source_end == self.instance.horizon
                    and t >= last_use.get(goal, -1)):
                states = []
                while state is not None:
                    states.append(state)
                    state = parent[state]
                states.reverse()
                path = [start]
                for following_state in states[1:]:
                    arrival = best[following_state][0]
                    while len(path) < arrival:
                        path.append(path[-1])
                    path.append(following_state[0])
                return path
            for following in self.neighbours[cell]:
                if heuristic[following] < 0:
                    continue
                for next_id, (begin, end) in enumerate(self._safe_intervals(following, reservations)):
                    arrival = max(t + 1, begin)
                    latest = min(end, source_end + 1, limit - heuristic[following])
                    while (arrival <= latest
                           and (arrival * self.v + following) * self.v + cell in edges):
                        arrival += 1
                    if arrival > latest:
                        continue
                    next_state = (following, next_id)
                    next_penalty = penalty + traffic[following]
                    label = (arrival, next_penalty)
                    if label < best.get(next_state, (1 << 60, 1 << 60)):
                        best[next_state] = label
                        parent[next_state] = (cell, interval_id)
                        heappush(queue, (arrival + heuristic[following], next_penalty,
                                         -arrival, following, next_id))
        return None

    def _path_astar(self, robot, reservations, limit, balanced=False, cutoff=None,
              expansion_cap=None):
        occupied, edges, parked, last_use, traffic, _cache = reservations
        start, goal = self.instance.starts[robot], self.instance.goals[robot]
        heuristic = self.heuristics[robot]
        if heuristic[start] < 0 or heuristic[start] > limit:
            return None
        last_goal_visit = last_use.get(goal, -1)
        if last_goal_visit > limit:
            return None
        # In repair mode a congestion pair is weighted against its SOC cost.
        ratio = ((2.0 / 3.0) * self.instance.lb_sum_of_costs
                 / self.instance.congestion_scale) if balanced else 0.0
        search_deadline = self.deadline if cutoff is None else min(self.deadline, cutoff)
        queue = [(heuristic[start], 0, 0, start)]
        parent = {start: -1}
        penalties = {start: 0}
        pops = 0
        while queue:
            _, penalty, negative_t, cell = heappop(queue)
            t = -negative_t
            state = t * self.v + cell
            if penalties.get(state) != penalty:
                continue
            pops += 1
            if expansion_cap is not None and pops > expansion_cap:
                return None
            if pops % 128 == 0 and perf_counter() >= search_deadline:
                return None
            if cell == goal and t >= last_goal_visit:
                path = []
                while state != -1:
                    path.append(state % self.v)
                    state = parent[state]
                return list(reversed(path))
            next_t = t + 1
            if next_t > limit:
                continue
            for following in self.neighbours[cell] + [cell]:
                if next_t + heuristic[following] > limit:
                    continue
                next_state = next_t * self.v + following
                parked_at = parked.get(following)
                if next_t in occupied.get(following, ()) or (parked_at is not None and next_t >= parked_at):
                    continue
                if (next_t * self.v + following) * self.v + cell in edges:
                    continue
                next_penalty = penalty + (traffic[following] if following != cell else 0)
                if next_penalty < penalties.get(next_state, 1 << 60):
                    penalties[next_state] = next_penalty
                    parent[next_state] = state
                    heappush(queue, (next_t + heuristic[following] + ratio * next_penalty,
                                     next_penalty, -next_t, following))
        return None

    def _construct(self, order, cutoff=None, limit_override=None, expansion_cap=None):
        paths = [None] * self.n
        reservations = self._reserve(paths)
        for robot in order:
            if perf_counter() >= (self.deadline if cutoff is None else cutoff):
                return None, None
            limit = (self.instance.horizon if self.best is None else
                     min(self.instance.horizon,
                         (self.best_cost - 150000) * self.instance.lb_makespan // 750000))
            if limit_override is not None:
                limit = min(limit, limit_override)
            path = self._path(robot, reservations, limit, cutoff=cutoff,
                              expansion_cap=expansion_cap)
            if path is None:
                return None, robot
            paths[robot] = path
            self._block(path, *reservations)
        return paths, None

    def _cost(self, paths):
        arrivals = [len(path) - 1 for path in paths]
        counts = [0] * self.v
        congestion = 0
        for path in paths:
            for cell in set(path) & self.corridor:
                congestion += counts[cell]
                counts[cell] += 1
        return (750000 * max(arrivals) // self.instance.lb_makespan
                + 150000 * sum(arrivals) // self.instance.lb_sum_of_costs
                + 100000 * congestion // self.instance.congestion_scale)

    def _offer(self, plan):
        cost = self._cost(plan)
        if self.best_cost is not None and cost >= self.best_cost:
            return False
        receipt = self.submit(plan)
        self.deadline = min(self.deadline, perf_counter() + receipt["remaining_s"] - 0.25)
        if receipt["accepted"]:
            self.best_cost = receipt["cost"]
            self.best = [list(path) for path in plan]
            return True
        return False

    def _improve(self):
        iteration = 0
        stale = 0
        while perf_counter() < self.deadline and iteration < 2400 and stale < 800:
            iteration += 1
            stale += 1
            if iteration % 25 == 0:
                order = list(self.seed_orders[(iteration // 25) % len(self.seed_orders)])
                for _ in range(max(1, self.n // 8)):
                    a, b = self.rng.randrange(self.n), self.rng.randrange(self.n)
                    order[a], order[b] = order[b], order[a]
                for _ in range(4):
                    plan, failed = self._construct(order, expansion_cap=5000)
                    if plan is not None:
                        if self._offer(plan):
                            stale = 0
                        break
                    if failed is None:
                        break
                    order.remove(failed)
                    order.insert(0, failed)
                continue
            arrivals = [len(path) - 1 for path in self.best]
            makespan = max(arrivals)
            delays = [arrivals[r] - self.distance[r] for r in range(self.n)]
            critical = [r for r in range(self.n) if arrivals[r] == makespan]
            if iteration % 4 == 0:
                anchor = self.rng.randrange(self.n)
            elif iteration % 4 == 1:
                anchor = self.rng.choice(critical)
            else:
                anchor = max(range(self.n), key=lambda r: (delays[r], self.rng.random()))
            size = [1, 4, 8, 16, max(24, self.n // 3)][iteration % 5]
            size = min(size, self.n)
            cells = set(self.best[anchor])
            scores = [(len(cells.intersection(self.best[r])) + self.rng.random(), r)
                      for r in range(self.n) if r != anchor]
            scores.sort(reverse=True)
            chosen = [anchor] + [r for _, r in scores[:size - 1]]
            # Occasionally include all makespan-critical paths to seek a smaller makespan.
            shrink = iteration % 6 == 0 and makespan > self.instance.lb_makespan
            if shrink:
                chosen = list(dict.fromkeys(critical + chosen))
            if iteration % 3 == 0:
                self.rng.shuffle(chosen)
            else:
                chosen.sort(key=lambda r: (-delays[r], -self.distance[r]))
            reservations = self._reserve(self.best, chosen)
            plan = list(self.best)
            for robot in chosen:
                # Full time labels retain traffic alternatives that earliest-
                # arrival interval compression can discard during cost repair.
                path = self._path_astar(robot, reservations, makespan - int(shrink),
                                        balanced=(iteration % 3 == 0))
                if path is None:
                    break
                plan[robot] = path
                self._block(path, *reservations)
            else:
                if perf_counter() < self.deadline:
                    if self._offer(plan):
                        stale = 0
