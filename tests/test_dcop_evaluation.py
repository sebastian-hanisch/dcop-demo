import cn_constants as C
from cn_ortools_reference import SCALE
from cn_scenario import generate_instance
from dcop_evaluation import full_comparison

# Siehe test_ortools_reference.py: CP-SAT rundet Zeiten bewusst AUF.
_ROUNDING_TOLERANCE_PER_JOB = 2.0 / SCALE


def test_correctness_gap_always_near_zero():
    for n_jobs in range(2, 8):
        for n_agents in (2, 3, 4):
            instance = generate_instance(n_jobs, n_agents, 0.4, 1.0, n_jobs * 7 + n_agents)
            cmp = full_comparison(instance, time_limit_seconds=5.0)
            assert abs(cmp["correctness_gap"]) < 1e-6, f"n_jobs={n_jobs} n_agents={n_agents}"


def test_makespan_gap_never_negative_beyond_rounding_tolerance():
    for seed in range(15):
        instance = generate_instance(6, 2, 0.4, 1.0, seed)
        cmp = full_comparison(instance, time_limit_seconds=5.0)
        if cmp["makespan_gap"] is None:
            continue
        tolerance = _ROUNDING_TOLERANCE_PER_JOB * instance.n_jobs
        assert cmp["makespan_gap"] >= -tolerance, f"seed={seed}"


def test_dpop_vs_cnp_can_be_positive_and_negative():
    positive_found = False
    negative_found = False
    for seed in range(60):
        instance = generate_instance(6, 3, 0.4, 1.2, seed)
        cmp = full_comparison(instance, time_limit_seconds=5.0)
        if cmp["dpop_vs_cnp"] > 0.5:
            positive_found = True
        if cmp["dpop_vs_cnp"] < -0.5:
            negative_found = True
        if positive_found and negative_found:
            break
    assert positive_found, "no swept seed showed DPOP worse than raw CNP - widen the sweep"
    assert negative_found, "no swept seed showed DPOP better than raw CNP - widen the sweep"


def test_presets_produce_expected_gap_and_makespan_bands():
    for name, params in C.PRESETS.items():
        instance = generate_instance(
            n_jobs=params["n_jobs"], n_agents=params["n_agents"],
            duration_variability=params["duration_variability"],
            travel_time_per_unit=params["travel_time_per_unit"], seed=params["seed"],
        )
        cmp = full_comparison(instance, time_limit_seconds=8.0)
        band = C.PRESET_EXPECTED_BANDS[name]

        assert abs(cmp["correctness_gap"]) < 1e-6, name

        lo, hi = band["makespan_gap_pct"]
        assert lo <= cmp["makespan_gap_pct"] <= hi, f"{name}: makespan_gap_pct={cmp['makespan_gap_pct']}"

        lo, hi = band["dpop_vs_cnp_pct"]
        assert lo <= cmp["dpop_vs_cnp_pct"] <= hi, f"{name}: dpop_vs_cnp_pct={cmp['dpop_vs_cnp_pct']}"
