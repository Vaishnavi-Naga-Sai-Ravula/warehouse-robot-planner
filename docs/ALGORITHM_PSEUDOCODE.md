# Warehouse planner: readable pseudocode

This explains the delivered `bench-warehouse/adapters/myteam.py`; it is not executable Python. The submission is one adapter file with class `Planner`, loaded as `adapters.myteam:Planner`.

## Main algorithm

```text
Read the supplied map, starts, goals, horizon, and objective normalizers.
Set a deadline with a 0.25-second safety reserve.
Use a fixed pseudorandom generator for tie choices and perturbations.

For every robot goal:
    Compute its static BFS distance map.

Trace one isolated shortest route for each robot.
If robot A's route crosses robot B's goal:
    Prefer planning A before B parks there.
Build several dependency, distance, and constrained-goal priority orders.

For progressively larger arrival limits, capped by the instance horizon:
    For each seed order:
        Attempt complete prioritized construction with bounded search work.
        If robot r fails:
            Promote r and retry, at most four times for that order.
        If a complete candidate is accepted:
            Store it as the incumbent and leave initial construction.

If there is still no incumbent:
    Try perturbed seed orders with a larger expansion cap until the deadline.
If no complete candidate succeeds:
    Return no plan.

Preserve the incumbent while trying bounded alternative parking orders.
Run neighborhood improvement until the time or iteration limits are reached.
Return the best accepted complete plan.
```

## Prioritized construction

```text
Start with empty reservations.
For each robot in the chosen priority order:
    Search for its minimum-arrival path with SIPP.
    If search fails or a work limit is reached:
        Return the failed robot for priority repair.
    Reserve its timed cells, edges, and permanently occupied goal.
Return all paths in robot-index order.
```

An order controls which routes are fixed first. The output list still follows robot indices, not priority order.

## Minimum-arrival safe-interval search

```text
For each requested cell:
    Find free time intervals between reserved visits.
    End all future availability when a fixed robot parks there.

Start from the interval containing the robot's start at time zero.
Maintain the earliest arrival label for each (cell, interval).
Explore states ordered by arrival time plus static BFS distance.

For each neighbor and each feasible neighbor interval:
    Choose the earliest destination arrival after the current time.
    Wait in the source cell if the neighbor is not yet free.
    Ensure the source stays free until departure.
    Advance the arrival past any reverse-edge conflict.
    Keep the label if it improves earliest arrival,
        or improves the traffic tie at equal arrival.

Accept a goal only when it remains free through the horizon.
Reconstruct the cell-by-cell route, explicitly inserting waits.
```

Example: a robot reaches source cell `u` at time 2. Destination `v` is first free at time 5. If `u` remains free through time 4 and no reverse edge blocks the move, the transition waits at `u` at times 3 and 4 and reaches `v` at time 5. The reconstructed path includes both waiting entries. Earlier arrival in one safe interval supports the minimum-arrival compression; it does not prove optimality for congestion or for all robots jointly.

## Neighborhood repair

```text
Choose an anchor robot:
    a robot finishing last, a highly delayed robot, or a random robot.
Choose other robots whose routes overlap the anchor's route.
Vary group size and priority order.

On selected iterations:
    Include every robot currently finishing at the makespan.
    Try an arrival cap one step below that makespan.
Otherwise:
    Keep the arrival cap at the current makespan.

Reserve all nonselected robots.
For each selected robot:
    Use full space-time A* for neighborhood repair.
    Every third neighborhood trial adds a traffic-exposure cost.
    If any selected route fails:
        Discard the entire repair trial.
    Otherwise reserve the newly repaired route before planning the next.

For a complete trial:
    Compute the exact composite integer objective.
    Submit only a strict incumbent improvement.
    Keep it only if the independent evaluator accepts it.

Periodically try bounded complete reconstruction instead of a subset repair.
Stop at the deadline, 2400 rounds, or 800 nonimproving rounds.
```

## The balanced repair priority

```text
priority = time + BFS_distance + lambda × accumulated_traffic_exposure
lambda   = (2/3) × lb_sum_of_costs / congestion_scale
```

The coefficient comes from the ratio of the congestion and sum-of-costs terms:

```text
(100000 / congestion_scale) / (150000 / lb_sum_of_costs)
= (2/3) × lb_sum_of_costs / congestion_scale
```

The heuristic remains unmultiplied, so this is not Weighted A*. The traffic term is an additive surrogate: repeated corridor entries can be charged repeatedly even though official congestion counts distinct visitors. The true complete-plan objective, including separate integer floor operations, remains the acceptance rule.

## The acceptance rule and guarantees

Every offered answer contains every robot's route. The evaluator independently checks movement, parking, collisions, horizon, and objective. The incumbent improves monotonically in accepted cost. The search does not accept equal-cost or worse incumbents, does not explore every joint plan, and has finite work limits. It therefore claims neither completeness nor global optimality. The actual public measurements and replay result are recorded in `../BENCHMARKS.md`.
