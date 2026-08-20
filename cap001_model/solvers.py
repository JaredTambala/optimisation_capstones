"""Solver adapters that normalize vendor results into CAP-001 evidence."""

from __future__ import annotations

import math
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping

import pyomo.environ as pyo

from cap001_model.contracts import SolutionStatus, SolverEvidence


def _finite(value: Any) -> float | None:
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _highs_status(termination: str, incumbent: float | None) -> SolutionStatus:
    normalized = termination.lower().replace("_", "")
    if normalized == "optimal":
        return SolutionStatus.GLOBALLY_OPTIMAL
    if "infeasible" in normalized:
        return SolutionStatus.INFEASIBLE
    if "timelimit" in normalized or "maxtime" in normalized:
        return (
            SolutionStatus.FEASIBLE_TIME_LIMITED
            if incumbent is not None
            else SolutionStatus.SOLVER_FAILED
        )
    if incumbent is not None:
        return SolutionStatus.BEST_FOUND
    return SolutionStatus.SOLVER_FAILED


class HighsSolverAdapter:
    """Solve Pyomo MILPs with the licence-accessible HiGHS interface."""

    solver_name = "HiGHS"

    def solve(
        self,
        model: Any,
        *,
        time_limit_seconds: float,
        options: Mapping[str, Any] | None = None,
    ) -> SolverEvidence:
        started = time.perf_counter()
        solver = pyo.SolverFactory("appsi_highs")
        if not solver.available(exception_flag=False):
            return SolverEvidence(
                solver_name=self.solver_name,
                solver_version=None,
                status=SolutionStatus.SOLVER_FAILED,
                raw_termination_condition="unavailable",
                termination_message="Pyomo appsi_highs is not available",
                runtime_seconds=time.perf_counter() - started,
                incumbent_objective=None,
                best_bound=None,
                absolute_gap=None,
                relative_gap=None,
                iteration_or_node_count=None,
            )
        solver.config.time_limit = time_limit_seconds
        # The legacy APPSI interface does not consistently propagate the
        # configuration value to every persistent HiGHS solve. Set the native
        # option as well so bounded authoring runs enforce their declared wall
        # time after model construction.
        solver.options["time_limit"] = time_limit_seconds
        for key, value in (options or {}).items():
            solver.options[key] = value
        try:
            results = solver.solve(model, load_solutions=False)
            termination = str(results.solver.termination_condition)
            lower_bound = _finite(results.problem.lower_bound)
            upper_bound = _finite(results.problem.upper_bound)
            status = _highs_status(termination, upper_bound)
            if status in {
                SolutionStatus.GLOBALLY_OPTIMAL,
                SolutionStatus.FEASIBLE_TIME_LIMITED,
                SolutionStatus.BEST_FOUND,
            }:
                solver.load_vars()
            absolute_gap = None
            relative_gap = None
            if lower_bound is not None and upper_bound is not None:
                absolute_gap = abs(upper_bound - lower_bound)
                relative_gap = absolute_gap / max(1e-10, abs(upper_bound))
            version = solver.version()
            version_text = (
                ".".join(str(part) for part in version)
                if isinstance(version, tuple)
                else str(version)
            )
            return SolverEvidence(
                solver_name=self.solver_name,
                solver_version=version_text,
                status=status,
                raw_termination_condition=termination,
                termination_message=str(results.solver.message),
                runtime_seconds=time.perf_counter() - started,
                incumbent_objective=upper_bound,
                best_bound=lower_bound,
                absolute_gap=absolute_gap,
                relative_gap=relative_gap,
                iteration_or_node_count=None,
            )
        except Exception as exc:  # failures become controlled evidence
            return SolverEvidence(
                solver_name=self.solver_name,
                solver_version=None,
                status=SolutionStatus.SOLVER_FAILED,
                raw_termination_condition=type(exc).__name__,
                termination_message=str(exc),
                runtime_seconds=time.perf_counter() - started,
                incumbent_objective=None,
                best_bound=None,
                absolute_gap=None,
                relative_gap=None,
                iteration_or_node_count=None,
            )


def find_ipopt_executable() -> Path | None:
    """Find a working IPOPT executable without trusting a stale shell shim."""

    candidates: list[Path] = []
    configured = os.environ.get("CAP001_IPOPT_EXECUTABLE")
    if configured:
        candidates.append(Path(configured))
    discovered = shutil.which("ipopt")
    if discovered:
        candidates.append(Path(discovered))
    candidates.extend(Path.home().glob(".pyenv/versions/*/envs/*/bin/ipopt"))
    for candidate in candidates:
        try:
            completed = subprocess.run(
                [str(candidate), "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if completed.returncode == 0 and "Ipopt" in completed.stdout:
            return candidate.resolve()
    return None


class IpoptSolverAdapter:
    """Solve continuous nonlinear subproblems and report local status only."""

    solver_name = "IPOPT"

    def __init__(self, executable: Path | None = None):
        self.executable = executable or find_ipopt_executable()

    def solve(
        self,
        model: Any,
        *,
        time_limit_seconds: float,
        options: Mapping[str, Any] | None = None,
    ) -> SolverEvidence:
        started = time.perf_counter()
        if self.executable is None:
            return SolverEvidence(
                solver_name=self.solver_name,
                solver_version=None,
                status=SolutionStatus.SOLVER_FAILED,
                raw_termination_condition="unavailable",
                termination_message="No working IPOPT executable was found",
                runtime_seconds=time.perf_counter() - started,
                incumbent_objective=None,
                best_bound=None,
                absolute_gap=None,
                relative_gap=None,
                iteration_or_node_count=None,
            )
        solver = pyo.SolverFactory("ipopt", executable=str(self.executable))
        solver.options["max_cpu_time"] = time_limit_seconds
        for key, value in (options or {}).items():
            solver.options[key] = value
        try:
            results = solver.solve(model, load_solutions=True)
            termination = str(results.solver.termination_condition)
            normalized = termination.lower().replace("_", "")
            active_objectives = list(
                model.component_data_objects(pyo.Objective, active=True)
            )
            incumbent = (
                float(pyo.value(active_objectives[0].expr))
                if active_objectives and "infeasible" not in normalized
                else None
            )
            if normalized == "optimal":
                status = SolutionStatus.LOCALLY_OPTIMAL
            elif "infeasible" in normalized:
                status = SolutionStatus.INFEASIBLE
            elif "timelimit" in normalized or "maxtime" in normalized:
                status = (
                    SolutionStatus.FEASIBLE_TIME_LIMITED
                    if incumbent is not None
                    else SolutionStatus.SOLVER_FAILED
                )
            else:
                status = SolutionStatus.SOLVER_FAILED
                incumbent = None
            return SolverEvidence(
                solver_name=self.solver_name,
                solver_version=None,
                status=status,
                raw_termination_condition=termination,
                termination_message=str(results.solver.message),
                runtime_seconds=time.perf_counter() - started,
                incumbent_objective=incumbent,
                best_bound=None,
                absolute_gap=None,
                relative_gap=None,
                iteration_or_node_count=None,
            )
        except Exception as exc:
            return SolverEvidence(
                solver_name=self.solver_name,
                solver_version=None,
                status=SolutionStatus.SOLVER_FAILED,
                raw_termination_condition=type(exc).__name__,
                termination_message=str(exc),
                runtime_seconds=time.perf_counter() - started,
                incumbent_objective=None,
                best_bound=None,
                absolute_gap=None,
                relative_gap=None,
                iteration_or_node_count=None,
            )


class MindtPySolverAdapter:
    """Run non-convex MINLP search with HiGHS and IPOPT subproblems."""

    solver_name = "Pyomo MindtPy OA (HiGHS/IPOPT)"

    def __init__(self, ipopt_executable: Path | None = None):
        self.ipopt_executable = ipopt_executable or find_ipopt_executable()

    def solve(
        self,
        model: Any,
        *,
        time_limit_seconds: float,
        options: Mapping[str, Any] | None = None,
    ) -> SolverEvidence:
        started = time.perf_counter()
        if self.ipopt_executable is None:
            return SolverEvidence(
                solver_name=self.solver_name,
                solver_version=None,
                status=SolutionStatus.SOLVER_FAILED,
                raw_termination_condition="unavailable",
                termination_message="No working IPOPT executable was found",
                runtime_seconds=time.perf_counter() - started,
                incumbent_objective=None,
                best_bound=None,
                absolute_gap=None,
                relative_gap=None,
                iteration_or_node_count=None,
            )

        highs = pyo.SolverFactory("appsi_highs")
        mindtpy = pyo.SolverFactory("mindtpy")
        if not highs.available(exception_flag=False) or not mindtpy.available(
            exception_flag=False
        ):
            return SolverEvidence(
                solver_name=self.solver_name,
                solver_version=None,
                status=SolutionStatus.SOLVER_FAILED,
                raw_termination_condition="unavailable",
                termination_message="Pyomo MindtPy or appsi_highs is not available",
                runtime_seconds=time.perf_counter() - started,
                incumbent_objective=None,
                best_bound=None,
                absolute_gap=None,
                relative_gap=None,
                iteration_or_node_count=None,
            )

        solve_options = {
            "mip_solver": "appsi_highs",
            "nlp_solver": "ipopt",
            "strategy": "OA",
            "init_strategy": "rNLP",
            "time_limit": time_limit_seconds,
            "tee": False,
        }
        solve_options.update(options or {})
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = (
            str(self.ipopt_executable.parent) + os.pathsep + original_path
        )
        try:
            results = mindtpy.solve(model, **solve_options)
            termination = str(results.solver.termination_condition)
            normalized = termination.lower().replace("_", "")
            active_objectives = list(
                model.component_data_objects(pyo.Objective, active=True)
            )
            incumbent = None
            if active_objectives:
                incumbent = _finite(
                    pyo.value(active_objectives[0].expr, exception=False)
                )
            if normalized == "optimal":
                # OA convergence over non-convex equalities is not a global
                # certificate. Preserve the raw label and make the weaker
                # normalized claim explicit.
                status = SolutionStatus.LOCALLY_OPTIMAL
            elif "infeasible" in normalized:
                status = SolutionStatus.INFEASIBLE
                incumbent = None
            elif "timelimit" in normalized or "maxtime" in normalized:
                status = (
                    SolutionStatus.FEASIBLE_TIME_LIMITED
                    if incumbent is not None
                    else SolutionStatus.SOLVER_FAILED
                )
            elif "feasible" in normalized and incumbent is not None:
                status = SolutionStatus.BEST_FOUND
            else:
                status = SolutionStatus.SOLVER_FAILED
                incumbent = None
            iterations = _finite(getattr(results.solver, "iterations", None))
            return SolverEvidence(
                solver_name=self.solver_name,
                solver_version=None,
                status=status,
                raw_termination_condition=termination,
                termination_message=str(results.solver.message),
                runtime_seconds=time.perf_counter() - started,
                incumbent_objective=incumbent,
                # MindtPy may report OA master bounds, but they are not valid
                # global bounds for this non-convex formulation.
                best_bound=None,
                absolute_gap=None,
                relative_gap=None,
                iteration_or_node_count=(
                    int(iterations) if iterations is not None else None
                ),
            )
        except Exception as exc:
            return SolverEvidence(
                solver_name=self.solver_name,
                solver_version=None,
                status=SolutionStatus.SOLVER_FAILED,
                raw_termination_condition=type(exc).__name__,
                termination_message=str(exc),
                runtime_seconds=time.perf_counter() - started,
                incumbent_objective=None,
                best_bound=None,
                absolute_gap=None,
                relative_gap=None,
                iteration_or_node_count=None,
            )
        finally:
            os.environ["PATH"] = original_path
