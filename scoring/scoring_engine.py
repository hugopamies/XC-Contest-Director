import math

def compute_round_score(data, category="academic",
                        best_unloaded_payload=1.0,
                        best_loading_time=1.0,
                        best_circuit_time=1.0,
                        best_glide_time=1.0):
    """
    Computes a team's round score based on inputs and category-specific weights.
    """

    # Scoring weights per category
    weights = {
        "academic": {
            "payload": 150,
            "circuit": 150,
            "glide": 100,
            "altitude": 100,
            "loading": 100
        },
        "clubs": {
            "payload": 200,
            "circuit": 200,
            "glide": 150,
            "altitude": 150,
            "loading": 100
        }
    }

    w = weights.get(category, weights["academic"])  # fallback to academic if not found

    # Input values
    Csol = data['Requested Payload']
    Cdes = data['Unloaded Payload']
    Tcircuit = data['Time Circuit']
    Tglide = data['Time Glide']
    A60s = data['Altitude']
    Tcarga = data['Loading Time']
    takeoff_distance = data['Takeoff Distance']
    internal_pilot = data['Pilot']
    legal_flight = data['Legal Flight']
    good_landing = data['Good Landing']
    used_replacement_parts = data['Replacement Parts']

    # --- Partial Scores ---
    Ppeso = w["payload"] * (Cdes / best_unloaded_payload) * (Cdes / Csol) if Csol > 0 else 0
    Ptiempo = w["circuit"] * (best_circuit_time / Tcircuit) if Tcircuit > 0 else 0
    Pglide = w["glide"] * (Tglide / best_glide_time) if best_glide_time > 0 else 0

    if category == "Academic":
        altitude_score = 4.3636e-6 * (A60s ** 4) - 0.001215 * (A60s ** 3) + 0.095732 * (A60s ** 2) - 0.86741 * A60s
    elif category == "Clubs":
        altitude_score = 6.5455e-6 * (A60s ** 4) - 0.001822 * (A60s ** 3) + 0.1436 * (A60s ** 2) - 1.3011 * A60s
    else:
        altitude_score = 0

    if Tcarga > 0:
        carga_eff = Cdes / math.sqrt(Tcarga)
        best_eff = best_unloaded_payload / math.sqrt(best_loading_time)
        Bcarga = w["loading"] * (carga_eff / best_eff)
    else:
        Bcarga = 0

    # --- Multipliers ---
    Bdespegue = 1.0
    if takeoff_distance <= 20:
        Bdespegue = 1.25
    elif takeoff_distance <= 40:
        Bdespegue = 1.125

    Spiloto = 1.0 #if internal_pilot else 0.75
    Lvuelo = 1.0 #if legal_flight else 0.0
    Laterrizaje = 1.0 #if good_landing else 0.5
    Srepuestos = 1.0 #if used_replacement_parts else 1.0

    # --- Final Score ---
    base = Ppeso + Ptiempo + Pglide + altitude_score
    total = ((base * Lvuelo * Laterrizaje + Bcarga) * Bdespegue) * Spiloto * Srepuestos

    return round(total, 2)

def total_score(round_scores):
    """Total score = average of all rounds except the worst one."""
    if not round_scores:
        return 0
    if len(round_scores) == 1:
        return round_scores[0]
    
    # Drop the lowest score and average the rest
    best_rounds = sorted(round_scores, reverse=True)[:-1]
    return round(sum(best_rounds) / len(best_rounds), 2)

def get_best_values_per_round(results, category, round_index):
    """
    Returns best values for normalization in a given round:
    - Highest unloaded payload
    - Shortest loading time
    - Shortest circuit time
    - Longest gliding time
    """
    best_unloaded_payload = 0
    best_loading_time = float("inf")
    best_circuit_time = float("inf")
    best_glide_time = 0

    for team_scores in results.get(category, {}).values():
        if round_index >= len(team_scores):
            continue

        entry = team_scores[round_index]
        inputs = entry.get("inputs") if isinstance(entry, dict) else None
        if not inputs:
            continue

        Cdes = inputs.get("Unloaded Payload")
        Tcarga = inputs.get("Loading Time")
        Tcircuit = inputs.get("Time Circuit")
        Tglide = inputs.get("Time Glide")

        if Cdes is not None:
            best_unloaded_payload = max(best_unloaded_payload, Cdes)
        if Tcarga and Tcarga > 0:
            best_loading_time = min(best_loading_time, Tcarga)
        if Tcircuit and Tcircuit > 0:
            best_circuit_time = min(best_circuit_time, Tcircuit)
        if Tglide is not None:
            best_glide_time = max(best_glide_time, Tglide)

    # Safeguards
    best_loading_time = best_loading_time if best_loading_time < float("inf") else 1
    best_circuit_time = best_circuit_time if best_circuit_time < float("inf") else 1
    best_unloaded_payload = best_unloaded_payload if best_unloaded_payload > 0 else 1
    best_glide_time = best_glide_time if best_glide_time > 0 else 1

    return best_unloaded_payload, best_loading_time, best_circuit_time, best_glide_time
