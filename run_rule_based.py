from typing import Optional
from scipy.stats import norm

from features.pitchers import fetch_pitchers
from features.pitchers import process_pitcher_stats
from features.batters import get_opposing_lineups
from features.batters import analyze_matchup
from features.contextual import apply_contextual_adjustments
from betting.betting_lines import get_strikeout_props
from betting.export import export_results
from betting.filters import filter_bets, get_bet_summary, print_filtered_bets
from features.rule_based import project_strikeouts_with_lineup_fetching


def run_daily_analysis(date: Optional[str] = None) -> None:
    """
    Run the complete daily analysis pipeline.
    
    Args:
        date (Optional[str]): Date to analyze in YYYY-MM-DD format. If None, uses today's date.
    """
    try:
        pitchers = fetch_pitchers()
        if not pitchers:
            print("No pitchers found for today's games")
            return

        print("Processing pitcher statistics...")
        pitcher_stats = process_pitcher_stats(pitchers)
        
        pitchers_with_stats = []
        for _, row in pitcher_stats.iterrows():
            original_pitcher = next((p for p in pitchers if p['pitcher_name'] == row['pitcher']), None)
            if original_pitcher:
                pitcher_with_stats = {
                    'pitcher_name': row['pitcher'],
                    'team': row['team'],
                    'opponent': original_pitcher['opponent'],
                    'stats': {
                        'k_per_9': row['k_per_9'],
                        'ip_per_g': row['ip_per_g'],
                        'pitch_mix': row['pitch_mix']
                    }
                }
                pitchers_with_stats.append(pitcher_with_stats)
        
        print("Pitchers with stats:", pitchers_with_stats)
        
        print("Fetching opposing lineups...")
        lineup_map = get_opposing_lineups(pitchers_with_stats, date)
        
        print("Analyzing pitcher-batter matchups...")
        matchup_scores = {}
        for pitcher in pitchers_with_stats:
            if pitcher['pitcher_name'] in lineup_map:
                matchup = analyze_matchup(pitcher, lineup_map[pitcher['pitcher_name']])
                if matchup:
                    matchup_scores[pitcher['pitcher_name']] = {
                        'agg_lineup_score': matchup['agg_lineup_score'],
                        'lineup': lineup_map[pitcher['pitcher_name']]
                    }
        
        print("Fetching betting lines...")
        betting_lines = get_strikeout_props(date)
        print("Betting lines:", betting_lines)
        
        print("Projecting strikeouts using enhanced model...")
        projections = []
        for pitcher in pitchers_with_stats:
            betting_line = next(
                (line['line'] for line in betting_lines 
                 if line['pitcher'] == pitcher['pitcher_name'] 
                 and line['team'] == pitcher['team']),
                None
            )
            
            if betting_line is None:
                print(f"No betting line found for {pitcher['pitcher_name']}")
                continue
            
            try:
                projected_k = project_strikeouts_with_lineup_fetching(
                    pitcher_info=pitcher,
                    date=date
                )
                
                edge_pct = round(((projected_k - betting_line) / 1.5) * 100, 1)
                z = (projected_k - betting_line) / 1.5
                confidence_pct = round(
                    100 * (norm.cdf(z) if projected_k > betting_line else 1 - norm.cdf(z)),
                    1
                )
                
                if edge_pct > 7 and confidence_pct >= 70:
                    recommendation = "Bet Over"
                elif edge_pct < -7 and confidence_pct >= 70:
                    recommendation = "Bet Under"
                else:
                    recommendation = "Skip"
                
                lineup_details = matchup_scores.get(pitcher['pitcher_name'], {}).get('lineup', [])
                
                projection = {
                    "pitcher": pitcher["pitcher_name"],
                    "team": pitcher["team"],
                    "opponent": pitcher["opponent"],
                    "projected_k": round(projected_k, 1),
                    "book_line": betting_line,
                    "edge_pct": edge_pct,
                    "confidence_pct": confidence_pct,
                    "recommendation": recommendation,
                    "details": {
                        "matchup_score": matchup_scores.get(pitcher['pitcher_name'], {}).get('agg_lineup_score', 0),
                        "lineup": lineup_details,
                        "model": "Enhanced Projection (Hitter Z-Scores + Pitcher K% + Pitch Quality + IP Adjustment)"
                    }
                }
                
                projections.append(projection)
                
            except Exception as e:
                print(f"Error projecting strikeouts for {pitcher['pitcher_name']}: {str(e)}")
                continue
        
        print("Applying contextual adjustments...")
        adjusted_projections = []
        for proj in projections:
            adjusted = apply_contextual_adjustments(
                pitcher={
                    'name': proj['pitcher'],
                    'team': proj['team'],
                    'opponent': proj['opponent'],
                    'home_away': 'Home' if proj.get('is_home', False) else 'Away'
                },
                raw_k=proj['projected_k']
            )
            proj['projected_k'] = adjusted['adjusted_k']
            adjusted_projections.append(proj)
        
        print("Filtering betting opportunities...")
        filtered_bets = filter_bets(adjusted_projections)
        bet_summary = get_bet_summary(filtered_bets)
        
        print("Exporting results...")
        export_results(adjusted_projections)
        
        print_filtered_bets(filtered_bets, bet_summary)
        
        print("Daily analysis complete!")
        
    except Exception as e:
        print(f"Error in daily analysis: {str(e)}")
        raise

def main():
    try:
        run_daily_analysis()
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        raise 

if __name__ == "__main__":
    main()
