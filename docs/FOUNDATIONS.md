# Warehouse Robot Planner: learn it from zero

## 1. Start with the warehouse story

A warehouse has many robots. Each robot already has an assigned starting position and destination. We must decide where every robot should be at every time step so that all reach their destinations without hitting one another.

This project plans routes; it does not assign orders to robots, detect objects with a camera, or control real motors. Its map and start/goal assignments are already provided. The term **multi-agent pathfinding**, or **MAPF**, means finding compatible paths for several moving agents. The exact movement and collision assumptions matter when comparing MAPF algorithms. [Stern et al., 2019](https://arxiv.org/abs/1906.08291).

## 2. The grid becomes a graph

Imagine a floor divided into square cells. A cell can be free or blocked by a shelf. A **graph** describes connections: each free cell is a **vertex**, and a legal connection between neighboring cells is an **edge**. A robot may move north, south, east, or west. It may also wait in its current cell. Diagonal movement is not permitted here.

The input encodes a cell with one integer:

```text
cell = y × width + x
x = cell % width
y = cell // width
```

For width `5`, cell `13` is `(x=3, y=2)`. `%` means remainder; `//` means integer division. These operations let the program store a whole grid in a simple one-dimensional array.

**A path** is a list of occupied cells, starting at time zero. `[6, 6, 7, 8]` means start at cell 6, wait for one step, move to 7, then move to 8. Four entries represent three actions. Simulation steps and computation seconds are different: a route can take 40 warehouse steps while the computer spends 0.1 seconds calculating it.

## 3. Find one robot's shortest route first

If only one robot existed, **breadth-first search**, or **BFS**, would find a shortest path because every move has the same cost of one step. BFS explores positions in layers: distance zero, distance one, distance two, and so on. A queue keeps the earliest discovered positions at the front.

We can run BFS backward from a robot's goal to obtain the distance from every reachable cell to that goal. Distances account for shelves and walls. A value of `-1` represents an unreachable cell. Running this once per goal allows the distances to be reused for many searches.

**A-star**, written **A***, directs search toward promising states. It orders alternatives using `f = g + h`: `g` is the cost already paid, and `h` estimates the remaining cost. The BFS distance is an exact remaining distance when other robots are ignored. Reservations can force waiting or detours, so this distance never overestimates the remaining number of actions. That makes it an **admissible heuristic**. Standard A* can find a shortest path under its search assumptions; this does not make the entire multi-robot method globally optimal. [Hart, Nilsson and Raphael, 1968](https://ai.stanford.edu/~nilsson/OnlinePubs-Nils/PublishedPapers/astar.pdf).

## 4. Independent shortest paths can collide

Planning each robot separately is insufficient. Two individually excellent routes may require the same narrow passage at the same time.

There are two prohibited conflicts in this benchmark:

| Conflict | Example | Why it fails |
|---|---|---|
| Vertex conflict | Robot A and B both occupy cell 7 at time 3 | They occupy the same space simultaneously |
| Edge-swap conflict | A moves 6→7 while B moves 7→6 in the same step | They exchange positions across the same edge |

Using the same corridor at different times can be legal. Following another robot into the cell it has just vacated can also be legal, provided there is no vertex conflict or opposite-direction swap. These are the benchmark's discrete rules; they do not model every possible physical clearance requirement.

## 5. Add time to the search

A cell can be unsafe at time 4 and safe at time 5. Therefore, the search state is **`(cell, time)`**, rather than just `cell`. This is a **space-time graph**.

A transition from `(6, 2)` to `(7, 3)` is a move. A transition from `(6, 2)` to `(6, 3)` is a wait. The goal is to reach the destination at a time when the robot can remain there safely.

A **reservation table** records earlier planned robots' occupied cells and directed moves. When searching for another robot, reject a move if its destination is reserved at the next time step, or if a reserved robot takes the opposite edge during that step. Space-time search and reservation tables are established cooperative-pathfinding techniques. [Silver, 2005](https://ojs.aaai.org/index.php/AIIDE/article/view/18726).

The reservation checks protect only the already fixed paths. We still need a complete plan for every robot before submitting an answer.

The delivered solver speeds up minimum-arrival search with **Safe Interval Path Planning**, or **SIPP**. Instead of storing every free `(cell, time)` separately, it groups uninterrupted free times into intervals. If a cell is occupied at times 3 and 7, its intervals could be `[0,2]`, `[4,6]`, and `[8,horizon]`. Within one interval, an earlier arrival can wait safely to imitate a later arrival. The search therefore keeps the earliest arrival for that cell and interval, reducing repeated waiting states. Edge-swap checks are still necessary. SIPP is an established method by Phillips and Likhachev, not a new algorithm invented here. [Phillips and Likhachev, ICRA 2011](https://www.cs.cmu.edu/~maxim/files/sipp_icra11.pdf).

In our code, reservations cut off intervals when a robot parks permanently. A transition chooses the earliest safe destination arrival, waiting in the source cell when needed. The returned cell-by-cell path explicitly reconstructs those waits. A goal is accepted only in an interval remaining free to the horizon. This compression is used for minimum-arrival search; repairs that trade arrival time against traffic use full `(cell,time)` A* states. Earlier arrival does not dominate every later arrival when route-history congestion costs also matter. Neither mode proves optimality for the complete fleet objective.

## 6. Finished robots stay at their goals

A robot does not disappear after finishing. If one path is shorter than the others, the validator keeps repeating its last cell. A finished robot therefore continues blocking its goal.

This changes planning. If Robot A parks in a narrow passage too early, Robot B may lose its only route. The planner must reserve a completed robot's goal for later times and must not settle a new robot at a goal that an already planned path needs later.

An early visit to the goal is not necessarily the arrival time. For path `[start, goal, other, goal, goal]`, the final uninterrupted goal suffix starts at time 3, so arrival is 3. Repeated goal cells at the end do not increase arrival time.

## 7. Priority determines whose route is fixed first

**Prioritized planning** chooses an order, finds a path for the first robot, reserves it, then plans the next robot around those reservations. It is faster than searching all robots' movements jointly, but the order matters.

Possible orders include long-distance robots first and robots with constrained destinations first. A low-priority robot may have no path under earlier reservations even though a joint solution exists. Promoting a failed robot and rebuilding the order can help. Trying more orders improves opportunities; it is not a completeness proof.

The implemented planner also estimates **goal-parking dependencies** from the geometry. It traces one isolated shortest route for each robot. If robot A's route passes through robot B's goal, it records a preference for planning A before B: A may need to pass before B parks. It builds orders favoring robots with few such incoming dependencies, using distance and fixed-seed tie choices. Another order delays goals that many isolated routes visit. These are preferences, not hard logical constraints: different routes can avoid a goal, and cyclic dependencies can occur. The algorithm breaks such ordering ties heuristically rather than proving all dependencies can be satisfied.

A small example makes this concrete. There is a three-cell horizontal passage `left—center—right`, plus a side bay connected above `center`. Robot A starts at `center` and its goal is also `center`. Robot B starts at `left` and wants `right`. Planning A first can park it immediately and block B. A legal coordinated answer instead uses the bay:

| Time | Robot A | Robot B |
|---|---|---|
| 0 | center | left |
| 1 | bay | center |
| 2 | center, its goal | right, its goal |

No cells are shared at a time and no opposite edges are swapped. Planning B first gives A a reason to leave its goal temporarily. This demonstrates why an individually shortest path can obstruct the fleet and why the benchmark defines arrival as final settling, rather than first goal contact.

## 8. Improve part of a plan instead of rebuilding everything

Once a legal plan exists, a better strategy is to reconsider a small group of robots while leaving the others fixed. This is **large-neighborhood search**, or **LNS**:

1. Select a group of robots whose routes might be improved.
2. Temporarily remove that group's paths from the reservations.
3. Keep all other robots fixed.
4. Replan the selected group in a different order or under a tighter completion-time target.
5. Keep the replacement only when it improves the true complete-plan objective.

MAPF-LNS is an established research direction, not a newly invented algorithm name for this project. Our program is a benchmark-oriented implementation of these ideas, rather than a claim to reproduce every feature or result of the published MAPF-LNS system. [Li, Chen, Harabor, Stuckey and Koenig, IJCAI 2021](https://www.ijcai.org/proceedings/2021/568).

The implemented planner combines minimum-arrival SIPP, space-time A* for neighborhood repairs, sometimes with an additive traffic term, geometry-derived priority orders, failure promotion, complete-plan reconstruction, and subset repair. A group is anchored on a makespan-critical, delayed, or random robot, and other members are selected by spatial route overlap. It varies group sizes and orders. Periodically it includes all robots determining makespan and attempts to finish them one step earlier. It retains only strict improvements in the full objective, so it can get stuck on a plateau where progress would require a temporarily equal or worse plan.

Construction first tries progressively larger arrival horizons, capped by the supplied maximum, instead of allowing every unsuccessful search to explore the entire space-time graph immediately. Searches also have fixed expansion caps. Improvement ends at the deadline or after at most 2400 iterations or 800 consecutive iterations without an accepted improvement. These work limits make computation more controlled, but may exclude a legal solution or a useful improvement. When no complete plan is found, the solver returns no answer rather than claiming success.

## 9. The objective: what counts as a better plan?

**Makespan** is the latest arrival time: when the last robot finishes. **Sum of costs** is the sum of all robots' arrival times. Here, waits before arrival count just as moves do. Minimizing only makespan could make many robots wait unnecessarily; the sum term discourages that.

**Congestion** measures shared use of designated corridor cells. For each such cell, count the distinct robots visiting it up to their arrival times. If `k` distinct robots visit it, the cell contributes `k × (k - 1) // 2`, the number of unordered robot pairs. Three visitors contribute 3; four visitors contribute 6. Repeated visits by one robot do not create additional visitors. Robots need not visit simultaneously for this congestion term to increase.

Congestion is an objective penalty, while collisions are hard invalidity conditions. A legal plan can have high congestion. Waiting in the same route does not by itself reduce this distinct-visitor measure; routing traffic through other corridors may reduce it.

The validator computes these integer terms separately:

```text
cost_units = (750000 × makespan)     // lb_makespan
           + (150000 × sum_of_costs) // lb_sum_of_costs
           + (100000 × congestion)   // congestion_scale
```

`//` truncates each nonnegative term downward separately. `lb_makespan`, `lb_sum_of_costs`, and `congestion_scale` are supplied instance normalizers. The reported decimal is `cost_units / 1,000,000`; displayed reports may round it. The integer total decides ordering.

Example: makespan 24 with normalizer 20, sum 70 with normalizer 60, and congestion 12 with scale 10 produce `900000 + 175000 + 120000 = 1195000` units, displayed as `1.195`. The coefficients give makespan the largest nominal weight, but this is a weighted scalar objective, not a lexicographic rule where makespan always overrides everything else.

Some repair searches use an additive traffic proxy with priority `time + BFS_distance + λ × traffic_exposure`, where `λ = (2/3) × lb_sum_of_costs / congestion_scale`. This ratio comes from comparing the congestion coefficient `100000/congestion_scale` with the sum-of-costs coefficient `150000/lb_sum_of_costs` while completion time is capped. It leaves the BFS heuristic coefficient at one: this is **not Weighted A***, which increases the heuristic's coefficient. The proxy counts exposure on corridor entries and can count re-entry again, unlike the official distinct-visitor measure. Integer floors and joint interactions also limit the approximation. The exact full-plan cost decides acceptance; no congestion-optimality guarantee is claimed.

## 10. The benchmark rewards early complete answers

For `R` robots, the nominal budget is `4 + R/12` computation seconds. Checkpoints are at 1%, 10%, 50%, and 100% of this budget, with weights 30%, 30%, 20%, and 20%. For 60 robots, the budget is 9 seconds and the first checkpoint is just 0.09 seconds. A strong result found only near the end misses substantial early credit.

Every checkpoint uses the best valid complete plan available by then. Baseline cost scores `0.25`; reference cost scores `1.00`; interpolation between them is linear and clipped to `[0, 1]`. Missing valid output scores zero; a poor valid cost can also clip to zero. Some source-file comments mention older splits or `0.50`; the executable scoring constants and problem README specify `0.25` and the current 70/30 scheme.

Quality contributes 70 points across the suite, and robustness contributes 30 across shifted cases. An engineering multiplier can reduce these points for unstable scored outputs, invalid candidates, instance mutation, or overruns. Families with no legal result or performance below baseline trigger additional penalties. A final reference match alone is not a 100-point guarantee.

The published anchors were produced with more search time for the reference: `public_reference.json` states a 15× reference budget. They are comparison targets, not certified global optima. The public suite has nine cases; official evaluation may use fresh cases or seeds.

## 11. What this implementation can honestly claim

It can claim that each submitted complete plan is checked against the actual movement rules and objective, and that measured results describe those particular tests. It can explain how reservations prevent vertex and edge-swap conflicts, and how partial repair aims to improve plan quality within a deadline.

It cannot claim global optimality, completeness over all solvable MAPF instances, hidden-test guarantees, or immediate readiness for physical robots. Priority choices can lock out later robots; LNS explores selected changes, not every possible joint plan. A deadline or makespan cap can stop a search that would succeed with more time.

The current model assumes a static known grid, assigned goals, synchronized unit-time moves, and ideal execution. Real deployments need localization, robot footprints, acceleration and turning constraints, safety margins, and recovery when execution differs from the plan.

## 12. The research connection, with limits

The project uses AI **search and planning** methods. It does not train a machine-learning model. A heuristic here means a rule or estimate guiding search, not a learned prediction.

Conflict-based search, or CBS, is a different method that systematically branches on conflicts and can preserve optimality under its standard formulation. This project does not implement CBS, and classic CBS's guarantees do not automatically cover this benchmark's congestion objective. [Sharon, Stern, Felner and Sturtevant, AAAI 2012](https://ojs.aaai.org/index.php/AAAI/article/view/8140/7998).

Use the papers to explain established foundations and the code to explain what was actually implemented. A credible presentation separates published methods, your implementation decisions, measured evidence, and future work.

## 13. Enough Python vocabulary to read the adapter

| Term | Meaning in this project |
|---|---|
| Variable | A name holding a value, such as the number of robots |
| List | An ordered collection; a path is a list of cell IDs, and a complete plan is a list of paths |
| Tuple | A small fixed grouping, such as `(cell, time)` |
| Dictionary | A lookup from a key to a value; a reservation can map `(time, cell)` to the robot occupying it |
| Set | A collection without duplicates; useful for distinct corridor visitors or selected robots |
| Function | A named operation with inputs and a result, such as searching for a path |
| Class | A container for related operations and stored state; the evaluator creates a `Planner` object |
| Loop | Repeats an operation over robots, cells, or search alternatives |
| Condition | Selects behavior when something is true, such as rejecting a reserved destination |
| Queue | Removes items in arrival order; used by BFS |
| Heap / priority queue | Removes the item with the lowest priority value; used for A* search priorities |
| Receipt | The evaluator's response to a submitted plan, including validity, cost, and remaining time |
| `None` | Absence of a result, such as a failed path search; it is not a legal complete plan |

Python indentation groups code into blocks. A line inside a loop runs repeatedly; a line outside it runs after the loop. When presenting, explain the data flow rather than reciting each line: read map → compute distances → construct paths → check and submit complete plan → repair paths → retain best plan.

The interface is `Planner.solve(instance, submit_candidate)`. `instance` is the provided problem; `submit_candidate` is the allowed communication channel to the evaluator. The adapter must produce paths from those inputs. It must not inspect hidden state, mutate the problem, or access external files or networks during planning.
