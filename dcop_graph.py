"""Die DCOP-Formulierung selbst: eine Variable pro AUFTRAG (nicht pro Agent),
Domäne = Agenten-ID. Reihenfolge innerhalb eines Agenten wird bewusst NICHT
modelliert (wie bei der Task-Swap-Verhandlung: Eigentümerschaft getrennt von
Reihenfolge) - die echte Makespan-Berechnung übernimmt unverändert
`cn_schedule.schedule_from_assignment` (aufsteigend nach Auftrags-Index).

DPOP/Max-Sum können nur SUMMEN-zerlegbare Ziele lösen, Makespan ist ein MAX -
deshalb optimiert DPOP hier ein bewusst gewähltes Summen-Surrogat, nicht den
Makespan direkt:

- Unärkosten: wie teuer wäre es, wenn AGENT a Auftrag j ALLEIN übernimmt -
  dieselbe Formel wie ein einzelnes Contract-Net-Gebot.
- Paarkosten: 0, wenn zwei Aufträge an verschiedene Agenten gehen; sonst die
  (reihenfolge-unabhängige) Distanz zwischen ihnen - eine Näherung für die
  Zusatzkosten, wenn derselbe Agent beide übernimmt.

Der Graph ist bewusst VOLLSTÄNDIG (jedes Auftragspaar hat eine Paarkosten-
Kante) - das ist genau das, was DPOPs eigene Schwäche (Tabellengröße) sofort
und drastisch zeigt, siehe cn_dpop.py."""


def unary_cost(instance, job_index, agent_id):
    job = instance.jobs[job_index]
    travel = instance.travel_time(instance.agent_start_positions[agent_id], job.position)
    return travel + job.duration


def pairwise_cost(instance, job_i, job_j, agent_a, agent_b):
    if agent_a != agent_b:
        return 0.0
    return instance.travel_time(instance.jobs[job_i].position, instance.jobs[job_j].position)


def objective_value(instance, assignment):
    """assignment: dict job_index -> agent_id, für ALLE Aufträge der Instanz."""
    total = 0.0
    for job_index, agent_id in assignment.items():
        total += unary_cost(instance, job_index, agent_id)
    n = instance.n_jobs
    for i in range(n):
        for j in range(i + 1, n):
            total += pairwise_cost(instance, i, j, assignment[i], assignment[j])
    return total
