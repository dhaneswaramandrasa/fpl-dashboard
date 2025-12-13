"""
Scraper utility for FPL Dashboard
Fetches data from FPL API and processes it
"""

import requests
import pandas as pd
import numpy as np
from pathlib import Path
import time
from typing import Dict, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

class FPLDataScraper:
    """Scrapes and processes FPL data"""
    
    def __init__(self):
        self.fpl_base_url = "https://fantasy.premierleague.com/api/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.teams = {}
        self.players = {}
    
    def get_bootstrap_data(self) -> Dict:
        """Fetch main FPL bootstrap data"""
        url = f"{self.fpl_base_url}bootstrap-static/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def initialize_mappings(self):
        """Initialize team and player mappings"""
        data = self.get_bootstrap_data()
        
        # Create team mapping
        self.teams = {team['id']: {
            'name': team['name'],
            'short_name': team['short_name']
        } for team in data['teams']}
        
        # Create player mapping
        positions = {pos['id']: pos['singular_name_short'] for pos in data['element_types']}
        
        self.players = {}
        for player in data['elements']:
            self.players[player['id']] = {
                'id': player['id'],
                'name': player['web_name'],
                'full_name': f"{player['first_name']} {player['second_name']}",
                'team': self.teams[player['team']]['name'],
                'team_short': self.teams[player['team']]['short_name'],
                'position': positions[player['element_type']],
                'price': player['now_cost'] / 10
            }
        
        return data
    
    def get_player_match_history(self, player_id: int) -> pd.DataFrame:
        """Get match-by-match history for a specific player"""
        url = f"{self.fpl_base_url}element-summary/{player_id}/"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'history' in data and data['history']:
                df = pd.DataFrame(data['history'])
                
                # Convert numeric columns immediately
                numeric_cols = ['minutes', 'total_points', 'goals_scored', 'assists',
                               'expected_goals', 'expected_assists', 'expected_goal_involvements',
                               'clean_sheets', 'goals_conceded', 'bonus', 'bps', 'saves',
                               'penalties_saved', 'penalties_missed', 'yellow_cards', 'red_cards',
                               'influence', 'creativity', 'threat', 'ict_index', 'starts', 'round']
                
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                # Add player info
                player_info = self.players[player_id]
                df['player_id'] = player_id
                df['player_name'] = player_info['name']
                df['full_name'] = player_info['full_name']
                df['player_team'] = player_info['team']
                df['player_team_short'] = player_info['team_short']
                df['position'] = player_info['position']
                df['player_price'] = player_info['price']
                
                return df
        except Exception as e:
            if "404" not in str(e):
                print(f"Error fetching player {player_id}: {e}")
        
        return pd.DataFrame()
    
    def scrape_player_data(self, max_players: Optional[int] = None) -> pd.DataFrame:
        """Scrape match data for all players"""
        print("Fetching player match data...")
        
        player_ids = list(self.players.keys())
        if max_players:
            player_ids = player_ids[:max_players]
        
        all_match_data = []
        total = len(player_ids)
        
        for i, player_id in enumerate(player_ids):
            if (i + 1) % 50 == 0:
                print(f"Progress: {i + 1}/{total} players ({(i+1)/total*100:.1f}%)")
                time.sleep(1)
            elif (i + 1) % 10 == 0:
                time.sleep(0.2)
            
            match_data = self.get_player_match_history(player_id)
            if not match_data.empty:
                all_match_data.append(match_data)
        
        if all_match_data:
            df = pd.concat(all_match_data, ignore_index=True)
            return df
        
        return pd.DataFrame()
    
    def calculate_rolling_metrics(self, df):
        """Calculate rolling form metrics"""
        def calc_rolling(group, windows=[3, 5, 10]):
            # Ensure numeric columns
            numeric_cols = ['expected_goals', 'expected_assists', 'expected_goal_involvements',
                          'total_points', 'goals_scored', 'assists', 'minutes']
            
            for col in numeric_cols:
                if col in group.columns:
                    group[col] = pd.to_numeric(group[col], errors='coerce').fillna(0)
            
            for window in windows:
                group[f'xG_last_{window}'] = group['expected_goals'].rolling(window, min_periods=1).sum()
                group[f'xA_last_{window}'] = group['expected_assists'].rolling(window, min_periods=1).sum()
                group[f'xGI_last_{window}'] = group['expected_goal_involvements'].rolling(window, min_periods=1).sum()
                group[f'points_last_{window}'] = group['total_points'].rolling(window, min_periods=1).sum()
                group[f'goals_last_{window}'] = group['goals_scored'].rolling(window, min_periods=1).sum()
                group[f'assists_last_{window}'] = group['assists'].rolling(window, min_periods=1).sum()
                group[f'minutes_last_{window}'] = group['minutes'].rolling(window, min_periods=1).sum()
                
                # Per 90 metrics
                group[f'xGI_per90_last_{window}'] = np.where(
                    group[f'minutes_last_{window}'] > 0,
                    group[f'xGI_last_{window}'] * 90 / group[f'minutes_last_{window}'],
                    0
                )
                group[f'points_per90_last_{window}'] = np.where(
                    group[f'minutes_last_{window}'] > 0,
                    group[f'points_last_{window}'] * 90 / group[f'minutes_last_{window}'],
                    0
                )
            return group
        
        df = df.sort_values(['full_name', 'round']).reset_index(drop=True)
        df = df.groupby('full_name', group_keys=False).apply(calc_rolling)
        return df
    
    def aggregate_player_stats(self, df):
        """Aggregate player stats for the season"""
        # Ensure all numeric columns are properly typed
        numeric_cols = ['round', 'starts', 'minutes', 'total_points', 'bonus', 'bps',
                       'goals_scored', 'assists', 'clean_sheets', 'expected_goals',
                       'expected_assists', 'expected_goal_involvements',
                       'xGI_last_5', 'points_last_5', 'goals_last_5', 'assists_last_5',
                       'minutes_last_5', 'xGI_per90_last_5', 'points_per90_last_5']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        season_agg = (
            df.groupby(['full_name', 'position'], as_index=False)
            .agg({
                'round': 'count',
                'starts': 'sum',
                'minutes': 'sum',
                'total_points': 'sum',
                'bonus': 'sum',
                'bps': 'sum',
                'goals_scored': 'sum',
                'assists': 'sum',
                'clean_sheets': 'sum',
                'expected_goals': 'sum',
                'expected_assists': 'sum',
                'expected_goal_involvements': 'sum',
                # Recent form
                'xGI_last_5': 'last',
                'points_last_5': 'last',
                'goals_last_5': 'last',
                'assists_last_5': 'last',
                'minutes_last_5': 'last',
                'xGI_per90_last_5': 'last',
                'points_per90_last_5': 'last',
            })
            .rename(columns={
                'round': 'fixtures_played',
                'minutes': 'total_minutes',
                'expected_goals': 'total_xG',
                'expected_assists': 'total_xA',
                'expected_goal_involvements': 'total_xGI',
            })
        )
        
        # Ensure aggregated columns are numeric
        agg_numeric_cols = ['fixtures_played', 'starts', 'total_minutes', 'total_points',
                           'bonus', 'bps', 'goals_scored', 'assists', 'clean_sheets',
                           'total_xG', 'total_xA', 'total_xGI', 'xGI_last_5',
                           'points_last_5', 'goals_last_5', 'assists_last_5',
                           'minutes_last_5', 'xGI_per90_last_5', 'points_per90_last_5']
        
        for col in agg_numeric_cols:
            if col in season_agg.columns:
                season_agg[col] = pd.to_numeric(season_agg[col], errors='coerce').fillna(0)
        
        # Calculate per 90 metrics - now safe since all columns are numeric
        season_agg['xGI_per90_season'] = np.where(
            season_agg['total_minutes'] > 0,
            season_agg['total_xGI'] * 90 / season_agg['total_minutes'],
            0
        )
        season_agg['points_per90_season'] = np.where(
            season_agg['total_minutes'] > 0,
            season_agg['total_points'] * 90 / season_agg['total_minutes'],
            0
        )
        season_agg['minutes_per_fixture'] = np.where(
            season_agg['fixtures_played'] > 0,
            season_agg['total_minutes'] / season_agg['fixtures_played'],
            0
        )
        
        # Form trends
        season_agg['form_trend_points'] = season_agg['points_per90_last_5'] - season_agg['points_per90_season']
        season_agg['hot_form'] = (season_agg['form_trend_points'] > 1.0) & (season_agg['fixtures_played'] >= 5)
        
        # Overperformance
        season_agg['xG_overperformance'] = season_agg['goals_scored'] - season_agg['total_xG']
        season_agg['xA_overperformance'] = season_agg['assists'] - season_agg['total_xA']
        
        return season_agg
    
    def scrape_team_stats(self):
        """Scrape team defensive and attacking stats"""
        print("Fetching team stats...")
        
        url = f"{self.fpl_base_url}fixtures/"
        response = self.session.get(url)
        response.raise_for_status()
        fixtures = response.json()
        
        fixtures_df = pd.DataFrame(fixtures)
        
        # Add team names
        fixtures_df['team_h_name'] = fixtures_df['team_h'].map(lambda x: self.teams[x]['name'])
        fixtures_df['team_a_name'] = fixtures_df['team_a'].map(lambda x: self.teams[x]['name'])
        fixtures_df['team_h_short'] = fixtures_df['team_h'].map(lambda x: self.teams[x]['short_name'])
        fixtures_df['team_a_short'] = fixtures_df['team_a'].map(lambda x: self.teams[x]['short_name'])
        
        # Convert scores to numeric
        fixtures_df['team_h_score'] = pd.to_numeric(fixtures_df['team_h_score'], errors='coerce').fillna(0)
        fixtures_df['team_a_score'] = pd.to_numeric(fixtures_df['team_a_score'], errors='coerce').fillna(0)
        
        # Get completed fixtures
        completed = fixtures_df[fixtures_df['finished'] == True].copy()
        
        if completed.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Analyze last 6 games for each team
        max_gw = completed['event'].max()
        recent_gws = list(range(max(1, max_gw - 5), max_gw + 1))
        recent_fixtures = completed[completed['event'].isin(recent_gws)]
        
        defensive_stats = []
        attacking_stats = []
        
        for team_id, team_info in self.teams.items():
            home_games = recent_fixtures[recent_fixtures['team_h'] == team_id]
            away_games = recent_fixtures[recent_fixtures['team_a'] == team_id]
            all_games = len(home_games) + len(away_games)
            
            if all_games == 0:
                continue
            
            # Defensive stats
            goals_conceded = float(home_games['team_a_score'].sum() + away_games['team_h_score'].sum())
            clean_sheets = int((home_games['team_a_score'] == 0).sum() + (away_games['team_h_score'] == 0).sum())
            
            defensive_stats.append({
                'team': team_info['name'],
                'short_name': team_info['short_name'],
                'games_played': all_games,
                'goals_conceded': goals_conceded,
                'goals_conceded_per_game': round(goals_conceded / all_games, 2),
                'clean_sheets': clean_sheets,
                'clean_sheet_%': round(clean_sheets / all_games * 100, 1),
            })
            
            # Attacking stats
            goals_scored = float(home_games['team_h_score'].sum() + away_games['team_a_score'].sum())
            
            attacking_stats.append({
                'team': team_info['name'],
                'short_name': team_info['short_name'],
                'games_played': all_games,
                'goals_scored': goals_scored,
                'goals_per_game': round(goals_scored / all_games, 2),
            })
        
        defensive_df = pd.DataFrame(defensive_stats).sort_values('goals_conceded_per_game', ascending=False)
        attacking_df = pd.DataFrame(attacking_stats).sort_values('goals_per_game', ascending=False)
        
        return defensive_df, attacking_df

def scrape_all_data():
    """Main function to scrape all FPL data"""
    scraper = FPLDataScraper()
    
    # Initialize
    print("Initializing FPL data scraper...")
    scraper.initialize_mappings()
    
    # Scrape player match data
    match_df = scraper.scrape_player_data()
    
    if not match_df.empty:
        # Calculate rolling metrics
        print("Calculating rolling metrics...")
        match_df = scraper.calculate_rolling_metrics(match_df)
        
        # Aggregate season stats
        print("Aggregating season stats...")
        player_df = scraper.aggregate_player_stats(match_df)
        
        # Save match data
        match_df.to_csv(DATA_DIR / 'fpl_match_data.csv', index=False)
        print(f"✅ Saved match data: {len(match_df)} records")
        
        # Save player aggregation
        player_df.to_csv(DATA_DIR / 'enhanced_player_aggregation.csv', index=False)
        print(f"✅ Saved player data: {len(player_df)} players")
    
    # Scrape team stats
    defensive_df, attacking_df = scraper.scrape_team_stats()
    
    if not defensive_df.empty:
        defensive_df.to_csv(DATA_DIR / 'team_defensive_analysis.csv', index=False)
        print(f"✅ Saved defensive stats: {len(defensive_df)} teams")
    
    if not attacking_df.empty:
        attacking_df.to_csv(DATA_DIR / 'team_attacking_analysis.csv', index=False)
        print(f"✅ Saved attacking stats: {len(attacking_df)} teams")
    
    print("\n✅ Data scraping complete!")
    return True
