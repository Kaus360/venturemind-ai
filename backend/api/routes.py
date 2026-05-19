from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.agents.problem_discovery_agent import ProblemDiscoveryAgent
from backend.agents.solution_generator_agent import SolutionGeneratorAgent
from backend.agents.validation_agent import ValidationAgent
from backend.workflows.orchestration_graph import venture_graph


router = APIRouter()


class GenerateProblemsRequest(BaseModel):
    domain: str


class GenerateSolutionRequest(BaseModel):
    problem_statement: str


class ValidateStartupRequest(BaseModel):
    startup_idea: str


class ExecuteWorkflowRequest(BaseModel):
    domain: str


@router.post("/generate-problems")
async def generate_problems(payload: GenerateProblemsRequest) -> dict[str, Any]:
    agent = ProblemDiscoveryAgent()
    result = await agent.run({"domain": payload.domain})

    problems = result.get("problems", [])
    if isinstance(problems, dict) and "problems" in problems:
        problems = problems["problems"]

    return {
        "problems": problems,
        "error": result.get("error"),
    }


@router.post("/generate-solution")
async def generate_solution(payload: GenerateSolutionRequest) -> dict[str, Any]:
    agent = SolutionGeneratorAgent()
    result = await agent.run({"problem_statement": payload.problem_statement})
    return {
        "solution": result.get("solution", {}),
        "error": result.get("error"),
    }


@router.post("/validate-startup")
async def validate_startup(payload: ValidateStartupRequest) -> dict[str, Any]:
    agent = ValidationAgent()
    result = await agent.run({"startup_idea": payload.startup_idea})
    return {
        "validation": result.get("validation", {}),
        "error": result.get("error"),
    }


@router.post("/execute-workflow")
async def execute_workflow(payload: ExecuteWorkflowRequest) -> dict[str, Any]:
    result = await venture_graph.ainvoke({"domain": payload.domain})
    return dict(result)
