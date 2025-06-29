import requests
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from pybaseball import playerid_lookup, pitching_stats
from typing import List, Dict, Union
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Team name to abbreviation mapping
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
    "Athletics": "OAK",
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

def fetch_pitchers() -> List[Dict[str, Any]]:

    try:
        today = datetime.now().strftime('%Y-%m-%d')

        # MLB stats api endpoint for probable pitchers
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=probablePitcher"
        print(f"Fetching probable pitchers for {today}")
        
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('dates'):
            print(f"No games found for {today}")
            return []
            
        games = data['dates'][0].get('games', [])
        pitchers = []
        
        for game in games:
            
            game_time = game.get('gameDate', '')
            
            
            home_team_name = game.get('teams', {}).get('home', {}).get('team', {}).get('name', '')
            away_team_name = game.get('teams', {}).get('away', {}).get('team', {}).get('name', '')
            
            home_team = TEAM_NAME_TO_ABBR.get(home_team_name, '')
            away_team = TEAM_NAME_TO_ABBR.get(away_team_name, '')
            
            if not home_team or not away_team:
                print(f"Could not convert team names to abbreviations: {home_team_name} or {away_team_name}")
                continue
            
            
            home_pitcher = game.get('teams', {}).get('home', {}).get('probablePitcher', {})
            away_pitcher = game.get('teams', {}).get('away', {}).get('probablePitcher', {})
            
            
            if home_pitcher and home_pitcher.get('fullName') and home_pitcher.get('fullName') != 'Unknown':
                pitchers.append({
                    'pitcher_name': home_pitcher.get('fullName', ''),
                    'team': home_team,
                    'opponent': away_team,
                    'game_time': game_time,
                    'is_home': True
                })
            elif home_pitcher:
                print(f"Skipping unknown home pitcher for {home_team}")
            
            
            if away_pitcher and away_pitcher.get('fullName') and away_pitcher.get('fullName') != 'Unknown':
                pitchers.append({
                    'pitcher_name': away_pitcher.get('fullName', ''),
                    'team': away_team,
                    'opponent': home_team,
                    'game_time': game_time,
                    'is_home': False
                })
            elif away_pitcher:
                print(f"Skipping unknown away pitcher for {away_team}")
        
        print(f"Successfully fetched {len(pitchers)} probable pitchers for {today}")
        return pitchers
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from MLB API: {str(e)}")
        raise



def resolve_fangraphs_id(first_name: str, last_name: str) -> Union[int, None]:
    try:
        player_info = playerid_lookup(last_name, first_name, True)
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

def get_season_stats(fg_id: int, season: int = 2025, pitcher_name: str = None) -> Dict:
    try:
        print(f"\nFetching stats for ID {fg_id} for season {season}")
        stats = pitching_stats(season, qual=1)
        print(f"Found {len(stats)} total pitchers")
        
       
        pitcher_stats = stats[stats['IDfg'] == fg_id]

        if pitcher_stats.empty and pitcher_name:
            print(f"No match found by ID, trying to find by name: {pitcher_name}")

            all_names = stats['Name'].tolist()
            

            best_match = process.extractOne(pitcher_name, all_names, scorer=fuzz.token_sort_ratio)
            
            if best_match and best_match[1] >= 88: 
                print(f"Found fuzzy match: {best_match[0]} with score {best_match[1]}")
                pitcher_stats = stats[stats['Name'] == best_match[0]]
                if fg_id == -1 and not pitcher_stats.empty:
                    new_fg_id = int(pitcher_stats.iloc[0]['IDfg'])
                    print(f"Updated FanGraphs ID to {new_fg_id}")
                    return get_season_stats(new_fg_id, season)
            else:
                print(f"No good fuzzy match found for {pitcher_name}")
        
        print(f"Found {len(pitcher_stats)} matching pitchers")
        
        if pitcher_stats.empty:
            print(f"No stats found for ID {fg_id}")
            return {
                'k_per_9': 0.0,
                'ip': 0.0,
                'g': 0,
                'ip_per_g': 0.0,
                'pitch_mix': {},
                'fg_id': fg_id  # Keep the original fg_id if no match found
            }
            
        stats_row = pitcher_stats.iloc[0]
        print(f"\nFound stats for {stats_row['Name']}")
        
        g = stats_row['G'] if pd.notna(stats_row['G']) else 0
        ip = stats_row['IP'] if pd.notna(stats_row['IP']) else 0.0
        ip_per_g = ip / g if g > 0 else ip
        
        pitch_mix = {}
        pitch_types = {
            'FA% (pi)': 'Fastball',
            'FC% (pi)': 'Cutter',
            'SL% (pi)': 'Slider',
            'CH% (pi)': 'Changeup',
            'CU% (pi)': 'Curveball',
            'SI% (pi)': 'Sinker'
        }
        
        total_pitches = 0
        for stat_key, pitch_name in pitch_types.items():
            raw_value = stats_row[stat_key]
            if stat_key in stats_row and pd.notna(stats_row[stat_key]):
                pitch_mix[pitch_name] = float(stats_row[stat_key])
                total_pitches += float(stats_row[stat_key])
            else:
                pass
        if total_pitches > 0:
            for pitch_name in pitch_mix:
                pitch_mix[pitch_name] = pitch_mix[pitch_name] / total_pitches
        
        print(f"\nFinal pitch mix for {stats_row['Name']}:")
        print(pitch_mix)
        
        result = {
            'k_per_9': float(stats_row['K/9']) if pd.notna(stats_row['K/9']) else 0.0,
            'ip': float(ip),
            'g': int(g),
            'ip_per_g': float(ip_per_g),
            'pitch_mix': pitch_mix,
            'fg_id': fg_id  # Use the potentially updated fg_id
        }
        
        return result
    except Exception as e:
        print(f"Error getting season stats for ID {fg_id}: {str(e)}")
        return {
            'k_per_9': 0.0,
            'ip': 0.0,
            'g': 0,
            'ip_per_g': 0.0,
            'pitch_mix': {},
            'fg_id': fg_id  # Keep the original fg_id on error
        }

def process_pitcher_stats(pitchers: List[Dict], season: int = 2025) -> pd.DataFrame:
    results = []
    
    for pitcher in pitchers:
        full_name = pitcher['pitcher_name']
        team = pitcher['team']
        
        name_parts = full_name.split()
        if len(name_parts) < 2:
            print(f"Invalid name format: {full_name}")
            continue
            
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        fg_id = resolve_fangraphs_id(first_name, last_name)
        if not fg_id:
            print(f"Could not resolve FanGraphs ID for {full_name}")
            fg_id = -1 
        
        stats = get_season_stats(fg_id, season, pitcher_name=full_name)

        pitcher_record = {
            'pitcher': full_name,
            'team': team,
            'fg_id': stats['fg_id'],  
            'k_per_9': stats['k_per_9'],
            'ip_per_g': stats['ip_per_g'],
            'pitch_mix': stats['pitch_mix']
        }
        
        results.append(pitcher_record)

    df = pd.DataFrame(results)
    
    return df

