from typing import List, Dict, Optional
from datetime import datetime

def filter_bets(
    results: List[Dict],
    edge_thresh: float = 7.0,
    conf_thresh: float = 70.0,
    direction: Optional[str] = None
) -> List[Dict]:

    if not results:
        return []
    

    filtered = []
    for r in results:

        if r.get("confidence_pct", 0) < conf_thresh:
            continue
            

        edge = r.get("edge_pct", 0)
        

        if direction == "over" and edge <= edge_thresh:
            continue
        elif direction == "under" and edge >= -edge_thresh:
            continue
        elif direction is None and abs(edge) <= edge_thresh:
            continue
            
        filtered.append(r)

    filtered.sort(key=lambda x: abs(x.get("edge_pct", 0)), reverse=True)
    
    return filtered

def get_bet_summary(filtered_bets: List[Dict]) -> Dict:
    if not filtered_bets:
        return {
            "total_bets": 0,
            "avg_edge": 0.0,
            "avg_confidence": 0.0,
            "over_bets": 0,
            "under_bets": 0
        }

    total_bets = len(filtered_bets)
    avg_edge = sum(bet.get("edge_pct", 0) for bet in filtered_bets) / total_bets
    avg_confidence = sum(bet.get("confidence_pct", 0) for bet in filtered_bets) / total_bets

    over_bets = sum(1 for bet in filtered_bets if bet.get("edge_pct", 0) > 0)
    under_bets = total_bets - over_bets
    
    return {
        "total_bets": total_bets,
        "avg_edge": round(avg_edge, 1),
        "avg_confidence": round(avg_confidence, 1),
        "over_bets": over_bets,
        "under_bets": under_bets
    }

def print_filtered_bets(filtered_bets: List[Dict], summary: Dict) -> None:
    print("\nTop Betting Opportunities")
    print("=" * 80)
    

    print(f"\nSummary:")
    print(f"Total Bets: {summary['total_bets']}")
    print(f"Average Edge: {summary['avg_edge']}%")
    print(f"Average Confidence: {summary['avg_confidence']}%")
    print(f"Over Bets: {summary['over_bets']}")
    print(f"Under Bets: {summary['under_bets']}")

    print("\nDetailed Picks:")
    for bet in filtered_bets:
        print(f"\n{bet['pitcher']} ({bet['team']} vs {bet['opponent']})")
        print(f"Projected Ks: {bet['projected_k']} | Book Line: {bet['book_line']}")
        print(f"Edge: {bet['edge_pct']}% | Confidence: {bet['confidence_pct']}%")
        print(f"Recommendation: {bet['recommendation']}")
        if "game_time" in bet:
            print(f"Game Time: {bet['game_time']}")
        print("-" * 40)

