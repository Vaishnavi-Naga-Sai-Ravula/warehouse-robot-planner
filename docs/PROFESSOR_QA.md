# Warehouse Robot Planner: questions to prepare for

## What problem are you solving?

I am solving a discrete multi-agent pathfinding problem. Each robot has a fixed start and goal on a blocked grid. I return a complete sequence of legal moves and waits for every robot, avoiding simultaneous cell occupancy and opposite-direction edge swaps. Finished robots remain at their goals.

## Is this AI? Is there machine learning?

It is AI in the classical search-and-planning sense. There is no training dataset, neural network, reinforcement-learning policy, or learned congestion model. BFS distances, A* search, and search heuristics use the supplied map directly.

## Why not run BFS separately for every robot?

BFS finds a shortest route for one robot when other robots are ignored. Those routes can collide. We retain BFS distance maps as useful lower-bound heuristics, then account for other robots through time-indexed reservations.

## What changes when time is included?

The state changes from a cell to a `(cell, time)` pair. Two visits to the same cell at different times can have different feasibility. A wait advances time without changing the cell, so it is a meaningful action.

## What is SIPP and why use it?

Safe Interval Path Planning groups uninterrupted free times for each cell. Our minimum-arrival search keeps a state for the cell and free interval, plus its earliest arrival. An earlier arrival can safely wait within that interval to mimic a later arrival. This often reduces repeated waiting states. It is an established single-robot planning technique, not a fleet-wide completeness guarantee.

## Do you drop edge swaps or goal parking when using intervals?

No. A move still checks the reverse reserved edge at its actual step, and may wait for a permitted departure. Safe intervals end before another robot parks permanently. A goal is accepted only in an interval free through the horizon. Reconstruction explicitly writes waiting cells into the returned path.

## Why not use one earliest arrival per interval for congestion optimization too?

Earliest arrival dominates later arrival for minimum completion time because waiting is allowed in the interval. With accumulated route-history traffic costs, an earlier high-exposure path need not dominate a later low-exposure path. Balanced repairs therefore use full `(cell,time)` states. Even that search uses an additive exposure proxy, so the exact distinct-visitor congestion objective is not optimized to a proven global optimum.

## Why is the heuristic admissible?

The BFS distance is the shortest remaining number of moves through the static map with other robots removed. Adding reservations cannot make the true remaining route shorter than that distance. This justifies a lower bound for the single-robot space-time search. It does not prove the multi-robot planner optimizes the full composite objective.

## Can your planner always find a solution when one exists?

No completeness guarantee is claimed. Earlier fixed routes may block a later robot, even when another joint arrangement would work. Promoting failed robots and changing subsets improves the search but does not enumerate all possibilities. Search deadlines and completion-time caps add further limits.

## Is the final result globally optimal?

No. The program maintains the best legal plan it has discovered within the allowed time. It does not have a proof that no better joint plan exists. Matching an organizer reference is a benchmark result, not an optimality certificate.

## What is new in your work?

The foundations are established: A*, SIPP, reservation-based prioritized planning, and MAPF large-neighborhood search. The contribution is the readable implementation and the particular choices used to construct early valid plans and improve them under this benchmark's objective and deadlines. I would not claim a novel research algorithm without a formal comparison, ablations, and evidence beyond these public cases.

## How does subset repair differ from rebuilding the whole plan?

Subset repair retains most robot paths and reserves them. It removes and replans only a chosen group. This concentrates computation on a local source of delay or congestion instead of repeatedly rebuilding unaffected paths. It can also miss improvements that require coordinated changes outside the selected group.

## Is congestion the same as a collision?

No. A collision invalidates the answer. Congestion adds cost when distinct robots use the same designated corridor cell, even at different times. Three distinct visitors create three pair contributions. Waiting or revisiting does not repeatedly count the same robot at that cell.

## Does the congestion-aware search minimize congestion exactly?

No. Construction uses traffic as a tie-break; selected repairs add a traffic-exposure term to the queue priority. The true cost still depends on the entire plan. The proxy can charge repeated corridor entries while the official objective counts distinct robot visitors. Improvements are retained only after strict comparison of the exact complete-plan objective and independent validation.

## Is this Weighted A*?

No. Balanced repairs use `t + h + λp`, not `t + wh`: the heuristic coefficient remains one. `p` is accumulated corridor-traffic exposure. `λ = (2/3) × lb_sum_of_costs/congestion_scale` compares the benchmark's congestion and sum-of-costs coefficients while a makespan cap is imposed. It is a surrogate path objective, not a proof of optimality for the fleet's congestion-inclusive cost.

## How do parking dependencies work?

The planner traces one isolated shortest path per robot. If A's path crosses B's goal, it prefers A before B so B does not park too early. This is derived from starts, goals, and traversable geometry, not an instance name, seed, profile, digest, or construction witness. Dependencies may cycle or vanish on alternative routes, so they are planning preferences rather than mandatory precedence constraints.

## Can a work cap make the planner miss an existing path?

Yes. A arrival-time limit can exclude a necessary detour or wait; an expansion cap or deadline can stop before discovery. The implementation broadens construction horizons and tries other orders to reduce that risk, but does not claim completeness. The supplied instance horizon remains a hard validity limit even when more time would otherwise help.

## Why stop after stagnation instead of using all remaining seconds?

The planner caps improvement at 2400 iterations or 800 consecutive iterations without an accepted improvement, as well as the wall-clock deadline. This limits unproductive search and makes the amount of attempted work more controlled. It can also stop before an improvement that would appear later; these are implementation choices to evaluate empirically, not theoretically optimal constants.

## What are makespan and sum of costs?

Makespan is the latest final arrival. Sum of costs adds all robots' final arrival times. Waiting before arrival contributes to both. The final arrival is the start of the uninterrupted suffix at the goal, so a temporary earlier goal visit does not count as finishing.

## Why these objective weights?

They are specified by the benchmark: 750000 for normalized makespan, 150000 for normalized sum of costs, and 100000 for normalized corridor congestion. I preserve those coefficients and the separate integer floor operations. I do not claim they are universally optimal warehouse design weights.

## What is the complexity?

For a grid graph with `V` usable cells and `E` neighbor connections, one BFS is `O(V + E)`. A finite space-time graph with horizon `H` has at most `V(H + 1)` states and at most five outgoing actions per state. SIPP uses one state per cell and safe interval instead, which can be much smaller when cells have few blocked times. With many distinct reservations, interval counts can grow, and this is not a worst-case fleet-wide speedup guarantee. Repeated searches and repairs add work. The joint multi-robot problem has up to `V^R` position combinations before excluding collisions for `R` robots. I measure runtime empirically rather than claiming a small worst-case bound for the entire planner.

## Why not use optimal CBS?

CBS is a valuable comparison method: it branches on conflicts rather than fixing one priority order. Standard CBS has optimality results for its usual MAPF objective and assumptions, but can require substantial work with many conflicts. This deadline-driven project chooses prioritized construction and subset repair. I have not established that this choice dominates CBS, and standard CBS would need careful adaptation to optimize this congestion-inclusive objective.

## How do you know the output is legal?

The independent validator checks starts, goals, passable cells, step legality, horizon limits, vertex conflicts, and edge swaps on padded paths. It computes the objective itself. A visualization helps inspect a plan, but a visually plausible animation is not the validity test.

## What benchmark evidence will you show?

Show the actual report with budget, first-valid time, all checkpoint costs, accepted/rejected candidates, objective components, and final reference gap. Include failures and distinguish a full official-harness run from any temporary experimental test. Discuss the public suite separately from unseen evaluation. Do not substitute a planned target for a measured result.

## Is your solver deterministic?

Use the actual replay evidence before claiming this. Fixed tie rules and a fixed pseudorandom seed make decisions reproducible for a fixed amount of work, but a wall-clock deadline can change how many iterations complete. The benchmark checks stability of scored outputs rather than demanding an identical candidate stream. One successful run does not prove reproducibility.

## Would this work on real warehouse robots immediately?

The planner solves an abstract model. Physical deployment would require footprint and clearance constraints, localization, motion limits, synchronization or timing tolerances, and execution monitoring with replanning. I would present it as a planning prototype rather than a deployed robot controller.

## Did AI tools help write it?

Answer accurately. The event allows AI coding assistance, but requires readable and explainable code. If assistance was used, say so and explain the parts you understand: the state, reservations, heuristic, repair policy, objective, validation, and limitations. Do not claim unaided authorship or deeper verification than you performed.

## What experiment would you do next?

An ablation study: compare initial prioritized planning, the same planner with subset repair, and the same method with congestion guidance. Use the same held-out instances and budgets, repeat runs, and report first-valid time, makespan, sum of costs, congestion, final score, and failures. This would separate the value of each design choice from chance or public-case tuning.

## How should you handle a question you cannot answer?

State the boundary precisely: “I have not evaluated that case yet. The model currently assumes ____. I would test it by ____.” A clear limitation and a concrete experiment are more credible than an unsupported guarantee.
