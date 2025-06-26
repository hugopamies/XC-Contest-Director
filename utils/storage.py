import json
import os

RESULTS_FILE = "data/results.json"

def load_results():
    if not os.path.exists(RESULTS_FILE):
        return {"Academic": {}, "Clubs": {}}
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_results(data):
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def add_round_score(team_id, category, score_entry):
    """
    Adds or updates a round score for a team in a specific category.
    The score_entry must contain a 'round' key indicating which round it belongs to.
    """
    data = load_results()
    str_id = str(team_id)
    round_index = score_entry.get("round")

    if str_id not in data[category]:
        data[category][str_id] = []

    team_scores = data[category][str_id]

    # Extend the list if the round index is beyond current length
    while len(team_scores) <= round_index:
        team_scores.append({})

    team_scores[round_index] = score_entry  # ✅ Replace at round index
    save_results(data)


def get_team_scores(team_id, category):
    data = load_results()
    return data.get(category, {}).get(str(team_id), [])

def delete_score(team_id, category, index):
    data = load_results()
    scores = data[category].get(str(team_id), [])
    if 0 <= index < len(scores):
        del scores[index]
        data[category][str(team_id)] = scores
        save_results(data)
        return True
    return False

def update_score(team_id, category, round_index, new_entry):
    data = load_results()
    str_id = str(team_id)

    if str_id in data[category] and 0 <= round_index < len(data[category][str_id]):
        data[category][str_id][round_index] = new_entry
        save_results(data)
        return True
    return False
