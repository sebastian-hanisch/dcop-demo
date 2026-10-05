"""Orakel-Test: DPOP gegen ein unabhängig aus der README-Formel gebautes Summen-Ziel (Aufzählung, lexikografisch kleinstes
Optimum) und gegen eine eigene Rekursion der UTIL-Tabellen. Ganzzahlige Instanzen erzeugen exakte Gleichstände (Tie-Break)."""

import itertools
import random
from functools import lru_cache

from cn_scenario import Instance, Job, generate_instance
from dcop_dpop import solve_dcop


def _objective(inst, x):
    tau = inst.travel_time_per_unit
    total = 0.0
    for j, a in enumerate(x):
        total += abs(inst.agent_start_positions[a] - inst.jobs[j].position) * tau + inst.jobs[j].duration
    for i in range(inst.n_jobs):
        for j in range(i + 1, inst.n_jobs):
            if x[i] == x[j]:
                total += abs(inst.jobs[i].position - inst.jobs[j].position) * tau
    return total


def _int_instance(rng, n, k):
    jobs = tuple(Job(i, float(rng.randint(0, 6)), float(rng.randint(1, 4))) for i in range(n))
    return Instance(n, k, jobs, tuple(float(rng.randint(0, 6)) for _ in range(k)), 1.0)


def test_dpop_matches_independent_enumeration_and_util_recursion():
    rng = random.Random(1)
    for it in range(60):
        n, k = rng.randint(1, 6), rng.randint(2, 4)
        integral = it % 2 == 0
        inst = _int_instance(rng, n, k) if integral else generate_instance(n, k, 0.5, rng.uniform(0.2, 2.0), rng.randint(0, 999))
        res = solve_dcop(inst)
        best, best_x = None, None
        for x in itertools.product(range(k), repeat=n):
            v = _objective(inst, x)
            if best is None or v < best - 1e-9:
                best, best_x = v, x
        assert abs(res.total_cost - best) < 1e-9
        got = tuple(res.assignment[j] for j in range(n))
        assert abs(_objective(inst, got) - res.total_cost) < 1e-9
        if integral:                       # exakte Gleichstände: lexikografisch kleinste Optimallösung
            assert got == best_x

        tau = inst.travel_time_per_unit

        def local(j, prefix, a):
            c = abs(inst.agent_start_positions[a] - inst.jobs[j].position) * tau + inst.jobs[j].duration
            return c + sum(abs(inst.jobs[i].position - inst.jobs[j].position) * tau for i, ai in enumerate(prefix) if ai == a)

        @lru_cache(None)
        def f(j, prefix):
            if j == n:
                return 0.0
            return min(local(j, prefix, a) + f(j + 1, prefix + (a,)) for a in range(k))

        for j, table in enumerate(res.util_tables):
            assert len(table.entries) == k ** j
            for sep, (cost, _agent) in table.entries.items():
                assert abs(cost - f(j, sep)) < 1e-9
