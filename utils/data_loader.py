"""
Data loader utility for FPL Dashboard
Loads preprocessed data from CSV files
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os

DATA_DIR = Path(__file__).parent.parent / "data"

def check_data_exists():
    """Check if required data files exist"""
    required_files = [
        'enhanced_player_aggregation.csv',
        'team_defensive_analysis.csv',
        'team_attacking_analysis.csv'
    ]
    
    if not DATA_DIR.exists():
        return False
    
    for file in required_files:
        if not (DATA_DIR / file).exists():
            return False
    
    return True

def load_player_data():
    """Load enhanced player aggregation data"""
    file_path = DATA_DIR / 'enhanced_player_aggregation.csv'
    
    if not file_path.exists():
        return None
    
    df = pd.read_csv(file_path)
    
    # Ensure numeric columns are properly typed
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    return df

def load_match_data():
    """Load per-match player data if available"""
    file_path = DATA_DIR / 'fpl_match_data.csv'
    
    if not file_path.exists():
        return None
    
    df = pd.read_csv(file_path)
    
    # Ensure numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    return df

def load_team_data():
    """Load team defensive and attacking analysis"""
    defensive_path = DATA_DIR / 'team_defensive_analysis.csv'
    attacking_path = DATA_DIR / 'team_attacking_analysis.csv'
    
    defensive_df = None
    attacking_df = None
    
    if defensive_path.exists():
        defensive_df = pd.read_csv(defensive_path)
    
    if attacking_path.exists():
        attacking_df = pd.read_csv(attacking_path)
    
    return defensive_df, attacking_df

def load_fpl_data():
    """Load all FPL data"""
    player_data = load_player_data()
    match_data = load_match_data()
    team_defensive, team_attacking = load_team_data()
    
    if player_data is None:
        return None
    
    return {
        'player_data': player_data,
        'match_data': match_data,
        'team_defensive': team_defensive,
        'team_attacking': team_attacking
    }

def get_player_list(df, position=None, min_minutes=0):
    """Get list of player names filtered by position and minutes"""
    if position and position != "All":
        df = df[df['position'] == position]
    
    if min_minutes > 0:
        df = df[df['total_minutes'] >= min_minutes]
    
    return sorted(df['full_name'].unique())

def get_position_list(df):
    """Get list of unique positions"""
    return sorted(df['position'].unique())

def download_fpl_data():
    """Download data with Understat integration"""
    scraper = ComprehensiveFPLScraper()
    scraper.initialize_mappings()
    
    # Use the new method
    df = scraper.scrape_with_understat()
    
    # Scrape team data
    scraper.scrape_team_stats()
    
    return df
