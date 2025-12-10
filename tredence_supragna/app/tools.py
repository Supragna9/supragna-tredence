# Simple tool registry: functions nodes can call.
from typing import Dict, Any, Callable

TOOLS: Dict[str, Callable] = {}

def register(name: str):
    def _decorator(fn):
        TOOLS[name] = fn
        return fn
    return _decorator

# Example tools for Code Review
@register("detect_smells")
def detect_smells(code: str) -> Dict[str, int]:
    # Extremely simple heuristics
    issues = 0
    if "TODO" in code:
        issues += 1
    if len(code.splitlines()) > 200:
        issues += 1
    if "eval(" in code:
        issues += 2
    return {"issues": issues}

@register("calc_complexity")
def calc_complexity(code: str) -> Dict[str, int]:
    # naive complexity proxy: number of branches/loops
    comps = 0
    for token in ["if ", "for ", "while ", "try:", "except"]:
        comps += code.count(token)
    return {"complexity": comps}
