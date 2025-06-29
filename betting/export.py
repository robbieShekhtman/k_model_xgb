import pandas as pd
from typing import List, Dict
from datetime import datetime
import os

def prepare_dataframe(results: List[Dict]) -> pd.DataFrame:

    df = pd.DataFrame(results)
    columns = [
        "pitcher", "team", "opponent", "game_time", "home_away",
        "projected_k", "book_line", "edge_pct", "confidence_pct", "recommendation"
    ]
    
    for col in columns:
        if col not in df.columns:
            if col == "game_time":
                df[col] = None
            elif col == "home_away":
                df[col] = "Unknown"
            else:
                df[col] = 0.0
    
    df = df[columns]
    
    df = df.sort_values("edge_pct", key=abs, ascending=False)

    df["projected_k"] = df["projected_k"].round(1)
    df["book_line"] = df["book_line"].round(1)
    df["edge_pct"] = df["edge_pct"].round(1)
    df["confidence_pct"] = df["confidence_pct"].round(1)
    
    return df

def export_results(
    results: List[Dict],
    export_type: str = "excel",
    date: str = None
) -> None:
    df = prepare_dataframe(results)
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    if export_type.lower() == "excel":
        os.makedirs("exports", exist_ok=True)
        
        filename = f"exports/strikeout_model_{date}.xlsx"
        df.to_excel(filename, index=False)
        print(f"\nExported results to {filename}")
        
    elif export_type.lower() == "sheets":
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from google.oauth2 import service_account
            
            # TODO: Implement Google Sheets export
            # This requires setting up Google API credentials
            print("\nGoogle Sheets export not yet implemented")
            print("Please use Excel export for now")
            
        except ImportError:
            print("\nGoogle Sheets export requires additional packages:")
            print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            print("\nPlease use Excel export for now")
    
    else:
        raise ValueError(f"Unsupported export type: {export_type}")

def print_results(results: List[Dict]) -> None:
    df = prepare_dataframe(results)
    print("\nStrikeout Projections")
    print("=" * 80)

    for _, row in df.iterrows():
        print(f"\n{row['pitcher']} ({row['team']} vs {row['opponent']})")
        print(f"Projected Ks: {row['projected_k']} | Book Line: {row['book_line']}")
        print(f"Edge: {row['edge_pct']}% | Confidence: {row['confidence_pct']}%")
        print(f"Recommendation: {row['recommendation']}")
        if pd.notna(row['game_time']):
            print(f"Game Time: {row['game_time']}")
        print("-" * 40)
