from typing import Dict, Union

# Ballpark strikeout factors based on 2023-25 averages
park_k_factors = {
    "COL": 0.92,  # Coors Field
    "BOS": 0.98,  # Fenway Park
    "CIN": 1.02,  # Great American Ball Park
    "ARI": 0.94,  # Chase Field
    "KC": 0.88,   # Kauffman Stadium
    "MIN": 1.07,  # Target Field
    "MIA": 0.99,  # loanDepot Park
    "HOU": 1.00,  # Minute Maid Park
    "WSH": 0.88,  # Nationals Park
    "LAD": 0.98,  # Dodger Stadium
    "BAL": 0.98,  # Camden Yards
    "LAA": 1.06,  # Angel Stadium
    "STL": 0.91,  # Busch Stadium
    "PIT": 0.95,  # PNC Park
    "ATL": 1.07,  # Truist Park
    "NYY": 1.01,  # Yankee Stadium
    "PHI": 1.02,  # Citizens Bank Park
    "TOR": 0.99,  # Rogers Centre
    "TEX": 1.00,  # Globe Life Field
    "DET": 0.99,  # Comerica Park
    "CWS": 1.01,  # Guaranteed Rate Field
    "SD": 1.02,   # Petco Park
    "NYM": 1.04,  # Citi Field
    "CHC": 1.02,  # Wrigley Field
    "CLE": 1.01,  # Progressive Field
    "SF": 0.97,   # Oracle Park
    "MIL": 1.11,  # American Family Field
    "SEA": 1.17   # T-Mobile Park
}

def apply_contextual_adjustments(pitcher: Dict, raw_k: float) -> Dict:
    park_team = pitcher["team"] if pitcher["home_away"] == "Home" else pitcher["opponent"]
    park_factor = park_k_factors.get(park_team, 1.00) 
    
    weather_factor = 1.0 # for now not incorporating
    umpire_factor = 1.0 # for now not incorporating
    
    adjusted_k = raw_k * park_factor * weather_factor * umpire_factor
    
    return {
        "pitcher": pitcher["name"],
        "raw_k": raw_k,
        "adjusted_k": adjusted_k,
        "park_team": park_team,
        "park_factor": park_factor,
        "weather_factor": weather_factor,
        "umpire_factor": umpire_factor
    } 