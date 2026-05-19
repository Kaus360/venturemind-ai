from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.agents.problem_discovery_agent import ProblemDiscoveryAgent
from backend.agents.solution_generator_agent import SolutionGeneratorAgent
from backend.agents.validation_agent import ValidationAgent


class VentureState(TypedDict, total=False):
    domain: str
    problem_statement: str
    startup_idea: str
    problems: Any
    solution: dict[str, Any]
    validation: dict[str, Any]
    memory_context: Any
    error: str


problem_discovery_agent = ProblemDiscoveryAgent()
solution_generator_agent = SolutionGeneratorAgent()
validation_agent = ValidationAgent()


async def extract_problem(state: VentureState) -> VentureState:
    next_state = dict(state)
    problems = state.get("problems", {})
    if isinstance(problems, dict):
        problem_items = problems.get("problems", [])
        if problem_items and isinstance(problem_items[0], dict):
            title = str(problem_items[0].get("title", "")).strip()
            description = str(problem_items[0].get("description", "")).strip()
            next_state["problem_statement"] = f"{title}: {description}".strip(": ").strip()
    return next_state


async def extract_idea(state: VentureState) -> VentureState:
    next_state = dict(state)
    solution = state.get("solution", {})
    if isinstance(solution, dict):
        next_state["startup_idea"] = str(solution.get("startup_idea", "")).strip()
    return next_state


async def run_problem_discovery(state: VentureState) -> VentureState:
    return await problem_discovery_agent.run(state)


async def run_solution_generator(state: VentureState) -> VentureState:
    return await solution_generator_agent.run(state)


async def run_validation(state: VentureState) -> VentureState:
    return await validation_agent.run(state)


graph = StateGraph(VentureState)
graph.add_node("problem_discovery", run_problem_discovery)
graph.add_node("extract_problem", extract_problem)
graph.add_node("solution_generator", run_solution_generator)
graph.add_node("extract_idea", extract_idea)
graph.add_node("validation_node", run_validation)

graph.add_edge(START, "problem_discovery")
graph.add_edge("problem_discovery", "extract_problem")
graph.add_edge("extract_problem", "solution_generator")
graph.add_edge("solution_generator", "extract_idea")
graph.add_edge("extract_idea", "validation_node")
graph.add_edge("validation_node", END)

venture_graph = graph.compile()
