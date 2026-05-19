from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.agents.competitor_agent import CompetitorAgent
from backend.agents.problem_discovery_agent import ProblemDiscoveryAgent
from backend.agents.redteam_agent import RedTeamAgent
from backend.agents.roadmap_agent import RoadmapAgent
from backend.agents.solution_generator_agent import SolutionGeneratorAgent
from backend.agents.validation_agent import ValidationAgent
from backend.chains.memory_chain import memory_chain
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


class AnalyzeCompetitorsRequest(BaseModel):
    startup_idea: str


class RedteamCritiqueRequest(BaseModel):
    startup_idea: str
    validation: dict[str, Any]


class GenerateRoadmapRequest(BaseModel):
    startup_idea: str
    solution: dict[str, Any]
    validation: dict[str, Any]


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
    memory_chain.add_entry(result)
    return dict(result)


@router.get("/memory-context")
async def get_memory_context() -> list[dict[str, Any]]:
    return memory_chain.get_context()


@router.post("/analyze-competitors")
async def analyze_competitors(payload: AnalyzeCompetitorsRequest) -> dict[str, Any]:
    agent = CompetitorAgent()
    result = await agent.run({"startup_idea": payload.startup_idea})
    return {
        "competitor_data": result.get("competitor_data", {}),
        "error": result.get("error"),
    }


@router.post("/redteam-critique")
async def redteam_critique(payload: RedteamCritiqueRequest) -> dict[str, Any]:
    agent = RedTeamAgent()
    result = await agent.run(
        {
            "startup_idea": payload.startup_idea,
            "validation": payload.validation,
        }
    )
    return {
        "critic_feedback": result.get("critic_feedback", {}),
        "error": result.get("error"),
    }


@router.post("/generate-roadmap")
async def generate_roadmap(payload: GenerateRoadmapRequest) -> dict[str, Any]:
    agent = RoadmapAgent()
    result = await agent.run(
        {
            "startup_idea": payload.startup_idea,
            "solution": payload.solution,
            "validation": payload.validation,
        }
    )
    return {
        "roadmap": result.get("roadmap", {}),
        "error": result.get("error"),
    }
