"""Zwei getrennte, beide wichtige Vergleiche:

1. Rechnet DPOP sein eigenes (Summen-)Ziel richtig? -> gegen Brute-Force über
   dasselbe Ziel (`correctness_gap`, sollte immer ~0 sein - ein Fehlschlag
   wäre ein echter Implementierungsfehler, keine Modellierungs-Aussage).
2. Ist DPOPs eigenes Ziel dasselbe wie der echte Makespan? -> DPOPs Zuteilung
   wird über `schedule_from_assignment` (aufsteigend nach Auftrags-Index,
   exakt wie bei Contract Net/Task-Swap-Verhandlung) in einen echten Zeitplan
   übersetzt und gegen das zentrale CP-SAT-Optimum UND das rohe Contract-Net-
   Ergebnis verglichen (`makespan_gap`, `dpop_vs_cnp`) - das ist die
   eigentliche, oft erhebliche Lücke, und sie kann in BEIDE Richtungen
   ausschlagen (DPOP kann besser ODER schlechter als das naive CNP sein)."""

from cn_ortools_reference import solve_with_ortools
from cn_protocol import run_protocol
from cn_schedule import schedule_from_assignment
from dcop_bruteforce import solve_bruteforce_dcop
from dcop_dpop import solve_dcop


def _schedules_from_assignment(instance, assignment):
    schedules = {a: [] for a in range(instance.n_agents)}
    for job_index in sorted(assignment):
        schedules[assignment[job_index]].append(job_index)
    return {a: tuple(jobs) for a, jobs in schedules.items()}


def full_comparison(instance, time_limit_seconds=10.0):
    dpop = solve_dcop(instance)
    bruteforce_cost, _bruteforce_assignment = solve_bruteforce_dcop(instance)
    correctness_gap = dpop.total_cost - bruteforce_cost

    cnp_result = run_protocol(instance)
    cnp_makespan = cnp_result.makespan

    dpop_schedules = _schedules_from_assignment(instance, dpop.assignment)
    _dpop_finish_times, dpop_makespan = schedule_from_assignment(instance, dpop_schedules)

    ortools_result = solve_with_ortools(instance, time_limit_seconds=time_limit_seconds)
    ortools_makespan = ortools_result.makespan if ortools_result.feasible else None

    makespan_gap = None
    makespan_gap_pct = None
    if ortools_makespan is not None and ortools_makespan > 0:
        makespan_gap = dpop_makespan - ortools_makespan
        makespan_gap_pct = makespan_gap / ortools_makespan * 100.0

    dpop_vs_cnp = dpop_makespan - cnp_makespan
    dpop_vs_cnp_pct = (dpop_vs_cnp / cnp_makespan * 100.0) if cnp_makespan > 0 else None

    return {
        "dpop_assignment": dpop.assignment,
        "dpop_schedules": dpop_schedules,
        "util_tables": dpop.util_tables,
        "util_table_sizes": tuple(len(t.entries) for t in dpop.util_tables),

        "dpop_total_cost": dpop.total_cost,
        "bruteforce_cost": bruteforce_cost,
        "correctness_gap": correctness_gap,

        "cnp_makespan": cnp_makespan,
        "dpop_makespan": dpop_makespan,

        "ortools_makespan": ortools_makespan,
        "ortools_feasible": ortools_result.feasible,
        "ortools_optimal": ortools_result.optimal,
        "ortools_wall_time": ortools_result.wall_time_ms / 1000.0,

        "makespan_gap": makespan_gap,
        "makespan_gap_pct": makespan_gap_pct,
        "dpop_vs_cnp": dpop_vs_cnp,
        "dpop_vs_cnp_pct": dpop_vs_cnp_pct,
    }
