"""Stable formulation, status and solver-evidence contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Protocol, runtime_checkable


class FormulationClass(StrEnum):
    MILP = "MILP"
    MINLP = "MINLP"


class MethodClassification(StrEnum):
    EXACT = "EXACT"
    RELAXED = "RELAXED"
    APPROXIMATE = "APPROXIMATE"
    HEURISTIC = "HEURISTIC"


class SolutionStatus(StrEnum):
    GLOBALLY_OPTIMAL = "globally_optimal"
    LOCALLY_OPTIMAL = "locally_optimal"
    FEASIBLE_TIME_LIMITED = "feasible_time_limited"
    BEST_FOUND = "best_found"
    INFEASIBLE = "infeasible"
    SOLVER_FAILED = "solver_failed"


@dataclass(frozen=True)
class SolverEvidence:
    solver_name: str
    solver_version: str | None
    status: SolutionStatus
    raw_termination_condition: str
    termination_message: str
    runtime_seconds: float
    incumbent_objective: float | None
    best_bound: float | None
    absolute_gap: float | None
    relative_gap: float | None
    iteration_or_node_count: int | None

    @property
    def has_solution(self) -> bool:
        return self.status in {
            SolutionStatus.GLOBALLY_OPTIMAL,
            SolutionStatus.LOCALLY_OPTIMAL,
            SolutionStatus.FEASIBLE_TIME_LIMITED,
            SolutionStatus.BEST_FOUND,
        }


@dataclass(frozen=True)
class ObjectiveStageResult:
    stage: int
    name: str
    objective_value: float
    lock_tolerance: float
    evidence: SolverEvidence


@runtime_checkable
class SolverAdapter(Protocol):
    """Solve a constructed algebraic model and return normalized evidence."""

    def solve(
        self,
        model: Any,
        *,
        time_limit_seconds: float,
        options: Mapping[str, Any] | None = None,
    ) -> SolverEvidence: ...
