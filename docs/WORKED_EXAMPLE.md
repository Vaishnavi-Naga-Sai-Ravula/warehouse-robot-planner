# Work through two robots by hand

Use `demo.html` to step through this example. It is a small teaching map,
not one of the nine public benchmark cases.

## Map and assignments

The warehouse is a 3-column, 2-row grid with no walls:

```text
Cell IDs:     Coordinates:
0  1  2       (0,0) (1,0) (2,0)
3  4  5       (0,1) (1,1) (2,1)
```

Robot 0 starts at cell 0 and wants cell 1. Robot 1 starts at cell 1 and wants
cell 0. Cells 0 and 1 are adjacent, so each isolated shortest route takes one
action. But the robots cannot both take those routes at the same time.

## The tempting answer fails

```text
Robot 0: [0, 1]
Robot 1: [1, 0]
```

At time 0, they are in different cells. At time 1, they are still in different
cells. Nevertheless, they traverse the same edge in opposite directions.
That is an **edge-swap conflict**, and the validator rejects the complete plan.
Checking only cell occupancy would miss this error.

## Reserve Robot 0 first

Suppose the priority order is `[0, 1]`. Robot 0 gets path `[0, 1]`.

- Reserve cell 0 at time 0.
- Reserve directed move 0→1 during the step ending at time 1.
- Reserve cell 1 from time 1 onward, because Robot 0 parks there permanently.

Now plan Robot 1 around those reservations.

From its state `(cell=1, time=0)`, the possibilities include:

| Proposed next state | Legal? | Reason |
|---|---|---|
| `(0, 1)` | No | Opposite of Robot 0's reserved move 0→1 |
| `(1, 1)` | No | Robot 0 occupies and parks at cell 1 |
| `(2, 1)` | Yes | Free neighboring cell, but it is not the destination |
| `(4, 1)` | Yes | Free neighboring cell; leads to the short detour |

Robot 1 can take `[1, 4, 3, 0]`. Each step is a legal cardinal move.

| Time | Robot 0 | Robot 1 |
|---:|---:|---:|
| 0 | 0 | 1 |
| 1 | 1 | 4 |
| 2 | 1 | 3 |
| 3 | 1 | 0 |

The shorter path is padded by repeating its final cell. Robot 0 remains at
cell 1 at times 2 and 3. The plan has no vertex conflict and no edge swap.

## How BFS helps A*

Ignoring other robots, BFS from Robot 1's goal, cell 0, gives:

```text
Distances to cell 0:
0  1  2
1  2  3
```

At state `(1, 0)`, `g=0`, `h=1`, so ordinary A* priority `f=g+h=1`.
The direct successor is rejected by reservations. At `(4, 1)`, `g=1`, `h=2`,
so `f=3`. After `(3, 2)`, `g=2`, `h=1`, again `f=3`. At goal `(0, 3)`,
`g=3`, `h=0`, so `f=3`.

The static distance did not predict the collision; it remained a lower bound.
Reservations supplied the missing coordination information. A* may inspect
other states as well; this table explains one valid route, not a promise about
the exact heap-pop sequence of every implementation mode.

## Compute the objective

Arrival times are 1 and 3. Therefore:

```text
makespan = max(1, 3) = 3
sum_of_costs = 1 + 3 = 4
```

The independent-distance lower bounds here are `lb_makespan=1` and
`lb_sum_of_costs=2`. If this toy instance declares cell 1 to be its only
corridor and `congestion_scale=1`, both robots visit cell 1, so its two visitors
contribute `2 × 1 // 2 = 1` congestion unit. They visit at different times;
that still counts as shared corridor use.

The toy integer objective would be:

```text
750000 × 3 // 1 + 150000 × 4 // 2 + 100000 × 1 // 1
= 2250000 + 300000 + 100000
= 2650000 units = 2.65 displayed cost
```

The demo's toy maps use no declared corridor cells for simplicity. The above
calculation deliberately adds a corridor to illustrate that objective term.
The actual public cases have their own supplied normalizers and corridors.

## How LNS changes the question

Priority planning asks, “What route can the next robot take around the fixed
routes?” LNS asks, “Which small group should we reconsider together?”

For this example, select both robots, remove their old reservations, and
try the reverse priority. Robot 1 might go directly to cell 0 while Robot 0
detours through the lower row to cell 1. The complete objective may be equal.
Our strict-improvement acceptance rule does not replace an incumbent with an
equal-cost plan. On a larger map, replanning a group can reduce delay or use
a different corridor and create a strict improvement.

## Explain this example aloud

“Two independently shortest paths create an edge swap. I reserve the first
robot's cells and move, including its parked goal. The other robot's A* state
includes time, so it checks those reservations and chooses a legal detour.
The independent validator then checks the full joint plan and computes its
cost. Group repair can reconsider the initial priority decisions.”
