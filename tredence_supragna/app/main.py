from fastapi import FastAPI, HTTPException
from typing import Dict
import uuid
from .models import GraphSpec, RunRequest
from .enigiine import create_graph, run_graph, GRAPHS, RUNS, get_run, register_node
from .workflows import code_review_graph
from . import tools

app = FastAPI(title="Workflow Engine")

# Register example graph at startup
@app.on_event("startup")
async def startup():
    example_id = "code_review_example"
    create_graph(example_id, code_review_graph())
    print("Registered graph:", example_id)

# API to create a graph (client-supplied JSON)
@app.post("/graph/create")
async def api_create_graph(payload: GraphSpec):
    graph_id = str(uuid.uuid4())
    create_graph(graph_id, payload)
    return {"graph_id": graph_id}

# API to run a graph (synchronous endpoint that triggers async run)
@app.post("/graph/run")
async def api_run_graph(req: RunRequest):
    if req.graph_id not in GRAPHS:
        raise HTTPException(status_code=404, detail="graph not found")
    run_state = await run_graph(req.graph_id, req.initial_state or {})
    # store run by id
    RUNS[run_state.run_id] = run_state
    return {"run_id": run_state.run_id, "final_state": run_state.state, "log": [l.dict() for l in run_state.log]}

# API to get run state
@app.get("/graph/state/{run_id}")
async def api_get_state(run_id: str):
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run.dict()

# ------------------------
# Node implementations (register nodes)
# ------------------------
@register_node("extract_functions")
def extract_functions(state: Dict, params: Dict, tools_registry: Dict):
    # Expect code in state["code"]
    code = state.get("code", "")
    # super simple: treat entire code as single function for demo
    state["functions"] = [{"name": "main", "code": code}]
    return {"state": {"extracted": True}, "note": "extracted 1 function"}

@register_node("check_complexity")
def check_complexity(state: Dict, params: Dict, tools_registry: Dict):
    funcs = state.get("functions", [])
    total = 0
    for f in funcs:
        res = tools_registry["calc_complexity"](f["code"])
        total += res.get("complexity", 0)
    state["complexity_score"] = total
    return {"state": {}, "note": f"complexity {total}"}

@register_node("detect_issues")
def detect_issues(state: Dict, params: Dict, tools_registry: Dict):
    funcs = state.get("functions", [])
    total_issues = 0
    for f in funcs:
        res = tools_registry["detect_smells"](f["code"])
        total_issues += res.get("issues", 0)
    state["issues"] = total_issues
    return {"state": {}, "note": f"issues {total_issues}"}

@register_node("suggest_improvements")
def suggest_improvements(state: Dict, params: Dict, tools_registry: Dict):
    # simple suggestions based on issues / complexity
    suggestions = []
    if state.get("issues", 0) > 0:
        suggestions.append("Fix TODOs and avoid eval()")
    if state.get("complexity_score", 0) > 10:
        suggestions.append("Refactor large functions into smaller ones")
    state["suggestions"] = suggestions
    return {"state": {}, "note": f"{len(suggestions)} suggestions"}

@register_node("evaluate_quality")
def evaluate_quality(state: Dict, params: Dict, tools_registry: Dict):
    # compute a simple quality score
    issues = state.get("issues", 0)
    complexity = state.get("complexity_score", 0)
    quality = max(0, 100 - (issues * 20 + complexity * 2))
    state["quality_score"] = quality
    # Loop logic: if quality below threshold, go back to 'suggest' to simulate refinement
    threshold = params.get("threshold", 80)
    if quality < threshold and state.get("suggestions"):
        return {"state": {}, "next": "suggest", "note": f"quality {quality} < {threshold}, loop to suggest"}
    return {"state": {}, "note": f"quality {quality}, finished"}
