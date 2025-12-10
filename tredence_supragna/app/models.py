from pydantic import BaseModel
from typing import Dict, List, Optional, Any

class NodeSpec(BaseModel):
    name: str
    func: str                 # name of function / node handler to run
    params: Optional[Dict[str, Any]] = {}

class GraphSpec(BaseModel):
    nodes: List[NodeSpec]
    edges: Dict[str, str]     # simple mapping "from": "to" (single-outgoing)
    start_node: str

class RunRequest(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any] = {}

class ExecutionLogEntry(BaseModel):
    node: str
    before: Dict[str, Any]
    after: Dict[str, Any]
    note: Optional[str] = None

class RunState(BaseModel):
    run_id: str
    graph_id: str
    state: Dict[str, Any]
    current_node: Optional[str] = None
    finished: bool = False
    log: List[ExecutionLogEntry] = []
