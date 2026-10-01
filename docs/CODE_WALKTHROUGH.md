# Read the Warehouse Planner code by following the data

Checked against the delivered `bench-warehouse/adapters/myteam.py`. The event entry point is `adapters.myteam:Planner`. No benchmark outcome is assumed here.

## `solve`: the main flow

The evaluator creates a `Planner` and calls `solve(instance, submit_candidate)`. The method stores the problem and callback, creates a time deadline with a safety reserve, initializes a fixed pseudorandom generator, and precomputes legal neighbors and BFS maps.

It traces one isolated shortest route per robot and records which other robots' goals occur on that route. This creates a directed preference: the traveler should be planned before a robot that may park on its route. Three orders favor low incoming dependency counts, with distance and fixed-seed tie choices. The dependency graph may contain cycles, so this selection is an ordering heuristic, not a topological feasibility proof. Another seed order puts goals visited by fewer isolated routes earlier. Long-distance, constrained-goal, and short-distance orders are also included.

Construction tries arrival limits based on the supplied makespan lower bound: `L + 4`, `L + max(8, L//4)`, `2L + 8`, and the instance horizon, removing duplicates and capping each at that horizon. Each initial search has an 8,000-pop cap. If an order fails for a particular robot, that robot is moved to the front; there are up to four attempts per order. Later perturbed orders use a 32,000-pop cap.

After a complete plan is accepted, up to 32 bounded reconstruction trials explore alternative parking orders when makespan remains more than one step above `L`. These use a 5,000-pop cap. The method then starts neighborhood improvement. It ultimately returns the best complete plan stored, or `None` if construction never succeeded before the deadline.

The output paths remain in **robot-index order**, even when robots were planned in a different priority order. Mixing these two orders would assign the wrong route to each robot.

## `_distances`: the reusable BFS estimate

This runs a queue-based search from one goal through the static graph. Each discovered cell gets its minimum number of moves to that goal. Other robots are ignored at this stage. These distance maps are reused by every subsequent search for the corresponding robot, which avoids repeating the same static calculation.

## `_reserve` and `_block`: record fixed robots

`_reserve` builds reservations from a list of paths, excluding any robots selected for replanning. `_block` adds one path.

Reservations contain a set of occupied times per cell, directed edges, the time each goal becomes permanently occupied, and the last explicit use time of each cell. Directed-edge encodings include the step and both endpoints. An additional cache stores each cell's free intervals; adding a path invalidates cached intervals for the affected cells.

It also counts how many fixed robots use each designated corridor cell. A set of cells per path ensures repeated visits by the same fixed robot count only once in that fixed-traffic table.

## `_safe_intervals`: compress the free times at a cell

For each cell, this method sorts its explicitly occupied times and takes the free gaps. Intervals have inclusive integer endpoints. It stops at the instance horizon, or one step before a fixed robot parks at that cell. A permanently occupied cell therefore has no later safe interval. The result is cached until adding a new path changes the reservations at that cell.

## `_path`: choose the single-robot search mode

Prioritized construction and complete reconstruction call `_path_sipp`. Neighborhood repair calls `_path_astar` directly for both ordinary minimum-arrival and additive-traffic modes. Full cell-and-time labels retain traffic alternatives that earliest-arrival interval compression can discard. Every mode respects the same fixed paths, edge-swap constraints, goal parking, and arrival limit.

## `_path_sipp`: minimum-arrival Safe Interval Path Planning

The state is `(cell, interval_id)` with a stored earliest arrival time. Its queue priority starts with `arrival_time + BFS_distance`; traffic exposure is only a tie preference. An earlier arrival in the same safe interval can wait until a later arrival time, so storing every such wait separately is unnecessary for the minimum-arrival objective. This dominance argument does not mean it minimizes route-history congestion.

For a neighboring destination interval, the candidate arrival is `max(current_time + 1, interval_begin)`. It must fit the destination interval, allow waiting in the source interval until departure, and leave enough time to reach the goal under the arrival limit. If a reverse edge is reserved at that step, the code advances arrival while it remains feasible.

The goal is accepted only when its interval extends through the instance horizon and the arrival is no earlier than the last fixed use of the goal. A goal already permanently occupied by another fixed robot is rejected. When reconstructing the path, the code repeats the previous cell for every waiting step before adding the next cell. Thus interval compression still produces the explicit path format expected by the validator.

SIPP checks time every 64 valid queue pops and also enforces any expansion cap. Its traffic preference can discard a later low-exposure arrival in favor of an earlier high-exposure one, so no exact congestion tie-optimality claim is made.

## `_path_astar`: time-and-traffic repair search

Here the state is `(cell,time)`, encoded as `time × number_of_grid_cells + cell`. A successor is a neighbor move or a wait. The search rejects occupied destinations, permanently parked destinations, and the reverse of a reserved edge.

Balanced repairs use priority `time + BFS_distance + λ × traffic_exposure`, where `λ = (2/3) × lb_sum_of_costs / congestion_scale`. This adds accumulated proxy cost rather than multiplying the heuristic; it is not Weighted A*. The ratio approximates the congestion-versus-sum-of-costs tradeoff under a makespan cap. A longer route may be preferred if it avoids enough exposure.

Entering a cell used by many fixed robots adds a penalty; waiting does not. Re-entry can add the proxy again, although official congestion counts a robot only once per cell. The proxy guides search; exact complete-plan cost determines improvement. Goal acceptance requires arriving no earlier than the last fixed use of the goal.

A* checks time every 128 valid queue pops and enforces any expansion cap. Neither search mode establishes the best robot ordering or the optimum fleet objective; arrival caps, expansion caps, and the deadline can terminate an otherwise promising search.

## `_construct`: build a complete initial schedule

For each robot in the chosen order, it searches for a path and reserves it. If a robot fails, the function returns that failure so `solve` can change the order. It does not submit a partially completed fleet plan. Before any incumbent, its default limit is the instance horizon. After an incumbent, it uses a completion cap derived from the incumbent cost, then respects any tighter explicit limit. That cap prunes search rather than changing the evaluator's objective.

Once every robot has a route, it returns the complete list in robot-index order. Complete candidates are passed to `_offer`.

## `_cost` and `_offer`: decide what is worth submitting

`_cost` computes the three specified integer terms: normalized makespan, normalized sum of arrival times, and exact distinct-robot corridor congestion. For the paths generated here, the final entry is the final settling time; the independent validator remains authoritative for all candidates.

`_offer` submits only a strict cost improvement over the stored incumbent. The evaluator's receipt states whether the complete plan is accepted and returns its independently computed cost. An accepted improvement becomes the new stored best plan. The receipt's remaining time tightens the planner's deadline with a safety reserve.

The program does not accept worse or equal-cost plans as new incumbents. This preserves monotone incumbent quality, but can prevent crossing plateaus or temporarily worse solutions that might lead to a better final plan. It is not simulated annealing.

## `_improve`: choose a group and repair it

An anchor robot is chosen from three kinds of candidates: a robot currently determining makespan, a robot with a large delay above its isolated shortest distance, or a random robot. Other group members are chosen by the amount of spatial overlap with the anchor's current route. This overlap is a selection heuristic; it is not itself a timed collision.

The usual group sizes vary among 1, 4, 8, 16, and `max(24, fleet_size//3)`, bounded by fleet size. The order is shuffled in some iterations and based on delay/distance in others. Nonselected paths are reserved, then each selected robot is replanned around those fixed routes and already repaired members. Every third neighborhood iteration uses the additive congestion proxy search.

Most repairs cap each new route at the current makespan. Periodically the method includes all robots currently reaching that makespan and tries a cap of one step less. Including all makespan-critical robots is necessary for such a trial: keeping any one of their old routes would retain the old makespan. The expanded group can therefore be larger than the usual neighborhood-size choices.

If any selected robot cannot be replanned, the trial is discarded. If the complete trial succeeds in time, `_offer` compares the true composite cost before submission. Not every successful repair improves the objective; only strict improvements replace the incumbent.

Every 25th improvement iteration instead tries bounded complete-plan reconstruction using a perturbed seed order. The improvement loop ends at the deadline, 2400 total iterations, or 800 consecutive iterations without an accepted improvement, whichever comes first. An accepted improvement resets the stagnation counter. The fixed random seed controls random choices but a wall-clock deadline can still alter how many trials complete; replay evidence is needed before claiming identical scored outputs.

## Explain the code in one sentence

“I compute static distance maps, construct a complete plan with safe-interval search and timed reservations, and repair overlapping groups with arrival or traffic-aware search while keeping only independently accepted improvements.”

## What this code does not prove

It does not systematically enumerate all priority orders, all subsets, or all joint paths. A makespan cap can exclude a useful detour, and accepting only strict improvements can trap the search at a local optimum. Success on measured cases is evidence about those cases, not a proof of completeness, global optimality, or unseen-case performance.
