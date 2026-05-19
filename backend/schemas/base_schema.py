from __future__ import annotations

from pydantic import BaseModel


class ProblemItem(BaseModel):
    title: str
    description: str
    impact_score: float
    feasibility_score: float
    target_audience: str


class ProblemDiscoveryResponse(BaseModel):
    problems: list[ProblemItem]


class SolutionResponse(BaseModel):
    startup_idea: str
    value_proposition: str
    key_features: list[str]
    target_audience: str
    innovation_summary: str


class ValidationResponse(BaseModel):
    innovation_score: float
    market_demand: float
    competition_risk: float
    feasibility: float
    summary: str
    weaknesses: list[str]
