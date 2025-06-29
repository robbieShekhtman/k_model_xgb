from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from scipy.stats import zscore
from pybaseball import batting_stats, pitching_stats
from datetime import datetime
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from features.batters import get_opposing_lineups
from features.batters import get_batter_stats, calculate_matchup_score



def fuzzy_name_match(target_name: str, name_list: List[str], cutoff: float = 90) -> Optional[str]:
    if not name_list or not target_name:
        return None
    if target_name in name_list:
        return target_name
    best_match = process.extractOne(target_name, name_list, scorer=fuzz.token_sort_ratio)
    
    if best_match and best_match[1] >= cutoff:
        print(f"Found fuzzy match: {best_match[0]} with score {best_match[1]}")
        return best_match[0]
    
    return None

def get_hitter_z_scores(season: int = None) -> pd.DataFrame:
    if season is None:
        season = datetime.now().year
    
    hitters = batting_stats(start_season=season, end_season=season, qual=0)
    
    hitters['wOBA'] = hitters['wOBA'].fillna(hitters['wOBA'].mean())
    hitters['K%'] = hitters['SO'] / hitters['PA']
    
    metrics = ['wOBA', 'K%', 'SLG', 'ISO']
    for metric in metrics:
        hitters[f'{metric}_z'] = zscore(hitters[metric].fillna(hitters[metric].mean()))
 
    hitters['susceptibility_score'] = (
        0.7 * hitters['K%_z'] +      
        0.2 * (-hitters['wOBA_z']) + 
        0.1 * hitters['ISO_z']       
    )
    
    hitters['susceptibility_z'] = zscore(hitters['susceptibility_score'])
    
    return hitters[['Name', 'susceptibility_z']]

def get_pitcher_k_factor(pitcher_name: str, season: int = None) -> float:
    if season is None:
        season = datetime.now().year
        
    pitchers = pitching_stats(season, qual=1)
    
    pitchers['K%'] = (pitchers['SO'] * 9) / (pitchers['IP'] * 9 + pitchers['BB'] + pitchers['H'])
    
    pitchers['K%_z'] = zscore(pitchers['K%'].fillna(pitchers['K%'].mean()))
    
    pitcher_names = pitchers['Name'].tolist()
    matched_name = fuzzy_name_match(pitcher_name, pitcher_names)
    
    if matched_name:
        pitcher = pitchers[pitchers['Name'] == matched_name]
        if not pitcher.empty:
            return float(pitcher['K%_z'].iloc[0])
    
    raise ValueError(f"Pitcher '{pitcher_name}' not found in pitching data. Available pitchers: {len(pitcher_names)}")

def get_pitch_quality_score(pitcher_name: str) -> float:
    try:
        season = datetime.now().year
        
        pitchers = pitching_stats(season, qual=1)

        pitcher_names = pitchers['Name'].tolist()
        matched_name = fuzzy_name_match(pitcher_name, pitcher_names)
        
        if not matched_name:
            raise ValueError(f"Pitcher '{pitcher_name}' not found in pitching data")
        
        pitcher = pitchers[pitchers['Name'] == matched_name]
        
        if pitcher.empty:
            raise ValueError(f"No data found for {pitcher_name}")
            
        stuff_plus = float(pitcher['Stuff+'].iloc[0])
        location_plus = float(pitcher['Location+'].iloc[0])
        
        stuff_score = (stuff_plus - 100) / 20 
        location_score = (location_plus - 100) / 20

        quality_score = (0.6 * stuff_score) + (0.4 * location_score)
        
        quality_score = max(min(quality_score, 1.0), -1.0)
        
        return quality_score
        
    except Exception as e:
        raise

def calculate_ip_adjustment(pitcher_name: str, lineup_woba: float, season: int = None) -> float:
    if season is None:
        season = datetime.now().year
        
    pitchers = pitching_stats(season, qual=1)
    
    pitcher_names = pitchers['Name'].tolist()
    matched_name = fuzzy_name_match(pitcher_name, pitcher_names)
    
    if not matched_name:
        raise ValueError(f"Pitcher '{pitcher_name}' not found in pitching data")
    
    pitcher = pitchers[pitchers['Name'] == matched_name]
    
    if pitcher.empty:
        raise ValueError(f"No data found for {pitcher_name}")
    
    league_woba = 0.320  

    base_ip = float(pitcher['IP'].iloc[0] / pitcher['G'].iloc[0])
    beta = 0.02  
    
    woba_diff = lineup_woba - league_woba
    ip_adj = base_ip * (1 - beta * woba_diff)
    
    return ip_adj

def get_lineup_woba(lineup: List[str], season: int = None):
    if season is None:
        season = datetime.now().year
    
    batting_stats_df = batting_stats(start_season=season, end_season=season, qual=0)
    
    found_players = []
    for player in lineup:
        matched_name = fuzzy_name_match(player, batting_stats_df['Name'].tolist())
        if matched_name:
            player_data = batting_stats_df[batting_stats_df['Name'] == matched_name]
            if not player_data.empty:
                found_players.append(float(player_data['wOBA'].iloc[0]))
    
    if not found_players:
        raise ValueError(f"No players found in lineup: {lineup}")
    
    return np.mean(found_players)

def project_strikeouts(
    pitcher_name: str,
    lineup: List[str],
    season: int = None,
    alpha: float = 0.06,
    gamma: float = 0.02
):
    if season is None:
        season = datetime.now().year

    hitters = get_hitter_z_scores(season)

    found_scores = []
    for player in lineup:
        matched_name = fuzzy_name_match(player, hitters['Name'].tolist())
        if matched_name:
            player_data = hitters[hitters['Name'] == matched_name]
            if not player_data.empty:
                found_scores.append(float(player_data['susceptibility_z'].iloc[0]))
    
    if len(found_scores) == 0:
        raise ValueError(f"No players found in lineup: {lineup}")
    
    lineup_z = np.mean(found_scores)
    
    k_z = get_pitcher_k_factor(pitcher_name, season)
    
    matchup_factor = 1 + (lineup_z - k_z) * alpha
    pitch_mix_score = calculate_pitch_mix_matchup_score(pitcher_name, lineup, season)
    
    combined_matchup_factor = (0.65 * (1 + pitch_mix_score * 0.2)) + (0.35 * matchup_factor)
    
    try:
        lineup_woba = get_lineup_woba(lineup, season)
    except Exception as e:
        print(f"ERROR: Could not get lineup wOBA: {str(e)}")
        raise
    
    estimated_ip = calculate_ip_adjustment(pitcher_name, lineup_woba, season) # pyright: ignore[reportArgumentType]
    
    try:
        pitchers = pitching_stats(season, qual=1)
        pitcher_names = pitchers['Name'].tolist()
        matched_name = fuzzy_name_match(pitcher_name, pitcher_names)
        
        if not matched_name:
            raise ValueError(f"Pitcher '{pitcher_name}' not found in pitching data")
        
        pitcher = pitchers[pitchers['Name'] == matched_name]
        
        if pitcher.empty:
            raise ValueError(f"No data found for {pitcher_name}")
        
        k_per_9 = float(pitcher['SO'].iloc[0] * 9 / pitcher['IP'].iloc[0])
        
    except Exception as e:
        raise
    
    base_strikeouts = (k_per_9 * estimated_ip) / 9
    core_projection = base_strikeouts * combined_matchup_factor
    
    quality_score = get_pitch_quality_score(pitcher_name)
    final_proj = core_projection * (1 + gamma * quality_score)
    
    return round(final_proj, 1)

def project_strikeouts_with_lineup_fetching(
    pitcher_info: Dict,
    date: str = None,
    season: int = None,
    alpha: float = 0.15,
    gamma: float = 0.15
):
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    if season is None:
        season = datetime.now().year
    
    pitcher_name = pitcher_info['pitcher_name']
    opponent = pitcher_info['opponent']
    
    lineup_map = get_opposing_lineups([pitcher_info], date)
    
    if pitcher_name not in lineup_map:
        raise ValueError(f"No lineup found for {pitcher_name} on {date}")
    
    lineup_data = lineup_map[pitcher_name]
    lineup = [player['name'] for player in lineup_data]
    
    
    projection = project_strikeouts(pitcher_name, lineup, season, alpha, gamma)
    
    projection *= 1.05 
    
    return round(projection, 1)

def get_pitcher_pitch_mix(pitcher_name: str, season: int = None) -> Dict:
    if season is None:
        season = datetime.now().year

    pitchers = pitching_stats(season, qual=1)
    
    pitcher_names = pitchers['Name'].tolist()
    matched_name = fuzzy_name_match(pitcher_name, pitcher_names)
    
    if not matched_name:
        raise ValueError(f"Pitcher '{pitcher_name}' not found in pitching data")
    
    pitcher = pitchers[pitchers['Name'] == matched_name]
    
    if pitcher.empty:
        raise ValueError(f"No data found for {pitcher_name}")
    
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
        if stat_key in pitcher.columns and pd.notna(pitcher[stat_key].iloc[0]):
            pitch_mix[pitch_name] = float(pitcher[stat_key].iloc[0])
            total_pitches += float(pitcher[stat_key].iloc[0])
    
    if total_pitches > 0:
        for pitch_name in pitch_mix:
            pitch_mix[pitch_name] = pitch_mix[pitch_name] / total_pitches
    
    return pitch_mix

def calculate_pitch_mix_matchup_score(pitcher_name: str, lineup: List[str], season: int = None):
    if get_batter_stats is None or calculate_matchup_score is None:
        print("Warning: Pitch mix analysis not available, returning 0")
        return 0.0
    
    if season is None:
        season = datetime.now().year
    
    try:
        pitch_mix = get_pitcher_pitch_mix(pitcher_name, season)
        
        if not pitch_mix:
            return 0.0

        matchup_scores = []
        for batter_name in lineup:
            try:
                batter_stats = get_batter_stats(batter_name, season)
                if not batter_stats or 'pitch_metrics' not in batter_stats:
                    continue
                
                matchup_score = calculate_matchup_score(batter_stats, pitch_mix)
                matchup_scores.append(matchup_score)
                
                
            except Exception as e:
                continue
        
        if not matchup_scores:
            return 0.0
        
        avg_score = np.mean(matchup_scores)
        return avg_score
        
    except Exception as e:
        print(f"Error calculating pitch mix matchup: {e}")
        return 0.0
