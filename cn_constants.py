"""Defaults, Slider-Grenzen und Presets für die DCOP/DPOP-Demo.
Szenario-Konstanten (Zeilen bis ORTOOLS_TIME_LIMIT_SECONDS) sind größtenteils
wortgleich aus contract-net-demo übernommen - dasselbe Vehikel, siehe project
memory - bis auf N_JOBS_MAX, das hier bewusst enger ist (siehe unten)."""

DEFAULT_N_JOBS = 5
DEFAULT_N_AGENTS = 3
DEFAULT_DURATION_VARIABILITY = 0.3
DEFAULT_TRAVEL_TIME_PER_UNIT = 1.0
DEFAULT_SEED = 7

# N_JOBS_MAX bewusst 8 statt des Root-Werts 16: DPOPs UTIL-Tabellengröße wächst
# als n_agents**job_index (vollständiger Constraint-Graph, siehe cn_dpop.py) -
# bei n_agents=4 wäre 4**15 ≈ 1.07 Mrd. Tabelleneinträge am oberen Ende
# unrealistisch. Bei N_JOBS_MAX=8 bleibt der Worst Case 4**7=16384 - spürbar,
# aber interaktiv, und zeigt das Wachstum über 5 Größenordnungen hinweg.
N_JOBS_MIN, N_JOBS_MAX = 3, 8
N_AGENTS_MIN, N_AGENTS_MAX = 2, 4
DURATION_VARIABILITY_MIN, DURATION_VARIABILITY_MAX = 0.0, 1.0
TRAVEL_TIME_PER_UNIT_MIN, TRAVEL_TIME_PER_UNIT_MAX = 0.2, 2.0

POSITION_RANGE_MAX = 20.0
DURATION_BASE_RANGE = (5, 15)
SPIKE_PROBABILITY_SCALE = 0.4
SPIKE_MULTIPLIER = 4.0

# OR-Tools-Referenzlauf: harte Zeitgrenze, damit ein Preset niemals hängt.
ORTOOLS_TIME_LIMIT_SECONDS = 10.0

# Ab welcher Makespan-Lücke (DPOP-Makespan vs. CP-SAT-echtes-Optimum) die
# Kernaussage-Sektion die Modellierungslücke ("DPOP löst das falsche Ziel
# exakt") als Hauptaussage zeigt - höchste Priorität in der Verdict-Kaskade.
MAKESPAN_GAP_WARNING_THRESHOLD_PCT = 40.0

# Ab welcher relativen Abweichung (in beide Richtungen) "DPOP vs. rohes CNP"
# als eigenständig bemerkenswert gilt (zweite Kaskaden-Stufe: DPOP kann
# schlechter ODER besser als das naive CNP-Ergebnis sein).
DPOP_VS_CNP_NOTABLE_PCT = 5.0

# Seeds empirisch kalibriert via calibrate_presets.py (seither gelöscht) - nicht
# der erste Versuch übernommen. Siehe README.md für die gemessenen Werte.
PRESETS = {
    "Surrogat trifft fast genau": {
        "n_jobs": 5, "n_agents": 3, "duration_variability": 0.0,
        "travel_time_per_unit": 1.5, "seed": 13,
    },
    "Surrogat hilft deutlich": {
        "n_jobs": 6, "n_agents": 2, "duration_variability": 0.0,
        "travel_time_per_unit": 2.0, "seed": 13,
    },
    "Surrogat schadet leicht": {
        "n_jobs": 4, "n_agents": 2, "duration_variability": 0.0,
        "travel_time_per_unit": 1.0, "seed": 6,
    },
    "Surrogat-Lücke eklatant": {
        "n_jobs": 6, "n_agents": 4, "duration_variability": 0.0,
        "travel_time_per_unit": 1.0, "seed": 24,
    },
    "Tabellen-Explosion": {
        "n_jobs": 8, "n_agents": 4, "duration_variability": 0.4,
        "travel_time_per_unit": 1.0, "seed": 6,
    },
}

PRESET_HELP = {
    "Surrogat trifft fast genau": "DPOPs Summen-Surrogat trifft hier fast genau "
        "den echten Makespan - und schlägt auch das rohe Contract-Net-Ergebnis.",
    "Surrogat hilft deutlich": "Das Surrogat senkt den Makespan fast auf die "
        "Hälfte des rohen CNP-Ergebnisses, mit kleiner Restlücke zum echten Optimum.",
    "Surrogat schadet leicht": "Exakt für das eigene (Summen-)Ziel heißt nicht "
        "'hilft der echten Kennzahl' - hier schneidet DPOP leicht schlechter ab "
        "als das naive Contract Net.",
    "Surrogat-Lücke eklatant": "Die Kernaussage: DPOP löst sein eigenes Modell "
        "exakt und verfehlt den echten Makespan trotzdem um mehr als das Doppelte.",
    "Tabellen-Explosion": "Regler-Maximum: die letzte UTIL-Tabelle hat 16384 "
        "Einträge - und der Makespan liegt trotzdem weit vom Optimum entfernt.",
}

# Regressions-Bänder für tests/test_dcop_evaluation.py::
# test_presets_produce_expected_gap_and_makespan_bands.
PRESET_EXPECTED_BANDS = {
    "Surrogat trifft fast genau": {
        "makespan_gap_pct": (-5.0, 15.0), "dpop_vs_cnp_pct": (-25.0, -2.0),
    },
    "Surrogat hilft deutlich": {
        "makespan_gap_pct": (0.0, 20.0), "dpop_vs_cnp_pct": (-60.0, -25.0),
    },
    "Surrogat schadet leicht": {
        "makespan_gap_pct": (2.0, 25.0), "dpop_vs_cnp_pct": (2.0, 25.0),
    },
    "Surrogat-Lücke eklatant": {
        "makespan_gap_pct": (80.0, 170.0), "dpop_vs_cnp_pct": (50.0, 120.0),
    },
    "Tabellen-Explosion": {
        "makespan_gap_pct": (70.0, 160.0), "dpop_vs_cnp_pct": (40.0, 100.0),
    },
}
