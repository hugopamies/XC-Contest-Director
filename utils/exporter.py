from utils.storage import load_results
from scoring.scoring_engine import total_score
import json
import csv

def export_all_scores(filename="ranking_export.csv"):
    with open("data/teams.json", "r", encoding="utf-8") as f:
        teams = json.load(f)
    results = load_results()

    combined = []
    for category in ["academic", "clubs"]:
        for team in teams[category]:
            tid = str(team["id"])
            rounds = results.get(category, {}).get(tid, [])
            score = total_score(rounds)
            combined.append((int(tid), team["name"], category.capitalize(), round(score, 2)))

    combined.sort(key=lambda x: x[3], reverse=True)
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Team ID", "Name", "Category", "Total Score"])
        writer.writerows(combined)
