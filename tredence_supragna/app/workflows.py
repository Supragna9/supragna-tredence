# Build a sample Code Review workflow (Option A)
from .models import GraphSpec, NodeSpec

def code_review_graph():
    nodes = [
        NodeSpec(name="extract", func="extract_functions"),
        NodeSpec(name="complexity", func="check_complexity"),
        NodeSpec(name="detect", func="detect_issues"),
        NodeSpec(name="suggest", func="suggest_improvements"),
        NodeSpec(name="evaluate", func="evaluate_quality")
    ]
    # edges define default flow
    edges = {
        "extract": "complexity",
        "complexity": "detect",
        "detect": "suggest",
        "suggest": "evaluate",
        # evaluate will either loop back to 'suggest' or end
    }
    return GraphSpec(nodes=nodes, edges=edges, start_node="extract")
