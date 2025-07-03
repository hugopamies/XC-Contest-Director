import json
from openpyxl import Workbook
from PyQt5.QtWidgets import QPushButton, QFileDialog

def export_input_data_to_xlsx(json_data, save_path):
    wb = Workbook()
    # Remove default sheet created by Workbook
    default_sheet = wb.active
    wb.remove(default_sheet)
    
    # Gather all rounds from data for sheet names
    rounds = set()
    # JSON structure example: { "Academic": { "1": [ {round:0, inputs:{}}, ... ] }, ... }
    for category in json_data:
        if category in ["static_scores", "penalties", "penalty_reasons"]:
            continue
        teams = json_data[category]
        for team_id, attempts in teams.items():
            for attempt in attempts:
                rounds.add(attempt.get("round", None))
    rounds = sorted(r for r in rounds if r is not None)
    
    for rnd in rounds:
        ws = wb.create_sheet(title=f"Round {rnd+1}")  # +1 to make it human-readable (round 0 -> Round 1)
        
        # Header: Team ID, Category, + input keys + score
        header = ["Category", "Team ID"]
        first_team = None
        # Find the first input keys to set columns
        for category in json_data:
            if category in ["static_scores", "penalties", "penalty_reasons"]:
                continue
            for team_id, attempts in json_data[category].items():
                for attempt in attempts:
                    if attempt.get("round", None) == rnd:
                        first_team = attempt
                        break
                if first_team:
                    break
            if first_team:
                break
        if not first_team:
            continue  # No data for this round
        header += list(first_team["inputs"].keys())
        header.append("Score")
        
        ws.append(header)
        
        # Fill data
        for category in json_data:
            if category in ["static_scores", "penalties", "penalty_reasons"]:
                continue
            teams = json_data[category]
            for team_id, attempts in teams.items():
                for attempt in attempts:
                    if attempt.get("round", None) == rnd:
                        row = [category, team_id]
                        inputs = attempt.get("inputs", {})
                        for key in header[2:-1]:  # input keys
                            row.append(inputs.get(key, ""))
                        row.append(attempt.get("score", ""))
                        ws.append(row)
    
    wb.save(save_path)
