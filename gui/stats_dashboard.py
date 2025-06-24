from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget
from utils.storage import load_results
from scoring.scoring_engine import total_score
import json

class StatsDashboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("📊 XtraChallenge 2025 Stats Dashboard"))

        self.top3_list = QListWidget()
        self.avg_score_list = QListWidget()
        self.best_round_label = QLabel()
        self.total_flights_label = QLabel()

        layout.addWidget(QLabel("🥇 Top 3 Teams Overall"))
        layout.addWidget(self.top3_list)

        layout.addWidget(QLabel("🧮 Average Score per Team"))
        layout.addWidget(self.avg_score_list)

        layout.addWidget(QLabel("🎯 Best Single Round Score"))
        layout.addWidget(self.best_round_label)

        layout.addWidget(QLabel("🛫 Total Flights Logged"))
        layout.addWidget(self.total_flights_label)

        self.setLayout(layout)
        self.compute_stats()

    def compute_stats(self):
        with open("data/teams.json", "r", encoding="utf-8") as f:
            teams = json.load(f)
        results = load_results()

        combined_scores = []
        best_single_score = 0
        total_flights = 0

        for category in ["Academic", "Clubs"]:
            for team in teams[category]:
                tid = str(team["id"])
                rounds = results.get(category, {}).get(tid, [])
                scores = [r["score"] if isinstance(r, dict) else r for r in rounds]
                total_flights += len(scores)

                if scores:
                    best_score = max(scores)
                    if best_score > best_single_score:
                        best_single_score = best_score

                    combined_scores.append({
                        "id": team["id"],
                        "name": team["name"],
                        "category": category,
                        "total_score": total_score(scores),
                        "average_score": round(sum(scores) / len(scores), 2)
                    })

        # 🥇 Top 3 by total score
        top_3 = sorted(combined_scores, key=lambda x: x["total_score"], reverse=True)[:3]
        self.top3_list.clear()
        for t in top_3:
            self.top3_list.addItem(f"{t['name']} ({t['category']}) — {t['total_score']}")

        # 🧮 Average scores per team
        self.avg_score_list.clear()
        for t in combined_scores:
            self.avg_score_list.addItem(f"{t['name']} ({t['category']}) — Avg: {t['average_score']}")

        # 🎯 Best single round
        self.best_round_label.setText(f"{best_single_score:.2f}")

        # 🛫 Total rounds logged
        self.total_flights_label.setText(str(total_flights))
