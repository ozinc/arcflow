# Use Case: Behavior Graphs

Model behavior trees as graph structures for game AI, robotics, and autonomous agents.

## The pattern

A behavior tree is a directed acyclic graph where:
- **Sequence** nodes execute children left-to-right, failing on first failure
- **Selector** nodes try children until one succeeds
- **Action** nodes perform actual work
- **Condition** nodes check state

In ArcFlow, the tree IS the graph. Nodes are graph nodes. Execution order is edge traversal.

## Why a graph database for BTs

- **Runtime modification** — add/remove/rewire behaviors with MERGE/DELETE
- **Shared blackboard** — node properties ARE the blackboard
- **Persistent state** — behavior state survives restarts (WAL-backed)
- **Algorithms** — use PageRank to find bottleneck behaviors, community detection for behavior clustering

## Implementation

```typescript
import { open } from '@arcflow/sdk'

const db = open('./behavior-graph')

// Define a behavior tree
db.batchMutate([
  "CREATE (root:BT_Sequence {name: 'patrol', status: 'idle'})",
  "CREATE (check:BT_Condition {name: 'is_enemy_visible', status: 'idle'})",
  "CREATE (move:BT_Action {name: 'move_to_waypoint', status: 'idle'})",
  "CREATE (attack:BT_Action {name: 'attack_enemy', status: 'idle'})",
])

db.batchMutate([
  "MATCH (root:BT_Sequence {name: 'patrol'}) MATCH (check:BT_Condition {name: 'is_enemy_visible'}) MERGE (root)-[:CHILD {order: 0}]->(check)",
  "MATCH (root:BT_Sequence {name: 'patrol'}) MATCH (move:BT_Action {name: 'move_to_waypoint'}) MERGE (root)-[:CHILD {order: 1}]->(move)",
  "MATCH (check:BT_Condition {name: 'is_enemy_visible'}) MATCH (attack:BT_Action {name: 'attack_enemy'}) MERGE (check)-[:ON_SUCCESS]->(attack)",
])

// Tick the behavior tree
const tick = db.query("CALL behavior.tick()")

// Check status
const status = db.query("CALL behavior.status()")
```

## Dynamic behavior modification

```typescript
// Add a new behavior at runtime
db.mutate("CREATE (heal:BT_Action {name: 'heal_self', status: 'idle'})")
db.mutate("MATCH (root:BT_Sequence {name: 'patrol'}) MATCH (heal:BT_Action {name: 'heal_self'}) MERGE (root)-[:CHILD {order: 2}]->(heal)")

// Remove a behavior
db.mutate("MATCH (n:BT_Action {name: 'attack_enemy'}) DETACH DELETE n")
```
