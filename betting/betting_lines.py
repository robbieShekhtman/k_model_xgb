from typing import List, Dict, Optional
import re
from dotenv import load_dotenv

load_dotenv()

def normalize_pitcher_name(name: str) -> str:
    name = re.sub(r'\s+(?:Over|Under)\s+\d+\.?\d*$', '', name)
    
    name = re.sub(r'\s+(?:Jr\.|Sr\.|III|II|IV)$', '', name)
    
    return name.title().strip()

def get_team_abbreviation(team_name: str) -> str:
    team_map = {
        "Arizona Diamondbacks": "ARI",
        "Atlanta Braves": "ATL",
        "Baltimore Orioles": "BAL",
        "Boston Red Sox": "BOS",
        "Chicago Cubs": "CHC",
        "Chicago White Sox": "CWS",
        "Cincinnati Reds": "CIN",
        "Cleveland Guardians": "CLE",
        "Colorado Rockies": "COL",
        "Detroit Tigers": "DET",
        "Houston Astros": "HOU",
        "Kansas City Royals": "KC",
        "Los Angeles Angels": "LAA",
        "Los Angeles Dodgers": "LAD",
        "Miami Marlins": "MIA",
        "Milwaukee Brewers": "MIL",
        "Minnesota Twins": "MIN",
        "New York Mets": "NYM",
        "New York Yankees": "NYY",
        "Oakland Athletics": "ATH",
        "Philadelphia Phillies": "PHI",
        "Pittsburgh Pirates": "PIT",
        "San Diego Padres": "SD",
        "San Francisco Giants": "SF",
        "Seattle Mariners": "SEA",
        "St. Louis Cardinals": "STL",
        "Tampa Bay Rays": "TB",
        "Texas Rangers": "TEX",
        "Toronto Blue Jays": "TOR",
        "Washington Nationals": "WSH"
    }
    return team_map.get(team_name, team_name)

def get_strikeout_props(date: Optional[str] = None) -> List[Dict]:
    # Currently this must be manually inputted each day
    return [
        {'pitcher': 'Chad Patrick', 'team': 'MIL', 'opponent': 'COL', 'line': 6.5, 'over_odds': None, 'under_odds': -165, 'book': 'ESPN Bet'},
        {'pitcher': 'Chris Paddack', 'team': 'MIN', 'opponent': 'DET', 'line': 3.5, 'over_odds': -132, 'under_odds': None, 'book': 'FanDuel'},
        {'pitcher': 'Luis Severino', 'team': 'ATH', 'opponent': 'NYY', 'line': 4.0, 'over_odds': -137, 'under_odds': None, 'book': 'PrizePicks'},
        {'pitcher': 'Nick Lodolo', 'team': 'CIN', 'opponent': 'SD', 'line': 4.0, 'over_odds': -137, 'under_odds': None, 'book': 'PrizePicks'},
        {'pitcher': 'Kris Bubic', 'team': 'KC', 'opponent': 'LAD', 'line': 4.5, 'over_odds': -142, 'under_odds': None, 'book': 'FanDuel'},
        {'pitcher': 'Matthew Liberatore', 'team': 'STL', 'opponent': 'CLE', 'line': 4.0, 'over_odds': -137, 'under_odds': None, 'book': 'PrizePicks'},
        {'pitcher': 'Spencer Strider', 'team': 'ATL', 'opponent': 'PHI', 'line': 7.5, 'over_odds': None, 'under_odds': -124, 'book': 'Underdog'},
        {'pitcher': 'German Marquez', 'team': 'COL', 'opponent': 'MIL', 'line': 3.5, 'over_odds': -115, 'under_odds': None, 'book': 'DraftKings'},
        {'pitcher': 'Mike Burrows', 'team': 'PIT', 'opponent': 'NYM', 'line': 3.5, 'over_odds': -128, 'under_odds': None, 'book': 'FanDuel'},
        {'pitcher': 'Justin Verlander', 'team': 'SF', 'opponent': 'CWS', 'line': 5.5, 'over_odds': None, 'under_odds': -145, 'book': 'DraftKings'},
        {'pitcher': 'Framber Valdez', 'team': 'HOU', 'opponent': 'CHC', 'line': 5.0, 'over_odds': -137, 'under_odds': None, 'book': 'PrizePicks'},
        {'pitcher': 'Tarik Skubal', 'team': 'DET', 'opponent': 'MIN', 'line': 8.0, 'over_odds': None, 'under_odds': -137, 'book': 'PrizePicks'},
        {'pitcher': 'Mitchell Parker', 'team': 'WSH', 'opponent': 'LAA', 'line': 4.0, 'over_odds': -137, 'under_odds': None, 'book': 'PrizePicks'},
        {'pitcher': 'Dean Kremer', 'team': 'BAL', 'opponent': 'TB', 'line': 4.0, 'over_odds': -137, 'under_odds': None, 'book': 'PrizePicks'},
        {'pitcher': 'Jack Kochanowicz', 'team': 'LAA', 'opponent': 'WSH', 'line': 3.5, 'over_odds': None, 'under_odds': -102, 'book': 'FanDuel'},
        {'pitcher': 'Walker Buehler', 'team': 'BOS', 'opponent': 'TOR', 'line': 3.5, 'over_odds': 108, 'under_odds': None, 'book': 'FanDuel'},
        {'pitcher': 'Jack Leiter', 'team': 'TEX', 'opponent': 'SEA', 'line': 4.5, 'over_odds': -110, 'under_odds': None, 'book': 'DraftKings'},
        {'pitcher': 'Logan Allen', 'team': 'CLE', 'opponent': 'STL', 'line': 4.5, 'over_odds': None, 'under_odds': -130, 'book': 'DraftKings'},
        {'pitcher': 'Cal Quantrill', 'team': 'MIA', 'opponent': 'ARI', 'line': 3.5, 'over_odds': None, 'under_odds': -162, 'book': 'FanDuel'},
        {'pitcher': 'Eduardo Rodriguez', 'team': 'ARI', 'opponent': 'MIA', 'line': 5.5, 'over_odds': None, 'under_odds': -120, 'book': 'DraftKings'},
        {'pitcher': 'Frankie Montas', 'team': 'NYM', 'opponent': 'PIT', 'line': 4.5, 'over_odds': None, 'under_odds': 105, 'book': 'DraftKings'},
        {'pitcher': 'Ranger Suarez', 'team': 'PHI', 'opponent': 'ATL', 'line': 5.5, 'over_odds': None, 'under_odds': -125, 'book': 'ESPN Bet'},
        {'pitcher': 'Luis Castillo', 'team': 'SEA', 'opponent': 'TEX', 'line': 5.5, 'over_odds': None, 'under_odds': -146, 'book': 'FanDuel'},
        {'pitcher': 'Jameson Taillon', 'team': 'CHC', 'opponent': 'HOU', 'line': 4.5, 'over_odds': None, 'under_odds': -156, 'book': 'FanDuel'},
        {'pitcher': 'Stephen Kolek', 'team': 'SD', 'opponent': 'CIN', 'line': 4.5, 'over_odds': None, 'under_odds': -150, 'book': 'FanDuel'},
        {'pitcher': 'Taj Bradley', 'team': 'TB', 'opponent': 'BAL', 'line': 5.5, 'over_odds': 105, 'under_odds': None, 'book': 'DraftKings'},
        {'pitcher': 'Eric Lauer', 'team': 'TOR', 'opponent': 'BOS', 'line': 4.5, 'over_odds': None, 'under_odds': -115, 'book': 'DraftKings'},
    ]


