import requests
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Union
from pybaseball import playerid_lookup, batting_stats
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


TEAM_NAME_TO_ABBR = {
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
    "Oakland Athletics": "OAK",
    "Athletics": "OAK",  # Alternative name
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

def get_lineup_for_team(team_abbr: str, date_str: str):
    try:
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher,lineups"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not data.get('dates'):
            print(f"No games found for {date_str}")
            return []
        games = data['dates'][0].get('games', [])
        for game in games:
            home_team_name = game.get('teams', {}).get('home', {}).get('team', {}).get('name', '')
            away_team_name = game.get('teams', {}).get('away', {}).get('team', {}).get('name', '')
            home_abbr = TEAM_NAME_TO_ABBR.get(home_team_name, '')
            away_abbr = TEAM_NAME_TO_ABBR.get(away_team_name, '')
            lineups = game.get('lineups', {})
            if team_abbr == home_abbr and 'homePlayers' in lineups:
                batters = [{'name': player.get('fullName', ''), 'team': team_abbr} for player in lineups['homePlayers']]
                if len(batters) == 9:
                    print(f"Found lineup for {team_abbr}: {', '.join(b['name'] for b in batters)}")
                    return batters
                else:
                    print(f"Incomplete home lineup for {team_abbr}: {len(batters)} batters")
                    return batters
            elif team_abbr == away_abbr and 'awayPlayers' in lineups:
                batters = [{'name': player.get('fullName', ''), 'team': team_abbr} for player in lineups['awayPlayers']]
                if len(batters) == 9:
                    print(f"Found lineup for {team_abbr}: {', '.join(b['name'] for b in batters)}")
                    return batters
                else:
                    print(f"Incomplete away lineup for {team_abbr}: {len(batters)} batters")
                    return batters
        print(f"No lineup found for {team_abbr} on {date_str}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching lineup from MLB API: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error getting lineup for {team_abbr}: {str(e)}")
        print("Full traceback:")
        return []

def get_opposing_lineups(pitchers: List[Dict], date_str: Optional[str] = None):
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
        
    lineup_map = {}
    
    for pitcher in pitchers:
        opponent = pitcher.get('opponent')
        if not opponent:
            print(f"No opponent found for {pitcher.get('pitcher_name')}")
            continue
            

        if opponent in TEAM_NAME_TO_ABBR.values():
            team_abbr = opponent
        else:
            team_abbr = TEAM_NAME_TO_ABBR.get(opponent)
            if not team_abbr:
                print(f"Could not convert team name '{opponent}' to abbreviation")
                continue
            
        print(f"Getting lineup for {pitcher['pitcher_name']}'s opponent: {opponent}")
        lineup = get_lineup_for_team(team_abbr, date_str)
        if lineup:
            lineup_map[pitcher['pitcher_name']] = lineup
        else:
            print(f"Failed to get lineup for {opponent}")
            
    return lineup_map 


def get_batter_stats(batter_name: str, season: int = 2025):
    try:
        name_parts = batter_name.split()
        if len(name_parts) < 2:
            print(f"Invalid name format: {batter_name}")
            return {}
            
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        fg_id = resolve_fangraphs_id(first_name, last_name)
        if not fg_id:
            print(f"Could not resolve FanGraphs ID for {batter_name}")
            fg_id = -1 
            
        stats = batting_stats(season, qual=0)
        batter_stats = stats[stats['IDfg'] == fg_id]
        
        if batter_stats.empty and fg_id == -1:
            print(f"No match found by ID, trying to find by name: {batter_name}")
            all_names = stats['Name'].tolist()
            
            best_match = process.extractOne(batter_name, all_names, scorer=fuzz.token_sort_ratio)
            
            if best_match and best_match[1] >= 90: 
                print(f"Found fuzzy match: {best_match[0]} with score {best_match[1]}")
                new_fg_id = int(stats[stats['Name'] == best_match[0]]['IDfg'].iloc[0])
                print(f"Updated FanGraphs ID to {new_fg_id}")
                batter_stats = stats[stats['IDfg'] == new_fg_id]
                fg_id = new_fg_id
            else:
                print(f"No good fuzzy match found for {batter_name}")
        
        if batter_stats.empty:
            return {}
            
        stats_row = batter_stats.iloc[0]
        
        pitch_metrics = {
            'Fastball': {
                'w_pitch': float(stats_row['wFA (sc)']) if pd.notna(stats_row['wFA (sc)']) else 0,
                'pct_seen': float(stats_row['FA% (sc)']) if pd.notna(stats_row['FA% (sc)']) else 0,
            },
            'Slider': {
                'w_pitch': float(stats_row['wSL (sc)']) if pd.notna(stats_row['wSL (sc)']) else 0,
                'pct_seen': float(stats_row['SL% (sc)']) if pd.notna(stats_row['SL% (sc)']) else 0,
            },
            'Changeup': {
                'w_pitch': float(stats_row['wCH (sc)']) if pd.notna(stats_row['wCH (sc)']) else 0,
                'pct_seen': float(stats_row['CH% (sc)']) if pd.notna(stats_row['CH% (sc)']) else 0,
            },
            'Curveball': {
                'w_pitch': float(stats_row['wCU (sc)']) if pd.notna(stats_row['wCU (sc)']) else 0,
                'pct_seen': float(stats_row['CU% (sc)']) if pd.notna(stats_row['CU% (sc)']) else 0,
            },
            'Cutter': {
                'w_pitch': float(stats_row['wFC (sc)']) if pd.notna(stats_row['wFC (sc)']) else 0,
                'pct_seen': float(stats_row['FC% (sc)']) if pd.notna(stats_row['FC% (sc)']) else 0,
            }
        }
        
        general_metrics = {
            'swstr': float(stats_row['SwStr%']) if pd.notna(stats_row['SwStr%']) else 0,
            'contact': float(stats_row['Contact% (sc)']) if pd.notna(stats_row['Contact% (sc)']) else 0
        }
        
        return {
            'pitch_metrics': pitch_metrics,
            'general_metrics': general_metrics,
            'fg_id': fg_id 
        }
        
    except Exception as e:
        print(f"Error getting batter stats for {batter_name}: {str(e)}")
        return {}

def normalize_metrics(metrics):
    if not metrics:
        return []
    mean = np.mean(metrics)
    std = np.std(metrics)
    if std == 0:
        return [0] * len(metrics)
    return [(x - mean) / std for x in metrics]

def calculate_pitch_score(neg_w_z: float, pct_seen_z: float, swstr_z: float, contact_z: float) -> float:
    return (0.30 * neg_w_z + 
            0.07 * pct_seen_z + 
            0.42 * swstr_z - 
            0.21 * contact_z)

def calculate_matchup_score(batter_stats: Dict, pitch_mix: Dict) -> float:
    total_score = 0.0
    total_weight = 0.0
    
    for pitch_type, usage in pitch_mix.items():
        if pitch_type in batter_stats['pitch_metrics']:
            pitch_stats = batter_stats['pitch_metrics'][pitch_type]
            neg_w = -pitch_stats['w_pitch']
            pct_seen = pitch_stats['pct_seen']
            swstr = batter_stats['general_metrics']['swstr']
            contact = batter_stats['general_metrics']['contact']
            
            pitch_score = calculate_pitch_score(neg_w, pct_seen, swstr, contact)
            total_score += pitch_score * usage
            total_weight += usage
    
    return total_score / total_weight if total_weight > 0 else 0.0

def analyze_matchup(pitcher: Dict, opponent_lineup: List[Dict], season: int = 2025):
    try:
        pitcher_name = pitcher['pitcher_name']
        team = pitcher['team']
        opponent = pitcher['opponent']
        
        stats = pitcher.get('stats', {})
        if not stats:
            print(f"Skipping {pitcher_name} - no stats data")
            return None
            
        k_per_9 = stats.get('k_per_9', 0.0)
        ip_per_g = stats.get('ip_per_g', 0.0)
        pitch_mix = stats.get('pitch_mix', {})
        
        print(f"\nAnalyzing {pitcher_name} vs {opponent}")
        print(f"Pitch mix: {pitch_mix}")
        
        if not pitch_mix:
            print(f"Skipping {pitcher_name} - no pitch mix data")
            return None
            
        agg_lineup_score = 0.0
        batter_scores = []
        valid_batters = 0
        
        for batter in opponent_lineup:
            batter_stats = get_batter_stats(batter['name'], season)
            if not batter_stats:
                continue

            matchup_score = calculate_matchup_score(batter_stats, pitch_mix)
            
            if matchup_score is not None:
                agg_lineup_score += matchup_score
                valid_batters += 1
                
                batter_scores.append({
                    'name': batter['name'],
                    'agg': matchup_score
                })
        
        if valid_batters == 0:
            print(f"Skipping {pitcher_name} - no valid batter matchups")
            return None
            
        agg_lineup_score = agg_lineup_score / valid_batters
            
        predicted_strikeouts = (k_per_9 * ip_per_g) / 9.0
        
        confidence = min(1.0, valid_batters / 9.0)
        
        return {
            'pitcher': pitcher_name,
            'opponent': opponent,
            'handedness': 'R',  # Default to right-handed for now
            'agg_lineup_score': agg_lineup_score,
            'batter_scores': batter_scores,
            'predicted_strikeouts': predicted_strikeouts,
            'confidence': confidence
        }
        
    except Exception as e:
        print(f"Error analyzing matchup: {str(e)}")
        return None

def resolve_fangraphs_id(first_name: str, last_name: str) -> Union[int, None]:
    """
    Resolve a player's FanGraphs ID from their name using pybaseball.
    
    Args:
        first_name (str): Player's first name
        last_name (str): Player's last name
        
    Returns:
        Union[int, None]: FanGraphs ID if found, None if not found
    """
    try:
        player_info = playerid_lookup(last_name, first_name)
        if player_info.empty:
            return None
        player = player_info.iloc[0]
        if (player['name_first'].lower() == first_name.lower() and 
            player['name_last'].lower() == last_name.lower()):
            return player['key_fangraphs']
        return None
    except Exception as e:
        print(f"Error resolving FanGraphs ID for {first_name} {last_name}: {str(e)}")
        return None
