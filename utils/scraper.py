"""
Comprehensive Enhanced FPL Data Scraper
Includes:
- npXG (Non-Penalty Expected Goals)
- Defensive Contribution metrics
- BPS/90 and Bonus/90
- Home/Away form splits
- Start percentage
- All available FPL API fields
"""

import requests
import pandas as pd
import numpy as np
from pathlib import Path
import time
from typing import Dict, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

class ComprehensiveFPLScraper:
    """Comprehensive scraper with all available FPL metrics"""
    
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
        """Get comprehensive match-by-match history"""
        url = f"{self.fpl_base_url}element-summary/{player_id}/"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'history' in data and data['history']:
                df = pd.DataFrame(data['history'])
                
                # Convert ALL numeric columns
                numeric_cols = [
                    'element', 'fixture', 'opponent_team', 'total_points', 'was_home',
                    'team_h_score', 'team_a_score', 'round', 'minutes', 'goals_scored',
                    'assists', 'clean_sheets', 'goals_conceded', 'own_goals',
                    'penalties_saved', 'penalties_missed', 'yellow_cards', 'red_cards',
                    'saves', 'bonus', 'bps', 'influence', 'creativity', 'threat',
                    'ict_index', 'starts', 'expected_goals', 'expected_assists',
                    'expected_goal_involvements', 'expected_goals_conceded', 'value',
                    'transfers_balance', 'selected', 'transfers_in', 'transfers_out',
                    # NEW: Defensive stats
                    'clearances_blocks_interceptions', 'recoveries', 'tackles',
                    'defensive_contribution'
                ]
                
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
                
                # Add opponent info
                if 'opponent_team' in df.columns:
                    df['opponent_team_id'] = df['opponent_team']
                    df['opponent_team'] = df['opponent_team'].map(
                        lambda x: self.teams[x]['name'] if x in self.teams else 'Unknown'
                    )
                    df['opponent_short'] = df['opponent_team_id'].map(
                        lambda x: self.teams[x]['short_name'] if x in self.teams else 'UNK'
                    )
                
                # Add venue
                if 'was_home' in df.columns:
                    df['venue'] = df['was_home'].map({True: 'Home', False: 'Away', 1: 'Home', 0: 'Away'})
                
                # === CALCULATE npXG (Non-Penalty Expected Goals) ===
                df['estimated_penalties'] = 0.0
                
                if 'expected_goals' in df.columns and 'goals_scored' in df.columns:
                    # Estimate penalties using xG heuristic
                    for idx, row in df.iterrows():
                        if row['goals_scored'] >= 1 and row['expected_goals'] >= 0.70:
                            if row['expected_goals'] < 1.5:
                                df.at[idx, 'estimated_penalties'] = 1.0
                            elif row['goals_scored'] > 1:
                                possible_pens = min(row['goals_scored'], int(row['expected_goals'] / 0.76))
                                df.at[idx, 'estimated_penalties'] = min(possible_pens, row['goals_scored'])
                
                # Calculate npXG metrics
                df['npxG'] = df['expected_goals'] - (df['estimated_penalties'] * 0.76)
                df['npxG'] = df['npxG'].clip(lower=0)
                df['npxA'] = df['expected_assists']
                df['npxGI'] = df['npxG'] + df['npxA']
                
                # === PER 90 CALCULATIONS ===
                # Avoid division by zero
                df['minutes_safe'] = df['minutes'].replace(0, 1)
                
                # Standard per 90
                df['points_per90'] = (df['total_points'] / df['minutes_safe']) * 90
                df['xG_per90'] = (df['expected_goals'] / df['minutes_safe']) * 90
                df['xA_per90'] = (df['expected_assists'] / df['minutes_safe']) * 90
                df['xGI_per90'] = (df['expected_goal_involvements'] / df['minutes_safe']) * 90
                
                # npXG per 90
                df['npxG_per90'] = (df['npxG'] / df['minutes_safe']) * 90
                df['npxGI_per90'] = (df['npxGI'] / df['minutes_safe']) * 90
                
                # BPS and Bonus per 90
                df['bps_per90'] = (df['bps'] / df['minutes_safe']) * 90
                df['bonus_per90'] = (df['bonus'] / df['minutes_safe']) * 90
                
                # ICT per 90
                df['influence_per90'] = (df['influence'] / df['minutes_safe']) * 90
                df['creativity_per90'] = (df['creativity'] / df['minutes_safe']) * 90
                df['threat_per90'] = (df['threat'] / df['minutes_safe']) * 90
                
                # Defensive per 90
                if 'defensive_contribution' in df.columns:
                    df['defensive_contribution_per90'] = (df['defensive_contribution'] / df['minutes_safe']) * 90
                if 'tackles' in df.columns:
                    df['tackles_per90'] = (df['tackles'] / df['minutes_safe']) * 90
                if 'clearances_blocks_interceptions' in df.columns:
                    df['clearances_blocks_interceptions_per90'] = (df['clearances_blocks_interceptions'] / df['minutes_safe']) * 90
                if 'recoveries' in df.columns:
                    df['recoveries_per90'] = (df['recoveries'] / df['minutes_safe']) * 90
                
                # Goal involvement
                df['goal_involvements'] = df['goals_scored'] + df['assists']
                df['goal_involvements_per90'] = (df['goal_involvements'] / df['minutes_safe']) * 90
                
                # Overperformance
                df['xG_overperformance'] = df['goals_scored'] - df['expected_goals']
                df['xA_overperformance'] = df['assists'] - df['expected_assists']
                df['npxG_overperformance'] = (df['goals_scored'] - df['estimated_penalties']) - df['npxG']
                
                return df
                
        except Exception as e:
            if "404" not in str(e):
                print(f"Error fetching player {player_id}: {e}")
        
        return pd.DataFrame()
    
    def scrape_player_data(self, max_players: Optional[int] = None) -> pd.DataFrame:
        """Scrape match data for all players"""
        print("Fetching comprehensive player match data...")
        
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
        """Calculate rolling metrics with home/away splits"""
        def calc_rolling(group, windows=[3, 5, 10]):
            # Ensure numeric columns
            numeric_cols = [
                'expected_goals', 'expected_assists', 'expected_goal_involvements',
                'total_points', 'goals_scored', 'assists', 'minutes',
                'npxG', 'npxA', 'npxGI', 'bps', 'bonus',
                'influence', 'creativity', 'threat',
                'defensive_contribution', 'tackles', 'clearances_blocks_interceptions',
                'recoveries', 'starts'
            ]
            
            for col in numeric_cols:
                if col in group.columns:
                    group[col] = pd.to_numeric(group[col], errors='coerce').fillna(0)
            
            # === OVERALL ROLLING METRICS ===
            for window in windows:
                # Core metrics
                group[f'xG_last_{window}'] = group['expected_goals'].rolling(window, min_periods=1).sum()
                group[f'xA_last_{window}'] = group['expected_assists'].rolling(window, min_periods=1).sum()
                group[f'xGI_last_{window}'] = group['expected_goal_involvements'].rolling(window, min_periods=1).sum()
                group[f'points_last_{window}'] = group['total_points'].rolling(window, min_periods=1).sum()
                group[f'goals_last_{window}'] = group['goals_scored'].rolling(window, min_periods=1).sum()
                group[f'assists_last_{window}'] = group['assists'].rolling(window, min_periods=1).sum()
                group[f'minutes_last_{window}'] = group['minutes'].rolling(window, min_periods=1).sum()
                
                # npXG metrics
                if 'npxG' in group.columns:
                    group[f'npxG_last_{window}'] = group['npxG'].rolling(window, min_periods=1).sum()
                    group[f'npxA_last_{window}'] = group['npxA'].rolling(window, min_periods=1).sum()
                    group[f'npxGI_last_{window}'] = group['npxGI'].rolling(window, min_periods=1).sum()
                
                # BPS and Bonus
                if 'bps' in group.columns:
                    group[f'bps_last_{window}'] = group['bps'].rolling(window, min_periods=1).sum()
                if 'bonus' in group.columns:
                    group[f'bonus_last_{window}'] = group['bonus'].rolling(window, min_periods=1).sum()
                
                # ICT components
                if 'influence' in group.columns:
                    group[f'influence_last_{window}'] = group['influence'].rolling(window, min_periods=1).sum()
                    group[f'creativity_last_{window}'] = group['creativity'].rolling(window, min_periods=1).sum()
                    group[f'threat_last_{window}'] = group['threat'].rolling(window, min_periods=1).sum()
                
                # Defensive metrics
                if 'defensive_contribution' in group.columns:
                    group[f'defensive_contribution_last_{window}'] = group['defensive_contribution'].rolling(window, min_periods=1).sum()
                if 'tackles' in group.columns:
                    group[f'tackles_last_{window}'] = group['tackles'].rolling(window, min_periods=1).sum()
                
                # Starts
                if 'starts' in group.columns:
                    group[f'starts_last_{window}'] = group['starts'].rolling(window, min_periods=1).sum()
                
                # Per 90 metrics
                group[f'defensive_contribution_per90_last_{window}'] = np.where(
                    group[f'minutes_last_{window}'] > 0,
                    group[f'defensive_contribution_last_{window}'] * 90 / group[f'minutes_last_{window}'],
                    0
                )

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
                
                if 'npxGI' in group.columns:
                    group[f'npxGI_per90_last_{window}'] = np.where(
                        group[f'minutes_last_{window}'] > 0,
                        group[f'npxGI_last_{window}'] * 90 / group[f'minutes_last_{window}'],
                        0
                    )
                
                if 'bps' in group.columns:
                    group[f'bps_per90_last_{window}'] = np.where(
                        group[f'minutes_last_{window}'] > 0,
                        group[f'bps_last_{window}'] * 90 / group[f'minutes_last_{window}'],
                        0
                    )
                
                if 'bonus' in group.columns:
                    group[f'bonus_per90_last_{window}'] = np.where(
                        group[f'minutes_last_{window}'] > 0,
                        group[f'bonus_last_{window}'] * 90 / group[f'minutes_last_{window}'],
                        0
                    )
            
            return group
        
        df = df.sort_values(['full_name', 'round']).reset_index(drop=True)
        df = df.groupby(['full_name','player_price','player_name','player_team','position'], group_keys=False).apply(calc_rolling)
        return df
    
    def calculate_home_away_splits(self, df):
        """Calculate home and away form separately"""
        
        # Create home/away subsets
        home_df = df[df['venue'] == 'Home'].copy()
        away_df = df[df['venue'] == 'Away'].copy()
        
        # Group by player
        home_stats = home_df.groupby(['full_name','player_price','player_name','player_team','position'], as_index=False).agg({
            'minutes': 'sum',
            'total_points': 'sum',
            'goals_scored': 'sum',
            'assists': 'sum',
            'expected_goals': 'sum',
            'expected_assists': 'sum',
            'expected_goal_involvements': 'sum',
            'npxG': 'sum',
            'npxGI': 'sum',
            'bps': 'sum',
            'bonus': 'sum',
            'defensive_contribution': 'sum',
            'tackles': 'sum',
            'starts': 'sum',
            'round': 'count'  # Number of home games
        }).rename(columns={
            'minutes': 'minutes_home',
            'total_points': 'points_home',
            'goals_scored': 'goals_home',
            'assists': 'assists_home',
            'expected_goals': 'xG_home',
            'expected_assists': 'xA_home',
            'expected_goal_involvements': 'xGI_home',
            'npxG': 'npxG_home',
            'npxGI': 'npxGI_home',
            'bps': 'bps_home',
            'bonus': 'bonus_home',
            'defensive_contribution': 'def_contrib_home',
            'tackles': 'tackles_home',
            'starts': 'starts_home',
            'round': 'games_home'
        })
        
        away_stats = away_df.groupby(['full_name','player_price','player_name','player_team','position'], as_index=False).agg({
            'minutes': 'sum',
            'total_points': 'sum',
            'goals_scored': 'sum',
            'assists': 'sum',
            'expected_goals': 'sum',
            'expected_assists': 'sum',
            'expected_goal_involvements': 'sum',
            'npxG': 'sum',
            'npxGI': 'sum',
            'bps': 'sum',
            'bonus': 'sum',
            'defensive_contribution': 'sum',
            'tackles': 'sum',
            'starts': 'sum',
            'round': 'count'  # Number of away games
        }).rename(columns={
            'minutes': 'minutes_away',
            'total_points': 'points_away',
            'goals_scored': 'goals_away',
            'assists': 'assists_away',
            'expected_goals': 'xG_away',
            'expected_assists': 'xA_away',
            'expected_goal_involvements': 'xGI_away',
            'npxG': 'npxG_away',
            'npxGI': 'npxGI_away',
            'bps': 'bps_away',
            'bonus': 'bonus_away',
            'defensive_contribution': 'def_contrib_away',
            'tackles': 'tackles_away',
            'starts': 'starts_away',
            'round': 'games_away'
        })
        
        # Calculate per 90 for home
        home_stats['points_home_per90'] = np.where(
            home_stats['minutes_home'] > 0,
            home_stats['points_home'] * 90 / home_stats['minutes_home'],
            0
        )
        home_stats['xGI_home_per90'] = np.where(
            home_stats['minutes_home'] > 0,
            home_stats['xGI_home'] * 90 / home_stats['minutes_home'],
            0
        )
        home_stats['npxGI_home_per90'] = np.where(
            home_stats['minutes_home'] > 0,
            home_stats['npxGI_home'] * 90 / home_stats['minutes_home'],
            0
        )
        home_stats['bps_home_per90'] = np.where(
            home_stats['minutes_home'] > 0,
            home_stats['bps_home'] * 90 / home_stats['minutes_home'],
            0
        )
        home_stats['bonus_home_per90'] = np.where(
            home_stats['minutes_home'] > 0,
            home_stats['bonus_home'] * 90 / home_stats['minutes_home'],
            0
        )
        home_stats['def_contrib_home_per90'] = np.where(
            home_stats['minutes_home'] > 0,
            home_stats['def_contrib_home'] * 90 / home_stats['minutes_home'],
            0
        )
        
        # Calculate per 90 for away
        away_stats['points_away_per90'] = np.where(
            away_stats['minutes_away'] > 0,
            away_stats['points_away'] * 90 / away_stats['minutes_away'],
            0
        )
        away_stats['xGI_away_per90'] = np.where(
            away_stats['minutes_away'] > 0,
            away_stats['xGI_away'] * 90 / away_stats['minutes_away'],
            0
        )
        away_stats['npxGI_away_per90'] = np.where(
            away_stats['minutes_away'] > 0,
            away_stats['npxGI_away'] * 90 / away_stats['minutes_away'],
            0
        )
        away_stats['bps_away_per90'] = np.where(
            away_stats['minutes_away'] > 0,
            away_stats['bps_away'] * 90 / away_stats['minutes_away'],
            0
        )
        away_stats['bonus_away_per90'] = np.where(
            away_stats['minutes_away'] > 0,
            away_stats['bonus_away'] * 90 / away_stats['minutes_away'],
            0
        )
        away_stats['def_contrib_away_per90'] = np.where(
            away_stats['minutes_away'] > 0,
            away_stats['def_contrib_away'] * 90 / away_stats['minutes_away'],
            0
        )
        
        return home_stats, away_stats
    
    def aggregate_player_stats(self, df):
        """Aggregate comprehensive player stats"""
        
        # Calculate home/away splits first
        home_stats, away_stats = self.calculate_home_away_splits(df)
        
        # Main season aggregation
        numeric_cols = [
            'round', 'starts', 'minutes', 'total_points', 'bonus', 'bps',
            'goals_scored', 'assists', 'clean_sheets', 'expected_goals',
            'expected_assists', 'expected_goal_involvements',
            'npxG', 'npxA', 'npxGI', 'estimated_penalties',
            'influence', 'creativity', 'threat',
            'defensive_contribution', 'tackles', 'clearances_blocks_interceptions', 'recoveries',
            'xGI_last_5', 'points_last_5', 'goals_last_5', 'assists_last_5',
            'minutes_last_5', 'xGI_per90_last_5', 'points_per90_last_5',
            'npxGI_last_5', 'npxGI_per90_last_5',
            'bps_last_5', 'bps_per90_last_5',
            'bonus_last_5', 'bonus_per90_last_5',
            'defensive_contribution_last_5','defensive_contribution_per90_last_5', 'tackles_last_5',
            'starts_last_5'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        season_agg = (
            df.groupby(['full_name','player_price','player_name','player_team', 'position'], as_index=False)
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
                'npxG': 'sum',
                'npxA': 'sum',
                'npxGI': 'sum',
                'estimated_penalties': 'sum',
                'influence': 'sum',
                'creativity': 'sum',
                'threat': 'sum',
                'defensive_contribution': 'sum',
                'tackles': 'sum',
                'clearances_blocks_interceptions': 'sum',
                'recoveries': 'sum',
                # Recent form
                'xGI_last_5': 'last',
                'points_last_5': 'last',
                'goals_last_5': 'last',
                'assists_last_5': 'last',
                'minutes_last_5': 'last',
                'xGI_per90_last_5': 'last',
                'points_per90_last_5': 'last',
                'npxGI_last_5': 'last',
                'npxGI_per90_last_5': 'last',
                'bps_last_5': 'last',
                'bps_per90_last_5': 'last',
                'bonus_last_5': 'last',
                'bonus_per90_last_5': 'last',
                'defensive_contribution_last_5': 'last',
                'defensive_contribution_per90_last_5': 'last',
                'tackles_last_5': 'last',
                'starts_last_5': 'last'
            })
            .rename(columns={
                'round': 'fixtures_played',
                'minutes': 'total_minutes',
                'expected_goals': 'total_xG',
                'expected_assists': 'total_xA',
                'expected_goal_involvements': 'total_xGI',
                'npxG': 'total_npxG',
                'npxA': 'total_npxA',
                'npxGI': 'total_npxGI',
                'influence': 'total_influence',
                'creativity': 'total_creativity',
                'threat': 'total_threat',
                'defensive_contribution': 'total_defensive_contribution',
                'tackles': 'total_tackles',
                'clearances_blocks_interceptions': 'total_clearances_blocks_interceptions',
                'recoveries': 'total_recoveries'
            })
        )
        
        # Merge home/away stats
        season_agg = season_agg.merge(home_stats, on='full_name', how='left')
        season_agg = season_agg.merge(away_stats, on='full_name', how='left')
        
        # Fill NaN in home/away stats with 0
        home_away_cols = [col for col in season_agg.columns if '_home' in col or '_away' in col]
        season_agg[home_away_cols] = season_agg[home_away_cols].fillna(0)
        
        # Ensure all numeric
        for col in season_agg.select_dtypes(include=['number']).columns:
            season_agg[col] = pd.to_numeric(season_agg[col], errors='coerce').fillna(0)
        
        # === SEASON-WIDE PER 90 CALCULATIONS ===

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
        season_agg['npxGI_per90_season'] = np.where(
            season_agg['total_minutes'] > 0,
            season_agg['total_npxGI'] * 90 / season_agg['total_minutes'],
            0
        )
        season_agg['npxG_per90_season'] = np.where(
            season_agg['total_minutes'] > 0,
            season_agg['total_npxG'] * 90 / season_agg['total_minutes'],
            0
        )
        
        # BPS and Bonus per 90
        season_agg['bps_per90_season'] = np.where(
            season_agg['total_minutes'] > 0,
            season_agg['bps'] * 90 / season_agg['total_minutes'],
            0
        )
        season_agg['bonus_per90_season'] = np.where(
            season_agg['total_minutes'] > 0,
            season_agg['bonus'] * 90 / season_agg['total_minutes'],
            0
        )
        
        # Defensive per 90
        season_agg['defensive_contribution_per90_season'] = np.where(
            season_agg['total_minutes'] > 0,
            season_agg['total_defensive_contribution'] * 90 / season_agg['total_minutes'],
            0
        )
        season_agg['tackles_per90_season'] = np.where(
            season_agg['total_minutes'] > 0,
            season_agg['total_tackles'] * 90 / season_agg['total_minutes'],
            0
        )
        season_agg['clearances_blocks_interceptions_per90_season'] = np.where(
            season_agg['total_minutes'] > 0,
            season_agg['total_clearances_blocks_interceptions'] * 90 / season_agg['total_minutes'],
            0
        )
        
        # ICT per 90
        season_agg['influence_per90'] = np.where(
            season_agg['total_minutes'] > 0,
            season_agg['total_influence'] * 90 / season_agg['total_minutes'],
            0
        )
        season_agg['creativity_per90'] = np.where(
            season_agg['total_minutes'] > 0,
            season_agg['total_creativity'] * 90 / season_agg['total_minutes'],
            0
        )
        season_agg['threat_per90'] = np.where(
            season_agg['total_minutes'] > 0,
            season_agg['total_threat'] * 90 / season_agg['total_minutes'],
            0
        )
        
        # Minutes per fixture
        season_agg['minutes_per_fixture'] = np.where(
            season_agg['fixtures_played'] > 0,
            season_agg['total_minutes'] / season_agg['fixtures_played'],
            0
        )
        
        # === START PERCENTAGE ===
        season_agg['start_percentage'] = np.where(
            season_agg['fixtures_played'] > 0,
            (season_agg['starts'] / season_agg['fixtures_played']) * 100,
            0
        )
        
        # Form trends
        season_agg['form_trend_points'] = season_agg['points_per90_last_5'] - season_agg['points_per90_season']
        season_agg['form_trend_npxGI'] = season_agg['npxGI_per90_last_5'] - season_agg['npxGI_per90_season']
        season_agg['form_trend_bps'] = season_agg['bps_per90_last_5'] - season_agg['bps_per90_season']
        season_agg['hot_form'] = (season_agg['form_trend_points'] > 1.0) & (season_agg['fixtures_played'] >= 5)
        
        # Overperformance
        season_agg['xG_overperformance'] = season_agg['goals_scored'] - season_agg['total_xG']
        season_agg['xA_overperformance'] = season_agg['assists'] - season_agg['total_xA']
        season_agg['npxG_overperformance'] = (season_agg['goals_scored'] - season_agg['estimated_penalties']) - season_agg['total_npxG']
        
        # Home/Away differential
        season_agg['home_away_points_diff'] = season_agg['points_home_per90'] - season_agg['points_away_per90']
        season_agg['home_away_xGI_diff'] = season_agg['xGI_home_per90'] - season_agg['xGI_away_per90']
        
        return season_agg
    
    def scrape_team_stats(self):
        """Scrape team stats (unchanged from before)"""
        print("Fetching team stats...")
        
        url = f"{self.fpl_base_url}fixtures/"
        response = self.session.get(url)
        response.raise_for_status()
        fixtures = response.json()
        
        fixtures_df = pd.DataFrame(fixtures)
        
        fixtures_df['team_h_name'] = fixtures_df['team_h'].map(lambda x: self.teams[x]['name'])
        fixtures_df['team_a_name'] = fixtures_df['team_a'].map(lambda x: self.teams[x]['name'])
        fixtures_df['team_h_short'] = fixtures_df['team_h'].map(lambda x: self.teams[x]['short_name'])
        fixtures_df['team_a_short'] = fixtures_df['team_a'].map(lambda x: self.teams[x]['short_name'])
        
        fixtures_df['team_h_score'] = pd.to_numeric(fixtures_df['team_h_score'], errors='coerce').fillna(0)
        fixtures_df['team_a_score'] = pd.to_numeric(fixtures_df['team_a_score'], errors='coerce').fillna(0)
        
        completed = fixtures_df[fixtures_df['finished'] == True].copy()
        
        if completed.empty:
            return pd.DataFrame(), pd.DataFrame()
        
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
    """Main function to scrape comprehensive FPL data"""
    scraper = ComprehensiveFPLScraper()
    
    print("="*70)
    print("COMPREHENSIVE FPL DATA SCRAPER")
    print("="*70)
    print("Initializing...")
    scraper.initialize_mappings()
    
    # Scrape player match data
    match_df = scraper.scrape_player_data()
    
    if not match_df.empty:
        # Calculate rolling metrics
        print("\nCalculating rolling metrics...")
        match_df = scraper.calculate_rolling_metrics(match_df)
        
        # Aggregate season stats
        print("Aggregating comprehensive season stats...")
        player_df = scraper.aggregate_player_stats(match_df)
        
        # Save match data
        match_df.to_csv(DATA_DIR / 'fpl_match_data.csv', index=False)
        print(f"\n✅ Saved match data: {len(match_df)} records")
        
        # Save player aggregation
        player_df.to_csv(DATA_DIR / 'enhanced_player_aggregation.csv', index=False)
        print(f"✅ Saved player data: {len(player_df)} players")
        
        # Print summary
        print("\n" + "="*70)
        print("NEW METRICS SUMMARY")
        print("="*70)
        print(f"📊 npXG Metrics:")
        print(f"   - Total estimated penalties: {player_df['estimated_penalties'].sum():.0f}")
        print(f"   - Average npxG per 90: {player_df['npxG_per90_season'].mean():.3f}")
        
        print(f"\n🛡️ Defensive Metrics:")
        print(f"   - Players with defensive contribution: {(player_df['total_defensive_contribution'] > 0).sum()}")
        print(f"   - Average tackles per 90: {player_df['tackles_per90_season'].mean():.2f}")
        
        print(f"\n🎯 Start Percentage:")
        print(f"   - Regular starters (>80%): {(player_df['start_percentage'] > 80).sum()}")
        print(f"   - Rotation risks (<50%): {(player_df['start_percentage'] < 50).sum()}")
        
        print(f"\n⚡ BPS/Bonus per 90:")
        print(f"   - Average BPS/90: {player_df['bps_per90_season'].mean():.2f}")
        print(f"   - Average Bonus/90: {player_df['bonus_per90_season'].mean():.3f}")
        
        print(f"\n🏠 Home/Away Splits:")
        print(f"   - Average home xGI/90: {player_df['xGI_home_per90'].mean():.3f}")
        print(f"   - Average away xGI/90: {player_df['xGI_away_per90'].mean():.3f}")
        
        print("\n" + "="*70)
        print("AVAILABLE COLUMNS")
        print("="*70)
        
        print("\n📈 New Season Metrics:")
        new_cols = [
            'start_percentage',
            'bps_per90_season', 'bonus_per90_season',
            'defensive_contribution_per90_season', 'tackles_per90_season',
            'clearances_blocks_interceptions_per90_season',
            'npxG_per90_season', 'npxGI_per90_season',
            'form_trend_bps', 'npxG_overperformance'
        ]
        for col in new_cols:
            if col in player_df.columns:
                print(f"  ✓ {col}")
        
        print("\n🏠 Home/Away Metrics:")
        home_away_cols = [col for col in player_df.columns if '_home_per90' in col or '_away_per90' in col]
        for col in sorted(home_away_cols)[:10]:  # Show first 10
            print(f"  ✓ {col}")
        if len(home_away_cols) > 10:
            print(f"  ... and {len(home_away_cols) - 10} more")
    
    # Scrape team stats
    defensive_df, attacking_df = scraper.scrape_team_stats()
    
    if not defensive_df.empty:
        defensive_df.to_csv(DATA_DIR / 'team_defensive_analysis.csv', index=False)
        print(f"\n✅ Saved defensive stats: {len(defensive_df)} teams")
    
    if not attacking_df.empty:
        attacking_df.to_csv(DATA_DIR / 'team_attacking_analysis.csv', index=False)
        print(f"✅ Saved attacking stats: {len(attacking_df)} teams")
    
    print("\n" + "="*70)
    print("✅ COMPREHENSIVE DATA SCRAPING COMPLETE!")
    print("="*70)
    
    return True
