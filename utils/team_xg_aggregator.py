"""
Team xG/xGC Aggregator
Calculates team-level expected goals metrics from player match data
"""

import pandas as pd
import numpy as np

def calculate_team_xg_stats(match_data_df):
    """
    Calculate comprehensive team xG/xGC statistics from player match data
    
    Args:
        match_data_df: DataFrame with player match-by-match data
        
    Returns:
        DataFrame with team-level xG/xGC metrics
    """
    
    if match_data_df is None or match_data_df.empty:
        return pd.DataFrame()
    
    # Make a copy to avoid modifying original data
    df = match_data_df.copy()
    
    # Ensure numeric columns
    numeric_cols = ['expected_goals', 'expected_assists', 'expected_goal_involvements', 
                    'expected_goals_conceded', 'was_home', 'round', 'fixture']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Convert boolean columns
    if 'was_home' in df.columns:
        df['was_home'] = df['was_home'].astype(bool)
    
    # ===== CALCULATE TEAM xG (Expected Goals Scored) =====
    # Group by team and match to get total xG per team per match
    team_xg_by_match = df.groupby(['player_team', 'fixture', 'round', 'was_home'], as_index=False).agg({
        'expected_goals': 'sum',
        'expected_assists': 'sum',
        'expected_goal_involvements': 'sum'
    }).rename(columns={
        'player_team': 'team',
        'expected_goals': 'xG',
        'expected_assists': 'xA',
        'expected_goal_involvements': 'xGI'
    })
    
    # ===== CALCULATE TEAM xGC (Expected Goals Conceded) =====
    # For each match, we need to get the opponent's xG
    # Create a mapping of fixture -> team -> opponent xG
    
    xgc_records = []
    
    # Get unique fixtures
    fixtures = df[['fixture', 'round', 'player_team', 'opponent_team', 'was_home']].drop_duplicates()
    
    for _, match_info in fixtures.iterrows():
        team = match_info['player_team']
        opponent = match_info['opponent_team']
        fixture_id = match_info['fixture']
        gameweek = match_info['round']
        was_home = match_info['was_home']
        
        # Get opponent's xG in this fixture (which becomes this team's xGC)
        opponent_matches = df[
            (df['player_team'] == opponent) & 
            (df['fixture'] == fixture_id)
        ]
        
        opponent_xg = opponent_matches['expected_goals'].sum()
        
        xgc_records.append({
            'team': team,
            'fixture': fixture_id,
            'round': gameweek,
            'was_home': was_home,
            'xGC': opponent_xg
        })
    
    xgc_df = pd.DataFrame(xgc_records)
    
    # Merge xG and xGC
    team_match_stats = team_xg_by_match.merge(
        xgc_df, 
        on=['team', 'fixture', 'round', 'was_home'], 
        how='left'
    )
    
    # Fill any missing xGC with 0
    team_match_stats['xGC'] = team_match_stats['xGC'].fillna(0)
    
    # ===== AGGREGATE TO SEASON TOTALS =====
    overall_stats = team_match_stats.groupby('team', as_index=False).agg({
        'fixture': 'count',  # Number of matches
        'xG': 'sum',
        'xA': 'sum',
        'xGI': 'sum',
        'xGC': 'sum'
    }).rename(columns={'fixture': 'matches_played'})
    
    # Calculate averages
    overall_stats['xG_per_match'] = np.where(
        overall_stats['matches_played'] > 0,
        overall_stats['xG'] / overall_stats['matches_played'],
        0
    )
    overall_stats['xGC_per_match'] = np.where(
        overall_stats['matches_played'] > 0,
        overall_stats['xGC'] / overall_stats['matches_played'],
        0
    )
    overall_stats['xGI_per_match'] = np.where(
        overall_stats['matches_played'] > 0,
        overall_stats['xGI'] / overall_stats['matches_played'],
        0
    )
    
    # Calculate xG differential (xG - xGC)
    overall_stats['xG_differential'] = overall_stats['xG'] - overall_stats['xGC']
    overall_stats['xG_differential_per_match'] = overall_stats['xG_per_match'] - overall_stats['xGC_per_match']
    
    # ===== HOME/AWAY SPLITS =====
    home_stats = team_match_stats[team_match_stats['was_home'] == True].groupby('team', as_index=False).agg({
        'fixture': 'count',
        'xG': 'sum',
        'xGC': 'sum',
        'xGI': 'sum'
    }).rename(columns={
        'fixture': 'home_matches',
        'xG': 'xG_home',
        'xGC': 'xGC_home',
        'xGI': 'xGI_home'
    })
    
    home_stats['xG_home_per_match'] = np.where(
        home_stats['home_matches'] > 0,
        home_stats['xG_home'] / home_stats['home_matches'],
        0
    )
    home_stats['xGC_home_per_match'] = np.where(
        home_stats['home_matches'] > 0,
        home_stats['xGC_home'] / home_stats['home_matches'],
        0
    )
    
    away_stats = team_match_stats[team_match_stats['was_home'] == False].groupby('team', as_index=False).agg({
        'fixture': 'count',
        'xG': 'sum',
        'xGC': 'sum',
        'xGI': 'sum'
    }).rename(columns={
        'fixture': 'away_matches',
        'xG': 'xG_away',
        'xGC': 'xGC_away',
        'xGI': 'xGI_away'
    })
    
    away_stats['xG_away_per_match'] = np.where(
        away_stats['away_matches'] > 0,
        away_stats['xG_away'] / away_stats['away_matches'],
        0
    )
    away_stats['xGC_away_per_match'] = np.where(
        away_stats['away_matches'] > 0,
        away_stats['xGC_away'] / away_stats['away_matches'],
        0
    )
    
    # Merge all stats
    final_stats = overall_stats.merge(home_stats, on='team', how='left')
    final_stats = final_stats.merge(away_stats, on='team', how='left')
    
    # Fill NaN values with 0
    numeric_columns = final_stats.select_dtypes(include=[np.number]).columns
    final_stats[numeric_columns] = final_stats[numeric_columns].fillna(0)
    
    # Add team short names from the original data
    if 'player_team_short' in df.columns:
        team_short_names = df[['player_team', 'player_team_short']].drop_duplicates()
        team_short_names.columns = ['team', 'short_name']
        final_stats = final_stats.merge(team_short_names, on='team', how='left')
    else:
        # If no short names available, just use the team name
        final_stats['short_name'] = final_stats['team'].str[:3].str.upper()
    
    # Reorder columns for better readability
    column_order = [
        'team', 'short_name', 'matches_played',
        # Overall
        'xG', 'xGC', 'xGI', 'xG_differential',
        'xG_per_match', 'xGC_per_match', 'xGI_per_match', 'xG_differential_per_match',
        # Home
        'home_matches', 'xG_home', 'xGC_home', 'xGI_home',
        'xG_home_per_match', 'xGC_home_per_match',
        # Away
        'away_matches', 'xG_away', 'xGC_away', 'xGI_away',
        'xG_away_per_match', 'xGC_away_per_match'
    ]
    
    # Only include columns that exist
    column_order = [col for col in column_order if col in final_stats.columns]
    final_stats = final_stats[column_order]
    
    return final_stats


def create_team_xg_leaderboard(team_xg_stats, metric='xG_per_match', ascending=False, top_n=20):
    """
    Create a leaderboard sorted by a specific metric
    
    Args:
        team_xg_stats: DataFrame with team xG statistics
        metric: Column to sort by
        ascending: Sort order
        top_n: Number of teams to show
        
    Returns:
        Sorted DataFrame
    """
    if team_xg_stats.empty or metric not in team_xg_stats.columns:
        return team_xg_stats
    
    return team_xg_stats.sort_values(metric, ascending=ascending).head(top_n).reset_index(drop=True)