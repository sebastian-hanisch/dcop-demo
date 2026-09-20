# Distributed Constraint Optimization (DCOP), gelöst mit DPOP, an der Kran-Auftragsvergabe – Streamlit-Demo

Drittes Stück der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations
Research und Machine Learning", **Multi-Agenten-Koordinations-Linie** - ein
**unabhängiger Zweig** direkt vom [contract-net-demo](../contract-net-demo)-Root,
keine Fortsetzung von [task-swap-demo](../task-swap-demo) (mirrort das Muster
gmm-demo/spectral-demo als unabhängige Zweige ab kmeans-demo).

## Was dieses Stück von beiden Vorgängern unterscheidet

- **contract-net-demo**: Unwiderruflichkeit - nie Revision nach Zuschlag.
- **task-swap-demo**: selbst mit voller Information kann eine auf paarweise
  Tausche beschränkte lokale Suche im lokalen Optimum steckenbleiben.
- **dcop-demo**: **DCOP** ist die Problemklasse (Variablen, Domänen, Summe
  lokaler Kosten), **DPOP** (Distributed Pseudotree Optimization Procedure,
  Petcu & Faltings 2005) ein **exakter** Löser dafür - beweisbar optimal über
  verteilte dynamische Programmierung auf einem Pseudo-Baum, kein
  Steckenbleiben möglich. Und verfehlt den echten Makespan trotzdem oft, aus
  einem völlig anderen Grund: ein DCOP minimiert eine SUMME von Unär- und
  Paarkosten, der echte Makespan (Maximum über Agenten, je eine
  reihenfolgeabhängige Summe über alle ihre Aufträge) lässt sich so nicht
  ausdrücken - also modelliert das DCOP ein bewusst gewähltes Summen-Surrogat,
  das DPOP exakt löst, das aber nicht dasselbe Ziel wie der echte Makespan
  ist. Eine **Modellierungslücke** (Modell, nicht Löser), orthogonal zu beiden
  Vorgänger-Schwächen (DPOP hat volle Information UND durchsucht erschöpfend -
  trotzdem kann es schlechter als das naive, myopische Contract-Net-Ergebnis
  abschneiden).
  Empirisch schlägt DPOP das rohe CNP-Ergebnis nur auf einem Teil der
  Instanzen und verliert auf einem anderen - kein Randfall, aber je nach
  Einstellung sehr unterschiedlich: auf 30 festen Held-out-Instanzen (n=8…12,
  k=3…4) liegen die Gewinne bei etwa 27–50 %, die Verluste bei etwa 47–70 %,
  im Mittel ist der Fahrzeug-DPOP 5–19 % schlechter als Contract Net (gemessen
  in ladcop-demo). Siehe
  `tests/test_dcop_evaluation.py::test_dpop_vs_cnp_can_be_positive_and_negative`
  für die Regression, dass beide Richtungen vorkommen.

## Die DCOP-Formulierung

Eine Variable pro AUFTRAG (nicht pro Agent): `x_j ∈ {0,...,n_agents-1}`.
Reihenfolge innerhalb eines Agenten wird nicht modelliert (wie bei
task-swap-demo: Eigentümerschaft getrennt von Reihenfolge) - echte
Makespan-Berechnung über das unveränderte `cn_schedule.schedule_from_assignment`.

- **Unärkosten**: `unary(j,a) = travel_time(agent_a_start, job_j.position) + job_j.duration`.
- **Paarkosten** (jedes Auftragspaar): `0` bei verschiedenen Agenten, sonst
  die (reihenfolge-unabhängige) Distanz zwischen den beiden Aufträgen.
- **DCOP-Ziel**: `Σ unary + Σ_{i<j} pairwise` über einen
  VOLLSTÄNDIGEN Constraint-Graphen - absichtlich, das lässt DPOPs eigene
  Schwäche (Tabellengröße) sofort und drastisch sichtbar werden.

**Der Pseudo-Baum entartet zu einer Kette**: eine Tiefensuche auf einem
vollständigen Graphen hat nie einen Grund zurückzuspringen. Auftrag `j`s
Separator ist immer `{0,...,j-1}`, Tabellengröße `n_agents^j` - bei
`n_agents=4, n_jobs=8` erreicht die letzte Tabelle 16.384 Einträge.

**Zwei getrennte Vergleiche**, nie vermischt:
1. *Löst DPOP das DCOP richtig?* (Frage an den Löser) - gegen Brute-Force über
   dasselbe Summen-Ziel (`correctness_gap`, sollte immer ≈0 sein).
2. *Ist das DCOP-Ziel dasselbe wie der echte Makespan?* (Frage ans Modell) - DPOPs
   Zuteilung wird in einen echten Zeitplan übersetzt und gegen CP-SATs
   echtes Optimum UND das rohe CNP-Ergebnis verglichen (`makespan_gap`,
   `dpop_vs_cnp`) - die eigentliche, oft erhebliche Lücke.

## Referenzlöser

- **`cn_ortools_reference.py`**: echter Google-OR-Tools-CP-SAT-Solver,
  wortgleich aus contract-net-demo übernommen - das echte Makespan-Optimum.
- **`dcop_bruteforce.py`**: vollständige Enumeration über DPOPs EIGENES
  Summen-Ziel (nicht den Makespan) - der Korrektheits-Check für die
  DPOP-Implementierung selbst.
- **`cn_bruteforce.py`**: wortgleich aus task-swap-demo, nur für den
  CP-SAT-Cross-Check in `tests/test_ortools_reference.py` gebraucht.

## Verifikation

- **Handgerechnetes Beispiel**: ein 3-Auftrags/2-Agenten-Beispiel mit einem
  echten Unentschieden in einer UTIL-Tabelle, von Hand hergeleitet und
  gegen die Implementierung verifiziert (`tests/test_dcop_dpop.py::
  test_hand_computed_util_tables_and_assignment`).
- **DPOP == Brute-Force** auf demselben Summen-Ziel über einen breiten
  Seed-Sweep - Kosten UND Zuteilung müssen übereinstimmen, nicht nur der Wert.
- **Tabellengröße wächst wie vorhergesagt** (`n_agents^job_index`) - explizit getestet.
- **Determinismus**: zweimal lösen liefert identisches Ergebnis.
- **`dpop_vs_cnp` kommt nachweislich in beide Richtungen vor** - eine echte
  Regression, keine bloße Behauptung.
- **Preset-Kalibrierung**: `test_presets_produce_expected_gap_and_makespan_bands`
  hält die gemessenen Bänder aller 5 Presets fest.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Hauptablauf: Presets, Einstellungen, CNP-Rekap, UTIL-/VALUE-Animationen, Zwei-Fragen-Vergleich |
| `cn_constants.py` | Defaults, Regler-Grenzen (N_JOBS_MAX bewusst 8, nicht 16), `PRESETS` |
| `cn_presets.py` | `SettingSpec`/Permalink-Logik (unverändert aus contract-net-demo) |
| `cn_scenario.py`, `cn_bidding.py`, `cn_protocol.py` | Vehikel + CNP (unverändert aus contract-net-demo) |
| `cn_ortools_reference.py` | Echter Google-OR-Tools-CP-SAT-Solver (zentrale Referenz) |
| `cn_bruteforce.py` | CNP-Bruteforce-Cross-Check (unverändert aus task-swap-demo) |
| `cn_schedule.py` | Zuteilung → Fertigstellungszeiten/Makespan (unverändert aus task-swap-demo) |
| `cn_evaluation.py`, `cn_visualization.py` | CNP-Rekap-Kennzahlen und -Charts (unverändert aus contract-net-demo) |
| `dcop_graph.py` | Die DCOP-Formulierung: Unär-/Paarkosten, Zielfunktion |
| `dcop_dpop.py` | `solve_dcop` - UTIL-/VALUE-Phasen über die Ketten-Struktur |
| `dcop_bruteforce.py` | Erschöpfende Referenz für DPOPs eigenes Summen-Ziel |
| `dcop_evaluation.py` | `full_comparison` - beide getrennten Vergleiche |
| `dcop_visualization.py` | DCOP-Gantt, UTIL-Tabellen-Balken, Tabellengrößen-Wachstumschart |
| `tests/` | Handgerechnetes Beispiel, Bruteforce-Cross-Checks, Tabellengrößen-, Determinismus- und Richtungs-Tests |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
