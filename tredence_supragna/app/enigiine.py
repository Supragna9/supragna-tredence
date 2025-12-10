import asyncio
import uuid
from typing import Dict, Callable, Any, Optional
from .models import GraphSpec, RunState, ExecutionLogEntry
from . import tools

# In-memory stores (simple)
GRAPHS: Dict[str, GraphSpec] = {}
RUNS: Dict[str, RunState] = {}

# Node registry: node functions that process the shared state
NODE_REGISTRY: Dict[str, Callable] = {}

def register_node(name: str):
    def _d(fn):
        NODE_REGISTRY[name] = fn
        return fn
    return _d

def create_graph(graph_id: str, graph: GraphSpec):
    GRAPHS[graph_id] = graph

def get_graph(graph_id: str) -> GraphSpec:
    return GRAPHS[graph_id]

def get_run(run_id: str) -> RunState:
    return RUNS[run_id]

async def run_graph(graph_id: str, initial_state: Dict[str, Any]) -> RunState:
    graph = get_graph(graph_id)
    run_id = str(uuid.uuid4())
    run_state = RunState(
        run_id=run_id,
        graph_id=graph_id,
        state=initial_state.copy(),
        current_node=graph.start_node,
        finished=False,
        log=[]
    )
    RUNS[run_id] = run_state

    current = graph.start_node
    visited = 0
    MAX_VISITS = 1000  # safety

    while current is not None and visited < MAX_VISITS:
        visited += 1
        run_state.current_node = current
        node_spec = next((n for n in graph.nodes if n.name == current), None)
        if node_spec is None:
            # nothing found: stop
            run_state.log.append(ExecutionLogEntry(node=current, before=run_state.state.copy(), after=run_state.state.copy(), note="node not found"))
            break

        before = run_state.state.copy()
        # call node handler
        handler = NODE_REGISTRY.get(node_spec.func)
        if handler is None:
            run_state.log.append(ExecutionLogEntry(node=current, before=before, after=before, note=f"handler '{node_spec.func}' not found"))
            break

        # node may be async or sync
        if asyncio.iscoroutinefunction(handler):
            result = await handler(run_state.state, node_spec.params or {}, tools.TOOLS)
        else:
            # run in thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, handler, run_state.state, node_spec.params or {}, tools.TOOLS)

        # handler may update state and optionally return next node override
        # Expect result to be dict: {"state": updated_state (optional), "next": node_name (optional), "note": str (optional)}
        if isinstance(result, dict):
            if "state" in result:
                run_state.state.update(result["state"])
            note = result.get("note")
            next_node = result.get("next")
        else:
            note = None
            next_node = None

        after = run_state.state.copy()
        run_state.log.append(ExecutionLogEntry(node=current, before=before, after=after, note=note))

        # branching/looping logic:
        # precedence: explicit next_node from handler > graph.edges mapping
        if next_node:
            current = next_node
        else:
            current = graph.edges.get(current)  # may be None (end)
    run_state.finished = True
    run_state.current_node = None
    return run_state
