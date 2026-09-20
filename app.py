"""
Distributed Constraint Optimization (DCOP), gelöst mit DPOP, an der
Kran-Auftragsvergabe – interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Drittes Stück der "Konzepte"-Reihe, Multi-Agenten-Koordinations-Linie - ein
UNABHÄNGIGER Zweig direkt vom Contract-Net-Protocol-Root (contract-net-demo),
keine Fortsetzung von task-swap-demo. DCOP ist die Problemklasse, DPOP ein
EXAKTER Löser dafür (verteilte dynamische Programmierung). DPOP löst das hier
modellierte DCOP beweisbar optimal - und verfehlt den echten Makespan trotzdem
oft, weil das DCOP-Modell nur ein Summen-Surrogat für den echten Makespan ist.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import cn_constants as C
from cn_evaluation import stats_up_to_step
from cn_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from cn_protocol import run_protocol
from cn_scenario import generate_instance
from cn_visualization import build_bid_chart, build_schedule_figure
from dcop_dpop import solve_dcop, util_table_size
from dcop_evaluation import full_comparison
from dcop_visualization import (
    build_dcop_schedule_figure,
    build_util_step_bar,
    build_util_table_size_chart,
    describe_value_step,
)

st.set_page_config(page_title="DCOP (DPOP) – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _compute_cnp(n_jobs, n_agents, duration_variability, travel_time_per_unit, seed):
    instance = generate_instance(n_jobs, n_agents, duration_variability, travel_time_per_unit, seed)
    result = run_protocol(instance)
    return instance, result


@st.cache_data(show_spinner=False)
def _compute_dpop(n_jobs, n_agents, duration_variability, travel_time_per_unit, seed):
    instance = generate_instance(n_jobs, n_agents, duration_variability, travel_time_per_unit, seed)
    return solve_dcop(instance)


@st.cache_data(show_spinner=False)
def _compute_comparison(n_jobs, n_agents, duration_variability, travel_time_per_unit, seed):
    instance = generate_instance(n_jobs, n_agents, duration_variability, travel_time_per_unit, seed)
    return full_comparison(instance, time_limit_seconds=C.ORTOOLS_TIME_LIMIT_SECONDS)


st.title("🧩 Distributed Constraint Optimization (DCOP) an der Kran-Auftragsvergabe")
st.markdown(
    """
Ein **unabhängiger Zweig** direkt vom Contract-Net-Protocol-Root
(**contract-net-demo**), keine Fortsetzung von task-swap-demo. **DCOP** ist
die *Problemklasse* (Variablen, Domänen, Kostenfunktionen, verteilt auf
Agenten), **DPOP** (Distributed Pseudotree Optimization Procedure) ein
*Löser* dafür: verteilte dynamische Programmierung, **beweisbar exakt** -
anders als die Task-Swap-Verhandlung kann DPOP nie im lokalen Optimum
steckenbleiben. Und verfehlt den echten Makespan trotzdem oft, aus einem
völlig anderen Grund: das hier modellierte DCOP ist nur ein Surrogat für das,
was wir eigentlich wollen.
"""
)
st.caption(
    "Contract Net (online, keine Rücksicht auf spätere Aufträge) und "
    "Task-Swap-Verhandlung (offline, aber nur lokale Suche) hatten je eine "
    "klare eigene Schwäche. DPOP hat WEDER von beidem - volle Information UND "
    "erschöpfende Suche über das DCOP - und kann trotzdem "
    "schlechter abschneiden als das naive Contract-Net-Ergebnis."
)

with st.expander("Wie funktioniert diese Demo?", expanded=True):
    st.markdown(
        r"""
**Phase 1 - Contract Net Protocol (Rekapitulation)**: wie in contract-net-demo -
Aufträge werden einzeln angekündigt, das niedrigste Gebot gewinnt, endgültig.
Dient hier nur als Vergleichs-Basislinie, nicht als Ausgangspunkt für DPOP.

**Zwei Ebenen, nicht eine**: Ein **DCOP** ist das *Modell* - Variablen, Domänen
und eine Summe lokaler Kostenfunktionen. **DPOP** ist der *Löser*, der genau
dieses Modell exakt minimiert. Die Modellierungsentscheidungen (Variablen,
Kosten, Graph) stecken im DCOP; Pseudo-Baum, UTIL-/VALUE-Phase und
Tabellengröße gehören zu DPOP. Ein anderer Löser (z.B. Max-Sum, DSA) würde
dasselbe DCOP-Modell mit denselben Modellgrenzen lösen - nur mit anderen
Stärken und Schwächen beim Lösen selbst.

**Das DCOP-Modell**: eine Variable PRO AUFTRAG (nicht pro Agent) -
`x_j ∈ {Agent 0, ..., Agent k-1}`, welcher Agent (Kran) Auftrag `j` übernimmt.
Achtung, zwei Bedeutungen von "Agent": in dieser Demo (wie in der ganzen
Reihe) ist ein Agent ein Kran; im DCOP-Formalismus heißt "Agent" dagegen der
Besitzer einer Variable - hier also der Auftrag. Die Krane sind die *Werte*
der Domäne. Die
Reihenfolge innerhalb eines Agenten wird bewusst NICHT modelliert (genau wie
bei der Task-Swap-Verhandlung: Eigentümerschaft getrennt von Reihenfolge,
aufsteigend nach Auftrags-Index).

**Warum ein Summen-Surrogat**: Ein DCOP minimiert per Definition eine SUMME
von Unär- und Paarkosten. Der echte Makespan lässt sich so nicht ausdrücken:
die Fertigstellungszeit eines Agenten hängt von ALLEN seinen Aufträgen und
deren Reihenfolge ab (eine n-stellige Funktion, keine unäre oder paarweise),
und darüber liegt noch ein Maximum über die Agenten. Deshalb modelliert dieses
DCOP ein bewusst gewähltes Surrogat: **Unärkosten** (wie teuer wäre Auftrag
`j` für Agent `a` allein) plus **Paarkosten** für JEDES Auftragspaar (0, falls
verschiedene Agenten; sonst die Distanz zwischen den beiden Aufträgen - eine
reihenfolge-unabhängige Näherung der Zusatzkosten, wenn derselbe Agent beide
übernimmt).

**Warum der Graph vollständig ist**: jedes Auftragspaar bekommt eine
Paarkosten-Kante, absichtlich - das lässt die Schwäche von DPOP (siehe unten)
sofort und drastisch sichtbar werden, statt sie künstlich zu vermeiden.

**DPOP: der Pseudo-Baum entartet zu einer Kette**: eine Tiefensuche auf einem
vollständigen Graphen hat nie einen Grund zurückzuspringen - jeder noch nicht
besuchte Auftrag ist ja ohnehin Nachbar. Auftrag 0 wird zur Wurzel, Auftrag
`n-1` zum Blatt, und Auftrag `j`s "Separator" (seine Vorfahren) ist immer
`{0,...,j-1}` - seine Tabellengröße wächst als `n_agents^j`.

**UTIL-Phase (bottom-up)**: beginnend beim Blatt berechnet jeder Auftrag für
JEDE mögliche Kombination der Werte seiner Vorfahren die beste eigene Wahl
(seine lokalen Kosten plus die bereits vom Kind berechnete Tabelle) und
sendet nur DIESES Ergebnis (eine Spalte kürzer) an seinen Baum-Elternteil -
kein einzelner Knoten sieht je den vollen gemeinsamen Zustand.

**VALUE-Phase (top-down)**: die Wurzel entnimmt ihren Wert direkt ihrer
eigenen (jetzt vollständigen) Tabelle; jeder weitere Auftrag schlägt in
seiner EIGENEN, während der UTIL-Phase behaltenen Tabelle nach - an der
Stelle, die den bereits feststehenden Werten seiner Vorfahren entspricht.

**Cross-Line-Bezug**: auf dieser entarteten Kette ist DPOP strukturell
dieselbe Tabellierung wie in dynamic-programming-demo - nur VERTEILT: jeder
Auftrag berechnet und sendet nur seine eigene Tabelle, nie die volle gemeinsame.

**Zwei getrennte Fragen, nicht eine**:
- *Löst DPOP das DCOP richtig?* (Frage an den Löser) → Vergleich gegen eine
  erschöpfende Brute-Force-Suche über dasselbe Summen-Ziel. Sollte IMMER
  ≈0 sein - ein Fehlschlag wäre ein echter Implementierungsfehler.
- *Ist das DCOP-Ziel dasselbe wie der echte Makespan?* (Frage ans Modell) →
  Vergleich der aus DPOPs Zuteilung abgeleiteten echten Zeitplanung gegen das
  zentrale CP-SAT-Optimum. Das ist die eigentliche, oft erhebliche Lücke.

**Keine bewiesene Reihenfolge**: anders als bei task-swap-demos
`ALG ≥ LS ≥ OPT` gibt es hier KEINE Garantie, dass DPOP mindestens so gut wie
das rohe Contract-Net-Ergebnis ist - DPOP kann schlechter UND besser
abschneiden, die App zeigt genau, wann was.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
PRESET_HELP = C.PRESET_HELP
preset_cols = st.columns(len(C.PRESETS))
for i, name in enumerate(C.PRESETS.keys()):
    with preset_cols[i]:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_jobs = st.slider(
        "Anzahl Aufträge", *bounds("n_jobs_slider"), key="n_jobs_slider",
        help="Bewusst eng begrenzt: DPOPs letzte UTIL-Tabelle wächst als n_agents^(n_jobs-1).",
    )
    n_agents = st.slider("Anzahl Agenten (Kräne)", *bounds("n_agents_slider"), key="n_agents_slider")
    duration_variability = st.slider(
        "Streuung der Auftragsdauer", *bounds("duration_variability_slider"), key="duration_variability_slider",
    )
    travel_time_per_unit = st.slider(
        "Anfahrtszeit pro Positionseinheit", *bounds("travel_time_per_unit_slider"),
        key="travel_time_per_unit_slider",
    )
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)

    st.button(
        "🎲 Neue Instanz generieren",
        width="stretch",
        on_click=randomize_seed,
        help="Würfelt einen neuen Zufalls-Seed für Auftragspositionen und -dauern.",
    )

sync_query_params(n_jobs, n_agents, duration_variability, travel_time_per_unit, seed)

scenario_key = (int(n_jobs), int(n_agents), duration_variability, travel_time_per_unit, int(seed))

with st.spinner("Führe Contract Net Protocol aus..."):
    instance, cnp_result = _compute_cnp(*scenario_key)
with st.spinner("Löse DPOP..."):
    dpop_result = _compute_dpop(*scenario_key)
cmp = _compute_comparison(*scenario_key)
ortools_makespan = cmp["ortools_makespan"] if cmp["ortools_feasible"] else None

# --- Phase 1: Contract Net Rekapitulation -----------------------------------

st.markdown("## 🎯 Phase 1: Contract Net Protocol (Rekapitulation)")

if "cn_step" not in st.session_state or st.session_state.get("cn_step_owner") != scenario_key:
    st.session_state["cn_step"] = instance.n_jobs - 1
    st.session_state["cn_step_owner"] = scenario_key

max_step = instance.n_jobs - 1
step_col, play_col = st.columns([5, 1])
with step_col:
    if max_step == 0:
        step = 0
        st.caption("Nur ein Auftrag - kein Regler nötig.")
    else:
        step = st.slider("Schritt (Auftragsvergabe)", 0, max_step, key="cn_step")
with play_col:
    auto_play_cnp = st.button("▶️ Abspielen", width="stretch", key="cnp_play")

chart_col, bid_col = st.columns([3, 2])
schedule_slot = chart_col.empty()
bid_slot = bid_col.empty()


def _render_cnp(current_step):
    schedule_slot.plotly_chart(
        build_schedule_figure(instance, cnp_result, current_step, ortools_makespan),
        width="stretch", key=f"cnp_schedule_{current_step}",
    )
    bid_slot.plotly_chart(
        build_bid_chart(cnp_result.steps[current_step]),
        width="stretch", key=f"cnp_bids_{current_step}",
    )


if auto_play_cnp:
    for s in range(0, max_step + 1):
        _render_cnp(s)
        time.sleep(0.4)
    step = max_step
else:
    _render_cnp(step)

live = stats_up_to_step(cnp_result, step)
lm1, lm2 = st.columns(2)
lm1.metric("Aufträge bisher vergeben", f"{live['jobs_awarded']} / {instance.n_jobs}")
lm2.metric("Aktuell schlechteste freie Zeit", f"{live['worst_agent_free_time']:.1f} min")

st.markdown("---")

# --- Phase 2a: DPOP UTIL-Phase ------------------------------------------------

st.markdown("## 🔼 Phase 2a: DPOP UTIL-Phase (bottom-up)")
st.caption(
    "Schritt 0 = Blatt (letzter Auftrag, größte Tabelle), letzter Schritt = Wurzel "
    "(Auftrag 1, ein einziger Bestwert) - genau die Berechnungsreihenfolge von DPOP."
)

util_max_step = instance.n_jobs - 1
util_step_col, util_play_col = st.columns([5, 1])
with util_step_col:
    if util_max_step == 0:
        util_step = 0
        st.caption("Nur ein Auftrag - kein Regler nötig.")
    else:
        util_step = st.slider("Schritt (UTIL-Berechnung)", 0, util_max_step, key="util_step")
with util_play_col:
    auto_play_util = st.button("▶️ Abspielen", width="stretch", key="util_play")

util_chart_slot = st.empty()
util_caption_slot = st.empty()


def _render_util(s):
    job_index = instance.n_jobs - 1 - s
    table = dpop_result.util_tables[job_index]
    fig, n_truncated = build_util_step_bar(table)
    util_chart_slot.plotly_chart(fig, width="stretch", key=f"util_{s}")
    size = util_table_size(instance.n_agents, job_index)
    trunc_note = f" (nur die ersten 16 von {size:,} Einträgen angezeigt)" if n_truncated else ""
    util_caption_slot.caption(
        f"Auftrag {job_index + 1}, Separator {table.separator} - Tabellengröße: {size:,}{trunc_note}"
    )


if auto_play_util:
    for s in range(0, util_max_step + 1):
        _render_util(s)
        time.sleep(0.6)
    util_step = util_max_step
else:
    _render_util(util_step)

st.plotly_chart(
    build_util_table_size_chart(instance, cmp["util_table_sizes"]), width="stretch", key="util_size_chart",
)
st.caption(
    f"Größte Tabelle: **{max(cmp['util_table_sizes']):,} Einträge** bei nur {instance.n_jobs} Aufträgen - "
    "das ist DPOPs eigene, strukturelle Schwäche (Tabellengröße wächst als n_agents^job_index auf einem "
    "vollständigen Constraint-Graphen), unabhängig davon, ob der Makespan am Ende passt."
)

st.markdown("---")

# --- Phase 2b: DPOP VALUE-Phase -----------------------------------------------

st.markdown("## 🔽 Phase 2b: DPOP VALUE-Phase (top-down)")
st.caption("Schritt 0 = Wurzel (Auftrag 1) zuerst entschieden, danach absteigend in Auftragsreihenfolge.")

value_max_step = instance.n_jobs - 1
value_step_col, value_play_col = st.columns([5, 1])
with value_step_col:
    if value_max_step == 0:
        value_step = 0
        st.caption("Nur ein Auftrag - kein Regler nötig.")
    else:
        value_step = st.slider("Schritt (VALUE-Entscheidung)", 0, value_max_step, key="value_step")
with value_play_col:
    auto_play_value = st.button("▶️ Abspielen", width="stretch", key="value_play")

value_chart_slot = st.empty()
value_caption_slot = st.empty()


def _partial_schedules(up_to_job):
    schedules = {a: [] for a in range(instance.n_agents)}
    for job_index in range(up_to_job + 1):
        schedules[dpop_result.assignment[job_index]].append(job_index)
    return {a: tuple(jobs) for a, jobs in schedules.items()}


def _render_value(s):
    schedules = _partial_schedules(s)
    value_chart_slot.plotly_chart(
        build_dcop_schedule_figure(instance, schedules, ortools_makespan, highlight_jobs=frozenset({s})),
        width="stretch", key=f"value_{s}",
    )
    value_caption_slot.caption(f"Schritt {s + 1}: " + describe_value_step(s, dpop_result.assignment[s]))


if auto_play_value:
    for s in range(0, value_max_step + 1):
        _render_value(s)
        time.sleep(0.5)
    value_step = value_max_step
else:
    _render_value(value_step)

st.markdown("---")

# --- Vergleich ---------------------------------------------------------------

st.subheader("📐 Ist das DCOP das richtige Problem?")

st.markdown("**Frage 1 (Löser): Löst DPOP das DCOP richtig?**")
correctness_delta = cmp["correctness_gap"]
st.metric(
    "DCOP-Ziel: DPOP vs. Brute-Force", f"{cmp['dpop_total_cost']:.2f}",
    delta=f"{correctness_delta:+.6f}" if abs(correctness_delta) >= 1e-6 else "±0.000000",
    delta_color="off",
    help="Sollte IMMER ≈0 sein - das beweist die Implementierung, nicht nur die Algorithmus-Behauptung.",
)

st.markdown("**Frage 2 (Modell): Ist das DCOP-Ziel dasselbe wie der echte Makespan?**")
vc1, vc2, vc3 = st.columns(3)
vc1.metric("Contract Net (roh)", f"{cmp['cnp_makespan']:.1f} min")

dpop_vs_cnp = cmp["dpop_vs_cnp"]
if abs(dpop_vs_cnp) < 1e-6:
    vc2.metric("DPOP-Makespan", f"{cmp['dpop_makespan']:.1f} min", delta="±0.0 min", delta_color="off")
else:
    vc2.metric(
        "DPOP-Makespan", f"{cmp['dpop_makespan']:.1f} min",
        delta=f"{dpop_vs_cnp:+.1f} min ggü. Contract Net roh", delta_color="inverse",
    )

if cmp["ortools_feasible"]:
    delta_ortools = cmp["ortools_makespan"] - cmp["dpop_makespan"]
    vc3.metric(
        "Zentrale Optimierung (CP-SAT)", f"{cmp['ortools_makespan']:.1f} min",
        delta=f"{delta_ortools:+.1f} min ggü. DPOP" if abs(delta_ortools) >= 1e-6 else "±0.0 min",
        delta_color="inverse" if abs(delta_ortools) >= 1e-6 else "off",
        help=f"Echter industrieller Solver, {cmp['ortools_wall_time']:.2f}s - "
        + ("beweist Optimalität." if cmp["ortools_optimal"] else "Zeitlimit erreicht, beste gefundene Lösung."),
    )
else:
    vc3.metric("Zentrale Optimierung (CP-SAT)", "kein Ergebnis im Zeitlimit")

if cmp["makespan_gap_pct"] is not None:
    st.caption(
        f"Lücke DPOP zu CP-SAT: **{cmp['makespan_gap_pct']:.1f}%**. DPOP vs. Contract Net roh: "
        f"**{cmp['dpop_vs_cnp_pct']:+.1f}%**."
    )

    if cmp["makespan_gap_pct"] >= C.MAKESPAN_GAP_WARNING_THRESHOLD_PCT:
        st.warning(
            f"⚠️ **Modellierungslücke**: DPOP hat das DCOP exakt gelöst (siehe Frage 1 oben), "
            f"verfehlt den echten Makespan aber um **{cmp['makespan_gap_pct']:.1f}%**. Das liegt NICHT an "
            f"eingeschränkter Kommunikation oder Suche (DPOP hatte volle Information und hat erschöpfend "
            f"gesucht) - sondern am DCOP-Modell: ein DCOP minimiert eine Summe von Unär- und Paarkosten, "
            f"der echte Makespan (Maximum über Agenten, je eine reihenfolgeabhängige Summe) lässt sich so "
            f"nur als Surrogat abbilden."
        )
    elif cmp["dpop_vs_cnp_pct"] >= C.DPOP_VS_CNP_NOTABLE_PCT:
        st.warning(
            f"⚠️ DPOP schneidet hier **{cmp['dpop_vs_cnp_pct']:.1f}% schlechter** ab als das naive, "
            f"myopische Contract-Net-Ergebnis - überraschend, aber kein Fehler: das DCOP exakt zu lösen "
            f"garantiert nicht, dass sein Ziel dem tatsächlichen Makespan entspricht."
        )
    elif cmp["dpop_vs_cnp_pct"] <= -C.DPOP_VS_CNP_NOTABLE_PCT:
        st.success(
            f"✅ Das Summen-Surrogat zahlt sich hier aus: DPOP schneidet **{-cmp['dpop_vs_cnp_pct']:.1f}% "
            f"besser** ab als das naive Contract-Net-Ergebnis."
        )
    else:
        st.info("Bei dieser Instanz unterscheiden sich DPOP und Contract Net kaum.")

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Unärkosten** für Auftrag $j$ bei Agent $a$ (Startposition $p_a$, Auftrags-Position
$q_j$, Dauer $d_j$):

$$
\text{unary}(j, a) = |p_a - q_j| \cdot \tau + d_j
$$

**Paarkosten** für Aufträge $i \neq j$:

$$
\text{pairwise}(i, j, a, b) = \begin{cases} 0 & a \neq b \\ |q_i - q_j| \cdot \tau & a = b \end{cases}
$$

**DCOP-Ziel** (vollständiger Graph, jedes Paar zählt):

$$
\text{objective}(x) = \sum_j \text{unary}(j, x_j) + \sum_{i<j} \text{pairwise}(i,j,x_i,x_j)
$$

**Separator-Formel (DPOP)**: auf der (aus dem vollständigen Graphen erzwungenen)
Ketten-Struktur ist Auftrag $j$s Separator $\{0,\dots,j-1\}$, Tabellengröße
$n_{\text{agents}}^{\,j}$.

**UTIL-Rekursion (DPOP)**: für Auftrag $j$ mit Separator-Belegung $s=(x_0,\dots,x_{j-1})$
und (falls vorhanden) Kind-Tabelle $U_{j+1}$:

$$
U_j(s) = \min_{x_j} \Big[ \text{unary}(j,x_j) + \sum_{i<j} \text{pairwise}(i,j,x_i,x_j) + U_{j+1}(s, x_j) \Big]
$$

(für das Blatt entfällt der letzte Term, für die Wurzel ist $s=()$).

**VALUE-Rekursion (DPOP)**: $x_0 = \arg\min U_0(())$; für $j>0$: $x_j$ = das im UTIL-Schritt
festgehaltene Optimum von $U_j$ an der Stelle $(x_0,\dots,x_{j-1})$.

**Tie-Break**: Agenten-IDs aufsteigend, nur bei striktem `<` aktualisieren - deckt
sich exakt mit einer Brute-Force-Enumeration in `itertools.product`-Reihenfolge.

**Keine bewiesene Reihenfolge**: anders als bei task-swap-demos
$\text{ALG} \geq \text{LS} \geq \text{OPT}$ gibt es hier keine Garantie
$\text{DPOP} \geq/\leq \text{ALG}$ - beide Richtungen kommen empirisch vor
(siehe Presets).

Implementiert in `dcop_graph.py` (Unär-/Paarkosten, Zielfunktion),
`dcop_dpop.py` (`solve_dcop`, UTIL-/VALUE-Phasen), `dcop_bruteforce.py`
(Korrektheits-Referenz) und `dcop_evaluation.py` (`full_comparison`,
die beiden getrennten Vergleiche).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
