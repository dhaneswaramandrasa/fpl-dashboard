"""
Fixture Analysis Utility
Fetches upcoming fixtures and calculates difficulty ratings
UPDATED: Skip nearly-complete gameweeks
"""

import requests
import pandas as pd
import numpy as np
from typing import Dict, List

class FixtureAnalyzer:
    """Analyzes upcoming fixtures and calculates difficulty ratings"""
    
    def __init__(self):
        self.fpl_base_url = "https://fantasy.premierleague.com/api/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.teams = {}
        self.fixtures = []
        self.current_gw = None
        self.first_full_gw = None  # First GW where most teams have fixtures
    
    def get_bootstrap_data(self) -> Dict:
        """Fetch main FPL bootstrap data"""
        url = f"{self.fpl_base_url}bootstrap-static/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def initialize(self):
        """Initialize team data and current gameweek"""
        data = self.get_bootstrap_data()
        
        # Create team mapping with strength ratings
        for team in data['teams']:
            self.teams[team['id']] = {
                'id': team['id'],
                'name': team['name'],
                'short_name': team['short_name'],
                'strength': team['strength'],
                'strength_overall_home': team['strength_overall_home'],
                'strength_overall_away': team['strength_overall_away'],
                'strength_attack_home': team['strength_attack_home'],
                'strength_attack_away': team['strength_attack_away'],
                'strength_defence_home': team['strength_defence_home'],
                'strength_defence_away': team['strength_defence_away'],
            }
        
        # Get current gameweek
        for event in data['events']:
            if event['is_current']:
                self.current_gw = event['id']
                break
        
        if not self.current_gw:
            for event in data['events']:
                if event['is_next']:
                    self.current_gw = event['id']
                    break
        
        return data
    
    def get_all_fixtures(self) -> pd.DataFrame:
        """Get all fixtures"""
        url = f"{self.fpl_base_url}fixtures/"
        response = self.session.get(url)
        response.raise_for_status()
        fixtures = response.json()
        
        df = pd.DataFrame(fixtures)
        
        # Add team names
        df['team_h_name'] = df['team_h'].map(lambda x: self.teams[x]['name'])
        df['team_a_name'] = df['team_a'].map(lambda x: self.teams[x]['name'])
        df['team_h_short'] = df['team_h'].map(lambda x: self.teams[x]['short_name'])
        df['team_a_short'] = df['team_a'].map(lambda x: self.teams[x]['short_name'])
        
        return df
    
    def find_first_full_gameweek(self, fixtures_df: pd.DataFrame) -> int:
        """
        Find the first gameweek where at least 75% of teams have unfinished fixtures
        This skips nearly-complete gameweeks (like GW16 where only 2 teams have fixtures left)
        """
        if self.current_gw is None:
            return None
        
        # Check upcoming gameweeks
        for gw in range(self.current_gw, self.current_gw + 10):
            gw_fixtures = fixtures_df[
                (fixtures_df['event'] == gw) &
                (fixtures_df['finished'] == False)
            ]
            
            # Count unique teams with fixtures in this gameweek
            teams_with_fixtures = set()
            for _, fixture in gw_fixtures.iterrows():
                teams_with_fixtures.add(fixture['team_h'])
                teams_with_fixtures.add(fixture['team_a'])
            
            num_teams = len(teams_with_fixtures)
            total_teams = len(self.teams)
            
            # If at least 75% of teams have fixtures, use this gameweek
            if num_teams >= (total_teams * 0.75):
                print(f"First full gameweek: GW{gw} ({num_teams}/{total_teams} teams have fixtures)")
                return gw
        
        # Fallback to current gameweek
        return self.current_gw
    
    def get_upcoming_fixtures(self, next_n_gameweeks: int = 5) -> pd.DataFrame:
        """Get upcoming fixtures for next N gameweeks, starting from first full gameweek"""
        if self.current_gw is None:
            return pd.DataFrame()
        
        fixtures_df = self.get_all_fixtures()
        
        # Find first gameweek where most teams have fixtures
        self.first_full_gw = self.find_first_full_gameweek(fixtures_df)
        
        if self.first_full_gw is None:
            self.first_full_gw = self.current_gw
        
        # Filter for upcoming unfinished fixtures starting from first full gameweek
        upcoming = fixtures_df[
            (fixtures_df['finished'] == False) &
            (fixtures_df['event'].notna()) &
            (fixtures_df['event'] >= self.first_full_gw) &
            (fixtures_df['event'] < self.first_full_gw + next_n_gameweeks)
        ].copy()
        
        upcoming = upcoming.sort_values(['event', 'kickoff_time'])
        
        print(f"Analyzing GW{self.first_full_gw} to GW{self.first_full_gw + next_n_gameweeks - 1}")
        print(f"Found {len(upcoming)} fixtures")
        
        return upcoming
    
    def calculate_fixture_difficulty(self, team_id: int, opponent_id: int, 
                                     is_home: bool, team_form_df: pd.DataFrame = None) -> float:
        """
        Calculate fixture difficulty score for a team
        Lower score = easier fixture
        
        Factors:
        1. Opponent strength rating (40%)
        2. Home/Away advantage (20%)
        3. Opponent's defensive form (20%)
        4. Opponent's attacking form (10%)
        5. Team's own form (10%)
        """
        
        opponent = self.teams[opponent_id]
        team = self.teams[team_id]
        
        # 1. Base opponent strength (1-5 scale)
        if is_home:
            opponent_strength = opponent['strength_overall_away'] / 1000  # Normalize to 0-1
        else:
            opponent_strength = opponent['strength_overall_home'] / 1000
        
        base_difficulty = opponent_strength * 5  # Scale to 1-5
        
        # 2. Home/Away adjustment
        home_advantage = -0.5 if is_home else 0.5  # Easier at home
        
        # 3. Opponent defensive form (from team_form_df if available)
        defensive_difficulty = 0
        if team_form_df is not None and not team_form_df.empty:
            opponent_data = team_form_df[team_form_df['team'] == opponent['name']]
            if not opponent_data.empty:
                # Higher goals conceded = easier for attackers
                goals_conceded = opponent_data.iloc[0].get('goals_conceded_per_game', 1.5)
                # Normalize: 2.0+ conceded = easy (0), 0.5 conceded = hard (1)
                defensive_difficulty = max(0, min(1, (2.0 - goals_conceded) / 1.5))
        
        # 4. Opponent attacking threat
        attacking_threat = 0
        if team_form_df is not None and not team_form_df.empty:
            opponent_data = team_form_df[team_form_df['team'] == opponent['name']]
            if not opponent_data.empty:
                # Higher goals scored = harder to keep clean sheet
                goals_scored = opponent_data.iloc[0].get('goals_per_game', 1.5)
                # Normalize: 0.5 goals = easy (0), 2.5+ goals = hard (1)
                attacking_threat = max(0, min(1, (goals_scored - 0.5) / 2.0))
        
        # 5. Team's own form (better form = handle tough fixtures better)
        team_form_factor = 0
        if team_form_df is not None and not team_form_df.empty:
            team_data = team_form_df[team_form_df['team'] == team['name']]
            if not team_data.empty:
                # Better form = can handle tougher fixtures
                goals_scored = team_data.iloc[0].get('goals_per_game', 1.0)
                team_form_factor = -max(0, min(0.5, (goals_scored - 1.0) / 2.0))  # Bonus for good form
        
        # Weighted combination
        difficulty = (
            base_difficulty * 0.4 +
            home_advantage +
            defensive_difficulty * 0.8 +
            attacking_threat * 0.4 +
            team_form_factor
        )
        
        # Normalize to 1-5 scale (like FPL FDR)
        difficulty = max(1.0, min(5.0, difficulty))
        
        return round(difficulty, 2)
    
    def analyze_team_fixtures(self, next_n_gameweeks: int = 5, 
                              team_form_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Analyze upcoming fixtures for all teams
        Returns DataFrame with fixture difficulty ratings
        """
        
        upcoming_fixtures = self.get_upcoming_fixtures(next_n_gameweeks)
        
        if upcoming_fixtures.empty:
            print("Warning: No upcoming fixtures found")
            return pd.DataFrame()
        
        team_fixture_data = []
        
        for team_id, team_info in self.teams.items():
            # Get all fixtures for this team (home and away)
            home_fixtures = upcoming_fixtures[upcoming_fixtures['team_h'] == team_id].copy()
            away_fixtures = upcoming_fixtures[upcoming_fixtures['team_a'] == team_id].copy()
            
            # Combine all fixtures into a list with gameweek info
            all_fixtures = []
            
            # Add home fixtures
            for _, fixture in home_fixtures.iterrows():
                opponent_id = fixture['team_a']
                opponent_short = self.teams[opponent_id]['short_name']
                gw = fixture['event']
                
                difficulty = self.calculate_fixture_difficulty(
                    team_id, opponent_id, True, team_form_df
                )
                
                all_fixtures.append({
                    'gw': gw,
                    'opponent_short': opponent_short,
                    'is_home': True,
                    'difficulty': difficulty
                })
            
            # Add away fixtures
            for _, fixture in away_fixtures.iterrows():
                opponent_id = fixture['team_h']
                opponent_short = self.teams[opponent_id]['short_name']
                gw = fixture['event']
                
                difficulty = self.calculate_fixture_difficulty(
                    team_id, opponent_id, False, team_form_df
                )
                
                all_fixtures.append({
                    'gw': gw,
                    'opponent_short': opponent_short,
                    'is_home': False,
                    'difficulty': difficulty
                })
            
            # Sort by gameweek to get chronological order
            all_fixtures.sort(key=lambda x: x['gw'])
            
            # Take only the first N fixtures
            all_fixtures = all_fixtures[:next_n_gameweeks]
            
            if all_fixtures:
                fixtures_list = []
                difficulty_scores = []
                
                for fixture in all_fixtures:
                    venue = 'H' if fixture['is_home'] else 'A'
                    fixtures_list.append(f"{fixture['opponent_short']} ({venue})")
                    difficulty_scores.append(fixture['difficulty'])
                
                team_fixture_data.append({
                    'team': team_info['name'],
                    'short_name': team_info['short_name'],
                    'fixtures': ', '.join(fixtures_list),
                    'num_fixtures': len(fixtures_list),
                    'avg_difficulty': round(np.mean(difficulty_scores), 2),
                    'total_difficulty': round(sum(difficulty_scores), 2),
                    'difficulty_scores': difficulty_scores,
                    'fixture_list': fixtures_list
                })
        
        df = pd.DataFrame(team_fixture_data)
        
        if df.empty:
            return df
        
        # Sort by average difficulty (ascending = easier fixtures)
        df = df.sort_values('avg_difficulty', ascending=True)
        df['rank'] = range(1, len(df) + 1)
        
        return df
    
    def get_detailed_fixtures(self, next_n_gameweeks: int = 5,
                             team_form_df: pd.DataFrame = None) -> pd.DataFrame:
        """Get detailed fixture by fixture breakdown with difficulty ratings"""
        
        upcoming_fixtures = self.get_upcoming_fixtures(next_n_gameweeks)
        
        if upcoming_fixtures.empty:
            return pd.DataFrame()
        
        detailed_fixtures = []
        
        for _, fixture in upcoming_fixtures.iterrows():
            gw = fixture['event']
            team_h_id = fixture['team_h']
            team_a_id = fixture['team_a']
            
            # Calculate difficulty for home team
            h_difficulty = self.calculate_fixture_difficulty(
                team_h_id, team_a_id, True, team_form_df
            )
            
            # Calculate difficulty for away team
            a_difficulty = self.calculate_fixture_difficulty(
                team_a_id, team_h_id, False, team_form_df
            )
            
            detailed_fixtures.append({
                'gameweek': gw,
                'fixture': f"{fixture['team_h_short']} vs {fixture['team_a_short']}",
                'home_team': fixture['team_h_name'],
                'away_team': fixture['team_a_name'],
                'home_difficulty': h_difficulty,
                'away_difficulty': a_difficulty,
                'kickoff_time': fixture.get('kickoff_time', '')
            })
        
        return pd.DataFrame(detailed_fixtures)


def analyze_fixtures(next_n_gameweeks: int = 5, 
                     defensive_df: pd.DataFrame = None,
                     attacking_df: pd.DataFrame = None) -> Dict:
    """
    Main function to analyze fixtures
    
    Returns dictionary with:
    - team_fixtures: DataFrame with team fixture difficulty rankings
    - detailed_fixtures: DataFrame with individual fixture details
    - current_gw: Current/starting gameweek number
    """
    
    analyzer = FixtureAnalyzer()
    analyzer.initialize()
    
    print(f"Current gameweek: {analyzer.current_gw}")
    
    # Merge team form data if available
    team_form_df = None
    if defensive_df is not None and attacking_df is not None:
        team_form_df = defensive_df.merge(
            attacking_df,
            on=['team', 'short_name', 'games_played'],
            how='outer',
            suffixes=('_def', '_att')
        )
    
    # Get team fixture analysis (this will find first full gameweek)
    team_fixtures = analyzer.analyze_team_fixtures(next_n_gameweeks, team_form_df)
    
    # Get detailed fixture breakdown
    detailed_fixtures = analyzer.get_detailed_fixtures(next_n_gameweeks, team_form_df)
    
    # Use first_full_gw as the starting point for display
    starting_gw = analyzer.first_full_gw if analyzer.first_full_gw else analyzer.current_gw
    
    print(f"Found fixtures for {len(team_fixtures)} teams")
    print(f"Total individual fixtures: {len(detailed_fixtures)}")
    
    return {
        'team_fixtures': team_fixtures,
        'detailed_fixtures': detailed_fixtures,
        'current_gw': starting_gw  # Return the starting GW (not current GW)
    }
