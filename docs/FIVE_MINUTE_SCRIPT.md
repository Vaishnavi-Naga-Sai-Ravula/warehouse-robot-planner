# Five-minute presentation rehearsal

This script matches the delivered `bench-warehouse/adapters/myteam.py`. Insert measured results before presenting. Aim for about 120–135 words per minute and pause briefly on the demo and formula.

## 0:00–0:45 — Problem

“My project is Warehouse Robot Planner. The input is a warehouse floor represented as a grid, with blocked shelves and a fixed start and destination for every robot. The output says where each robot should be at every time step.

“A robot can move one cell north, south, east, or west, or wait. Two robots cannot occupy the same cell at the same time, and they cannot exchange places across an edge. A robot continues occupying its goal after it finishes.

“The challenge is coordination. Planning a shortest route for each robot separately can produce routes that collide.”

## 0:45–1:30 — Foundations

“I convert the free cells into a graph: cells are vertices and neighboring moves are edges. I compute a BFS distance map backward from each goal. This gives the shortest remaining distance when other robots are ignored.

“Then I account for time. A cell may be occupied now and available later. For minimum arrival, safe-interval search groups consecutive free times at a cell. An earlier arrival can wait within that interval, reducing repeated waiting states. A* priorities use arrival time plus BFS distance.

“The BFS estimate is a lower bound because other robots can force additional waiting or detours.”

## 1:30–2:25 — Coordination

“I initially plan robots in a priority order. After planning a robot, I reserve its occupied cells and directed edges at the relevant times. The next robot avoids those reservations. I also reserve a finished robot's goal for the remaining time.

“The order matters. Planning one robot first may leave another without a legal path. I derive parking preferences from routes that cross other robots' goals, try useful orders, and promote a robot that fails.

“This construction is heuristic: it does not guarantee a solution for every solvable instance. Its purpose is to produce a legal complete plan quickly, because the benchmark gives substantial credit to early answers.”

## 2:25–3:15 — Improvement

“After obtaining a plan, I improve selected groups of robots rather than repeatedly rebuilding every route. This is large-neighborhood search. I keep the other robots fixed, remove the selected group's reservations, and replan that group.

“The search can try a tighter completion-time target and alternative routes through corridors. Traffic-aware repairs retain full cell-and-time states and add a traffic-exposure cost to A*. This proxy does not optimize congestion exactly. I retain a replacement only when it improves the actual full-plan cost.

“These are established planning ideas. My work is their implementation and evaluation under this benchmark, not a claim that A* or MAPF large-neighborhood search is a new invention.”

## 3:15–4:00 — Objective and demo

“The cost combines three quantities. Makespan is the last robot's arrival time. Sum of costs adds every robot's arrival time. Congestion counts pairs of distinct robots using each designated corridor cell, even when their visits occur at different times.

“Collisions invalidate a plan; congestion only makes a legal plan more expensive. The benchmark normalizes these quantities and weights them 75, 15, and 10 percent using exact integer arithmetic.

“In the demo, I will show a narrow passage, explain one wait or detour, and show that the finished robot stays at its goal. Then I will show the reported objective components.”

## 4:00–4:40 — Evidence

“The public suite has nine instances, with budgets depending on robot count. It scores plans at 1, 10, 50, and 100 percent of the budget. The first two checkpoints together carry 60 percent of plan-quality credit.

“Here is the actual report: 9 valid cases out of nine, all within budget, and 6 final reference targets reached. The measured public score is 58.467 out of 100. The first-case replay was stable; that result is included rather than hidden. I distinguish these public results from unpublished evaluation. A final reference match is not a proof of optimality, and the reference used a larger search budget.”

## 4:40–5:00 — Limits and next experiment

“The method has no global optimality or completeness guarantee. It assumes a static map and synchronized ideal moves. My next experiment would compare construction alone against subset repair and congestion guidance on held-out maps under equal time budgets. That would show which decisions actually improve performance.”
