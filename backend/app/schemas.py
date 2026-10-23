"""Strict JSON contracts between the LLM, the API and the React frontend."""
from typing import Literal
from pydantic import BaseModel, Field

Level = Literal["low", "medium", "high", "critical"]


class Violation(BaseModel):
    issue: str
    severity: Level
    location: str = ""
    recommendation: str


class SafetyReport(BaseModel):
    safety_score: int = Field(ge=0, le=100)
    overall_risk: Level
    summary: str
    ppe_summary: str
    violations: list[Violation]


class CrackReport(BaseModel):
    crack_detected: bool
    crack_type: str
    severity: Level
    estimated_width_mm: float | None = None
    confidence: float = Field(ge=0, le=1)
    probable_causes: list[str]
    recommended_actions: list[str]
    urgency: str
    disclaimer: str


class Factor(BaseModel):
    factor: str
    impact: Literal["positive", "neutral", "negative"]
    note: str = ""


class ValuationReport(BaseModel):
    currency: str
    estimated_value_low: float
    estimated_value_high: float
    price_per_sqft: float
    market_outlook: str
    factors: list[Factor]
    assumptions: list[str]
    confidence: float = Field(ge=0, le=1)


class Phase(BaseModel):
    name: str
    duration_days: int
    tasks: list[str]
    materials: list[str]
    risks: list[str]


class PlanReport(BaseModel):
    total_duration_days: int
    estimated_cost_range: str
    phases: list[Phase]
    critical_path: list[str]
    resource_needs: list[str]
    recommendations: list[str]


class AssistantReport(BaseModel):
    answer: str
    priority: Level
    action_items: list[str]
    follow_up_questions: list[str]


class WeatherAdvisory(BaseModel):
    work_suitability: Literal["good", "caution", "halt"]
    summary: str
    recommended_activities: list[str]
    avoid_activities: list[str]
    precautions: list[str]


class KnowledgeReport(BaseModel):
    answer: str
    key_points: list[str]
    standards_referenced: list[str]
    related_topics: list[str]
