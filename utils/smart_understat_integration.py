"""
SMART SOLUTION: Automatic Name Matching
Uses FPL player data + team matching to automatically find Understat players
NO MANUAL MAPPING NEEDED!
"""

import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from pathlib import Path

try:
    from understatapi import UnderstatClient
    UNDERSTAT_AVAILABLE = True
except ImportError:
    UNDERSTAT_AVAILABLE = False


class SmartUnderstatIntegration:
    """
    Automatic matching between FPL and Understat
    No manual name mapping required!
    """
    
    def __init__(self):
        if not UNDERSTAT_AVAILABLE:
            raise ImportError("Install understatapi: pip install understatapi")
        
        # Team name mappings (these are consistent)
        self.team_mapping = {
            # Understat team name: FPL team name
            'Arsenal': 'Arsenal',
            'Aston Villa': 'Aston Villa',
            'Bournemouth': 'Bournemouth',
            'Brentford': 'Brentford',
            'Brighton': 'Brighton',
            'Chelsea': 'Chelsea',
            'Crystal Palace': 'Crystal Palace',
            'Everton': 'Everton',
            'Fulham': 'Fulham',
            'Ipswich': 'Ipswich',
            'Leicester': 'Leicester',
            'Liverpool': 'Liverpool',
            'Manchester City': 'Man City',
            'Manchester United': 'Man Utd',
            'Newcastle United': 'Newcastle',
            'Nottingham Forest': "Nott'm Forest",
            "Nottingham' Forest": "Nott'm Forest",
            'Southampton': 'Southampton',
            'Tottenham': 'Spurs',
            'West Ham': 'West Ham',
            'Wolverhampton Wanderers': 'Wolves',
        }
        
        # Cache for Understat data
        self.understat_cache = None
    
    def similarity_score(self, name1, name2):
        """Calculate similarity between two names"""
        # Clean names
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        
        # Exact match
        if n1 == n2:
            return 1.0
        
        # Check if last names match
        last1 = n1.split()[-1]
        last2 = n2.split()[-1]
        
        if last1 == last2 and len(last1) > 3:
            return 0.85  # Strong match on last name
        
        # Sequence matcher
        return SequenceMatcher(None, n1, n2).ratio()
    
    def fetch_understat_data(self, league="EPL", season="2025", verbose=True):
        """Fetch all Understat data for current season (2025/2026)"""
        
        if verbose:
            print(f"🌐 Fetching Understat data for {league} {season}/{int(season)+1}...")
        
        try:
            with UnderstatClient() as understat:
                player_data = understat.league(league=league).get_player_data(season=season)
                
                if not player_data:
                    print("❌ No data returned from Understat")
                    return None
                
                df = pd.DataFrame(player_data)
                
                # Convert numeric columns
                numeric_cols = ['games', 'time', 'goals', 'xG', 'assists', 'xA',
                              'shots', 'key_passes', 'npg', 'npxG', 'xGChain', 'xGBuildup']
                
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                # Map team names
                df['fpl_team'] = df['team_title'].map(self.team_mapping)
                
                if verbose:
                    print(f"✅ Fetched {len(df)} players from Understat")
                
                self.understat_cache = df
                return df
                
        except Exception as e:
            if verbose:
                print(f"❌ Error: {e}")
            return None
    
    def match_players(self, fpl_df, understat_df, verbose=True):
        """
        Automatically match FPL players to Understat players
        Uses name similarity + team matching
        """
        
        if verbose:
            print("\n🔍 Matching FPL players to Understat...")
        
        matches = []
        
        for _, fpl_player in fpl_df.iterrows():
            fpl_name = fpl_player['player_name']
            fpl_team = fpl_player['team_short']
            
            # Find Understat players from the same team
            same_team = understat_df[understat_df['fpl_team'] == fpl_team]
            
            if len(same_team) == 0:
                # Try without team filter (for team name mismatches)
                same_team = understat_df
            
            # Calculate similarity scores
            best_match = None
            best_score = 0
            
            for _, us_player in same_team.iterrows():
                us_name = us_player['player_name']
                score = self.similarity_score(fpl_name, us_name)
                
                # Bonus for same team
                if us_player['fpl_team'] == fpl_team:
                    score += 0.15
                
                if score > best_score:
                    best_score = score
                    best_match = us_player
            
            # Only accept strong matches
            if best_score >= 0.7:  # Threshold for acceptance
                matches.append({
                    'fpl_player_id': fpl_player.get('player_id', None),
                    'fpl_name': fpl_name,
                    'fpl_team': fpl_team,
                    'understat_name': best_match['player_name'],
                    'understat_team': best_match['team_title'],
                    'match_score': best_score,
                    'understat_index': best_match.name
                })
        
        matches_df = pd.DataFrame(matches)
        
        if verbose:
            print(f"✅ Matched {len(matches_df)}/{len(fpl_df)} players ({len(matches_df)/len(fpl_df)*100:.1f}%)")
            print(f"   Average match confidence: {matches_df['match_score'].mean():.2%}")
        
        return matches_df
    
    def merge_with_fpl(self, fpl_df, understat_df=None, verbose=True):
        """
        Merge Understat data with FPL data using automatic matching
        """
        
        # Fetch Understat data if not provided
        if understat_df is None:
            understat_df = self.fetch_understat_data(verbose=verbose)
        
        if understat_df is None or understat_df.empty:
            print("⚠️ No Understat data available")
            return fpl_df
        
        # Match players
        matches = self.match_players(fpl_df, understat_df, verbose=verbose)
        
        if len(matches) == 0:
            print("⚠️ No matches found")
            return fpl_df
        
        # Calculate metrics for Understat data
        understat_df = self._calculate_metrics(understat_df)
        
        # Merge based on matches
        for _, match in matches.iterrows():
            us_idx = match['understat_index']
            us_data = understat_df.loc[us_idx]
            
            # Find FPL player
            fpl_mask = fpl_df['player_name'] == match['fpl_name']
            
            if fpl_mask.sum() > 0:
                # Add Understat columns
                fpl_df.loc[fpl_mask, 'total_shots'] = us_data['shots']
                fpl_df.loc[fpl_mask, 'shots_per_90'] = us_data['shots_per_90']
                fpl_df.loc[fpl_mask, 'xG_per_shot'] = us_data['xG_per_shot']
                fpl_df.loc[fpl_mask, 'shot_conversion'] = us_data['shot_conversion']
                fpl_df.loc[fpl_mask, 'chances_created'] = us_data['key_passes']
                fpl_df.loc[fpl_mask, 'chances_created_per_90'] = us_data['key_passes_per_90']
                fpl_df.loc[fpl_mask, 'key_passes_per_90'] = us_data['key_passes_per_90']  # Alias for compatibility
                fpl_df.loc[fpl_mask, 'xGChain'] = us_data['xGChain']
                fpl_df.loc[fpl_mask, 'xGBuildup'] = us_data['xGBuildup']
                fpl_df.loc[fpl_mask, 'goals_vs_xG'] = us_data['goals_vs_xG']
                fpl_df.loc[fpl_mask, 'assists_vs_xA'] = us_data['assists_vs_xA']
                fpl_df.loc[fpl_mask, 'non_penalty_goals'] = us_data['npg']
                fpl_df.loc[fpl_mask, 'non_penalty_xG'] = us_data['npxG']
        
        has_data = fpl_df['total_shots'].notna().sum()
        if verbose:
            print(f"✅ Added shot data to {has_data} players")
        
        return fpl_df
    
    def _calculate_metrics(self, df):
        """Calculate derived metrics"""
        
        df['shots_per_90'] = np.where(
            df['time'] > 0,
            (df['shots'] / df['time']) * 90,
            0
        )
        
        df['key_passes_per_90'] = np.where(
            df['time'] > 0,
            (df['key_passes'] / df['time']) * 90,
            0
        )
        
        df['xG_per_shot'] = np.where(
            df['shots'] > 0,
            df['xG'] / df['shots'],
            0
        )
        
        df['shot_conversion'] = np.where(
            df['shots'] > 0,
            (df['goals'] / df['shots']) * 100,
            0
        )
        
        df['goals_vs_xG'] = df['goals'] - df['xG']
        df['assists_vs_xA'] = df['assists'] - df['xA']
        
        return df
    
    def get_goals_imminent(self, fpl_df, min_shots=6, max_goals=2):
        """Find players with high shots but low goals"""
        
        if 'total_shots' not in fpl_df.columns:
            return pd.DataFrame()
        
        candidates = fpl_df[
            (fpl_df['total_shots'].notna()) &
            (fpl_df['total_shots'] >= min_shots) &
            (fpl_df['goals_scored'] <= max_goals) &
            (fpl_df['total_minutes'] >= 180)
        ].copy()
        
        if len(candidates) == 0:
            return pd.DataFrame()
        
        candidates['xG_delta'] = candidates['goals_scored'] - candidates['expected_goals']
        candidates = candidates.sort_values('xG_delta')
        
        return candidates[[
            'player_name', 'team_short', 'price', 'position',
            'total_shots', 'shots_per_90', 'goals_scored',
            'expected_goals', 'xG_delta', 'shot_conversion'
        ]]
    
    def get_assists_imminent(self, fpl_df, min_chances=6, max_assists=2):
        """Find players with high chances created but low assists"""
        
        if 'chances_created' not in fpl_df.columns:
            return pd.DataFrame()
        
        candidates = fpl_df[
            (fpl_df['chances_created'].notna()) &
            (fpl_df['chances_created'] >= min_chances) &
            (fpl_df['assists'] <= max_assists) &
            (fpl_df['total_minutes'] >= 180)
        ].copy()
        
        if len(candidates) == 0:
            return pd.DataFrame()
        
        candidates['xA_delta'] = candidates['assists'] - candidates['expected_assists']
        candidates = candidates.sort_values('xA_delta')
        
        return candidates[[
            'player_name', 'team_short', 'price', 'position',
            'chances_created', 'chances_created_per_90', 'assists',
            'expected_assists', 'xA_delta'
        ]]
    
    def save_cache(self, df, filepath='data/understat_cache.csv'):
        """Save Understat data to cache"""
        Path(filepath).parent.mkdir(exist_ok=True)
        df.to_csv(filepath, index=False)
        print(f"💾 Cached to {filepath}")


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("SMART UNDERSTAT INTEGRATION - AUTOMATIC MATCHING")
    print("="*70)
    print()
    
    if not UNDERSTAT_AVAILABLE:
        print("❌ understatapi not installed")
        print("Install with: pip install understatapi")
        exit(1)
    
    # Test with sample FPL data
    print("Testing automatic matching...")
    print()
    
    integration = SmartUnderstatIntegration()
    
    # Fetch Understat data
    understat_data = integration.fetch_understat_data()
    
    if understat_data is not None:
        print("\n✅ SUCCESS!")
        print("="*70)
        
        # Show sample
        print("\nSample Understat players:")
        print("-"*70)
        sample = understat_data[['player_name', 'team_title', 'shots', 'key_passes']].head(10)
        print(sample.to_string(index=False))
        
        # Test matching with sample FPL data
        print("\n" + "="*70)
        print("To use in your dashboard:")
        print("="*70)
        print("""
1. Replace understat_package_integration.py with this file (smart_understat_integration.py)

2. In your scraper, use:
   
   from utils.smart_understat_integration import SmartUnderstatIntegration
   
   integration = SmartUnderstatIntegration()
   understat_data = integration.fetch_understat_data()
   aggregated = integration.merge_with_fpl(aggregated, understat_data)

3. That's it! No manual name mapping needed.
""")
        
        integration.save_cache(understat_data)
        
    else:
        print("\n❌ Failed to fetch Understat data")