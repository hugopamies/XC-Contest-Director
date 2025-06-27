# XtraChallenge 2025 - UAV Contest Director and Dashboard

This is the official scoring and visualization dashboard for the **XtraChallenge 2025** UAV competition. It enables contest directors to manage, input, visualize, and export team performance data in real time across multiple categories and rounds.
Please note that all existing scores in this code are mere examples and not real. The final scores will be published in www.xtra2upv.com after the competition.

##  Features

-  Input and update flight results per team and round
-  Score calculation with real-time normalization per round
-  Tabbed rankings view (Academic & Clubs) with sorting and export
-  Dynamic statistics dashboard:
  - Team performance trends
  - Glide & circuit distribution by round
  - Top performers per metric (payload, circuit time, etc.)
  - Round tabs and automatic rotation
-  PDF and Excel exports
-  Manual and editable round management

---

##  Scoring Logic

Implemented in `scoring/scoring_engine.py`, with category-specific weights and dynamic normalization using:
- Best glide time
- Shortest loading and circuit time
- Max payload carried

Total score is the average of all rounds, excluding the worst if more than 3.

---

##  Required Libraries

```
pip install PyQt6 matplotlib openpyxl reportlab
```

##  Run the App

```
python main.py
```


