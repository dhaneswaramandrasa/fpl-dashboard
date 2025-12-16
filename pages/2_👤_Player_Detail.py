"""
Enhanced Player Detail Page - Individual Player Statistics and Match History
Shows comprehensive stats for a single selected player with detailed visualizations

Version: 5.0 - Complete Performance Analysis Dashboard

Features:
- Sidebar filters: Position, Team, Price Range
- Default selection: Haaland
- Enhanced tooltips: Match opponent (H/A), minutes played
- 6 Performance visualizations:
  1. FPL Points by Gameweek (line chart)
  2. Goal Contributions - Goals + Assists stacked bar chart
  3. Goals + Assists vs xGI (line comparison)
  4. Goals vs xG (line comparison)
  5. Assists vs xA (line comparison)
  6. Defensive Contributions bar chart (color-coded by position thresholds)
  7. Goals Conceded vs xGC (for GKP/DEF only)
- Match-by-match table with Totals and Per 90 rows
- Upcoming fixtures with FDR analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import fixture analyzer
try:
    from utils.fixture_analyzer import FixtureAnalyzer
except:
    FixtureAnalyzer = None

# Page config
st.set_page_config(
    page_title="Player Detail - FPL Dashboard",
    page_icon="👤",
    layout="wide"
)

# Check if data is loaded
if 'player_data' not in st.session_state or st.session_state.player_data is None:
    st.error("❌ No data loaded. Please go to the Home page and download data first.")
    if st.button("🏠 Go to Home"):
        st.switch_page("app.py")
    st.stop()

# Get data from session state
player_data = st.session_state.player_data
match_data = st.session_state.match_data

def get_fdr_color(fdr):
    """Get color based on FDR - turquoise for easy, pink for hard"""
    if fdr <= 2.0:
        return '#40E0D0'  # Turquoise - Easy
    elif fdr <= 2.5:
        return '#7FFFD4'  # Aquamarine - Easy-Medium
    elif fdr <= 3.0:
        return '#E0E0E0'  # Light Gray - Medium
    elif fdr <= 3.5:
        return '#FFB6C1'  # Light Pink - Medium-Hard
    elif fdr <= 4.0:
        return '#FF69B4'  # Hot Pink - Hard
    else:
        return '#FF1493'  # Deep Pink - Very Hard

def format_opponent_display(opponent, was_home):
    """Format opponent display with (H) or (A) suffix"""
    if pd.isna(opponent) or opponent == '':
        return 'N/A'
    
    # Handle was_home being various types
    if pd.isna(was_home):
        suffix = "(H)"  # Default to home
    elif isinstance(was_home, bool):
        suffix = "(H)" if was_home else "(A)"
    elif isinstance(was_home, (int, float)):
        suffix = "(H)" if was_home == 1 or was_home == True else "(A)"
    else:
        suffix = "(H)"  # Default to home if unclear
    
    return f"{opponent} {suffix}"

def create_enhanced_tooltip(row):
    """Create enhanced tooltip text with match details"""
    # Determine which opponent column exists
    opponent = None
    if 'opponent_short' in row.index:
        opponent = row['opponent_short']
    elif 'opponent_team_short' in row.index:
        opponent = row['opponent_team_short']
    elif 'opponent_team' in row.index:
        opponent = row['opponent_team']
    
    if opponent and not pd.isna(opponent):
        opponent_display = format_opponent_display(opponent, row.get('was_home', True))
    else:
        opponent_display = f"GW{int(row['round'])}"
    
    tooltip = f"<b>GW{int(row['round'])}: {opponent_display}</b><br>"
    tooltip += f"Minutes: {int(row['minutes'])}<br>"
    return tooltip

def show_performance_trends_enhanced(chart_df, player_position):
    """Show enhanced performance trends with multiple visualizations"""
    
    st.markdown("---")
    st.markdown("#### 📊 Performance Trends")
    
    # Prepare data - ensure proper sorting and numeric types
    chart_df = chart_df.copy()
    chart_df = chart_df.sort_values('round')
    
    # Convert to numeric
    numeric_cols = ['round', 'total_points', 'goals_scored', 'assists', 
                    'expected_goals', 'expected_assists', 'expected_goal_involvements',
                    'minutes', 'defensive_contribution', 'goals_conceded', 
                    'expected_goals_conceded']
    
    for col in numeric_cols:
        if col in chart_df.columns:
            chart_df[col] = pd.to_numeric(chart_df[col], errors='coerce').fillna(0)
    
    # Determine which opponent column to use
    opponent_col = None
    if 'opponent_short' in chart_df.columns:
        opponent_col = 'opponent_short'
    elif 'opponent_team_short' in chart_df.columns:
        opponent_col = 'opponent_team_short'
    elif 'opponent_team' in chart_df.columns:
        opponent_col = 'opponent_team'
    
    # Create opponent display
    if opponent_col:
        chart_df['opponent_display'] = chart_df.apply(
            lambda x: format_opponent_display(x[opponent_col], x.get('was_home', True)), 
            axis=1
        )
    else:
        # Fallback if no opponent column found
        chart_df['opponent_display'] = chart_df['round'].apply(lambda x: f"GW{int(x)}")
    
    # Calculate G+A
    chart_df['goal_contributions'] = chart_df['goals_scored'] + chart_df['assists']
    
    # Row 1: FPL Points and Goal Contributions (existing)
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['total_points'],
            mode='lines+markers',
            name='Points',
            line=dict(color='#3498db', width=3),
            marker=dict(size=8),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Minutes: %{text}<br>' +
                         'Points: %{y}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display'],
            text=chart_df['minutes'].astype(int)
        ))
        
        fig.update_layout(
            title='FPL Points by Gameweek',
            xaxis_title='Gameweek',
            yaxis_title='Points',
            height=350,
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=chart_df['round'],
            y=chart_df['goals_scored'],
            name='Goals',
            marker_color='#e74c3c',
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Minutes: %{text}<br>' +
                         'Goals: %{y}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display'],
            text=chart_df['minutes'].astype(int)
        ))
        
        fig.add_trace(go.Bar(
            x=chart_df['round'],
            y=chart_df['assists'],
            name='Assists',
            marker_color='#3498db',
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Minutes: %{text}<br>' +
                         'Assists: %{y}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display'],
            text=chart_df['minutes'].astype(int)
        ))
        
        fig.update_layout(
            title='Goal Contributions',
            xaxis_title='Gameweek',
            yaxis_title='Count',
            barmode='stack',
            height=350,
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Row 2: G+A vs xGI and Goals vs xG
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        # Actual G+A
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['goal_contributions'],
            mode='lines+markers',
            name='Goals + Assists',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=8),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Minutes: %{text}<br>' +
                         'G+A: %{y}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display'],
            text=chart_df['minutes'].astype(int)
        ))
        
        # xGI
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['expected_goal_involvements'],
            mode='lines+markers',
            name='xGI',
            line=dict(color='#95a5a6', width=2, dash='dash'),
            marker=dict(size=6),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Minutes: %{text}<br>' +
                         'xGI: %{y:.2f}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display'],
            text=chart_df['minutes'].astype(int)
        ))
        
        fig.update_layout(
            title='Goals + Assists vs xGI',
            xaxis_title='Gameweek',
            yaxis_title='Count',
            height=350,
            hovermode='closest',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = go.Figure()
        
        # Actual Goals
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['goals_scored'],
            mode='lines+markers',
            name='Goals',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=8),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Minutes: %{text}<br>' +
                         'Goals: %{y}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display'],
            text=chart_df['minutes'].astype(int)
        ))
        
        # xG
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['expected_goals'],
            mode='lines+markers',
            name='xG',
            line=dict(color='#95a5a6', width=2, dash='dash'),
            marker=dict(size=6),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Minutes: %{text}<br>' +
                         'xG: %{y:.2f}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display'],
            text=chart_df['minutes'].astype(int)
        ))
        
        fig.update_layout(
            title='Goals vs xG',
            xaxis_title='Gameweek',
            yaxis_title='Count',
            height=350,
            hovermode='closest',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Row 3: Assists vs xA and DC (Defensive Contributions)
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        # Actual Assists
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['assists'],
            mode='lines+markers',
            name='Assists',
            line=dict(color='#3498db', width=3),
            marker=dict(size=8),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Minutes: %{text}<br>' +
                         'Assists: %{y}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display'],
            text=chart_df['minutes'].astype(int)
        ))
        
        # xA
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['expected_assists'],
            mode='lines+markers',
            name='xA',
            line=dict(color='#95a5a6', width=2, dash='dash'),
            marker=dict(size=6),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Minutes: %{text}<br>' +
                         'xA: %{y:.2f}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display'],
            text=chart_df['minutes'].astype(int)
        ))
        
        fig.update_layout(
            title='Assists vs xA',
            xaxis_title='Gameweek',
            yaxis_title='Count',
            height=350,
            hovermode='closest',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # DC threshold based on position
        if player_position == 'DEF':
            dc_threshold = 10
            threshold_label = 'DEF (10+)'
            high_color = '#2ecc71'  # Green for defenders
        elif player_position in ['MID', 'FWD']:
            dc_threshold = 12
            threshold_label = f'{player_position} (12+)'
            high_color = '#f39c12'  # Orange for mid/fwd
        else:  # GKP
            dc_threshold = 10
            threshold_label = 'GKP (10+)'
            high_color = '#9b59b6'  # Purple for GKP
        
        # Color bars based on threshold
        colors = ['#3498db' if dc < dc_threshold else high_color 
                  for dc in chart_df['defensive_contribution']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=chart_df['round'],
            y=chart_df['defensive_contribution'],
            name='Defensive Contributions',
            marker_color=colors,
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Minutes: %{text}<br>' +
                         'DC: %{y}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display'],
            text=chart_df['minutes'].astype(int)
        ))
        
        # Add threshold line
        fig.add_hline(
            y=dc_threshold, 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"Threshold: {dc_threshold}",
            annotation_position="right"
        )
        
        fig.update_layout(
            title=f'Defensive Contributions (Highlight: {threshold_label})',
            xaxis_title='Gameweek',
            yaxis_title='DC',
            height=350,
            hovermode='closest',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Row 4: Goals Conceded vs xGC (for GKP and DEF only)
    if player_position in ['GKP', 'DEF']:
        st.markdown("##### 🛡️ Defensive Metrics")
        
        fig = go.Figure()
        
        # Actual Goals Conceded
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['goals_conceded'],
            mode='lines+markers',
            name='Goals Conceded',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=8),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Minutes: %{text}<br>' +
                         'GC: %{y}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display'],
            text=chart_df['minutes'].astype(int)
        ))
        
        # xGC
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['expected_goals_conceded'],
            mode='lines+markers',
            name='xGC',
            line=dict(color='#95a5a6', width=2, dash='dash'),
            marker=dict(size=6),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Minutes: %{text}<br>' +
                         'xGC: %{y:.2f}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display'],
            text=chart_df['minutes'].astype(int)
        ))
        
        fig.update_layout(
            title='Goals Conceded vs Expected Goals Conceded (xGC)',
            xaxis_title='Gameweek',
            yaxis_title='Goals',
            height=350,
            hovermode='closest',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)


def show_upcoming_fixtures(player_info):
    """Show all upcoming fixtures for the player's team until GW38"""
    st.markdown("### 📅 Upcoming Fixtures")
    
    if FixtureAnalyzer is None:
        st.warning("Fixture analyzer not available")
        return
    
    try:
        # Initialize fixture analyzer
        analyzer = FixtureAnalyzer()
        analyzer.initialize()
        
        # Get player's team
        player_team = player_info.get('team', player_info.get('player_team', ''))
        
        if not player_team:
            st.warning("Team information not available for this player")
            return
        
        # Get all upcoming fixtures
        all_fixtures = analyzer.get_all_fixtures()
        
        # Get team form data
        team_form_df = None
        if 'team_defensive' in st.session_state and 'team_attacking' in st.session_state:
            defensive_df = st.session_state.team_defensive
            attacking_df = st.session_state.team_attacking
            if defensive_df is not None and attacking_df is not None:
                team_form_df = defensive_df.merge(
                    attacking_df,
                    on=['team', 'short_name', 'games_played'],
                    how='outer',
                    suffixes=('_def', '_att')
                )
        
        # Find team ID
        team_id = None
        for tid, team_info in analyzer.teams.items():
            if team_info['name'] == player_team:
                team_id = tid
                break
        
        if team_id is None:
            st.warning(f"Could not find team ID for {player_team}")
            return
        
        # Get upcoming fixtures for this team
        upcoming = all_fixtures[
            (all_fixtures['finished'] == False) &
            ((all_fixtures['team_h'] == team_id) | (all_fixtures['team_a'] == team_id))
        ].sort_values('event')
        
        if upcoming.empty:
            st.info("No upcoming fixtures available")
            return
        
        # Build fixture list with FDR
        fixture_list = []
        
        for _, fixture in upcoming.iterrows():
            gw = fixture['event']
            is_home = fixture['team_h'] == team_id
            
            if is_home:
                opponent_id = fixture['team_a']
                opponent_name = analyzer.teams[opponent_id]['name']
                opponent_short = analyzer.teams[opponent_id]['short_name']
                venue = "H"
                venue_emoji = "🏠"
            else:
                opponent_id = fixture['team_h']
                opponent_name = analyzer.teams[opponent_id]['name']
                opponent_short = analyzer.teams[opponent_id]['short_name']
                venue = "A"
                venue_emoji = "✈️"
            
            # Calculate FDR
            fdr = analyzer.calculate_fixture_difficulty(
                team_id, opponent_id, is_home, team_form_df
            )
            
            fixture_list.append({
                'GW': int(gw),
                'Venue': venue_emoji,
                'Opponent': opponent_short,
                'Full Name': opponent_name,
                'FDR': fdr,
                'Difficulty': 'Easy' if fdr < 2.5 else 'Medium' if fdr < 3.5 else 'Hard'
            })
        
        if not fixture_list:
            st.info("No upcoming fixtures available")
            return
        
        # Create dataframe
        fixtures_df = pd.DataFrame(fixture_list)
        
        # Display summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_fdr = fixtures_df['FDR'].mean()
            st.metric("Average FDR", f"{avg_fdr:.2f}")
        
        with col2:
            easy_fixtures = len(fixtures_df[fixtures_df['FDR'] < 2.5])
            st.metric("Easy Fixtures", easy_fixtures)
        
        with col3:
            hard_fixtures = len(fixtures_df[fixtures_df['FDR'] > 3.5])
            st.metric("Hard Fixtures", hard_fixtures)
        
        st.markdown("---")
        
        # Display fixtures table with color coding
        st.markdown(f"#### Next {len(fixtures_df)} Fixtures")
        
        def color_fdr(val):
            """Color code FDR values"""
            try:
                fdr = float(val)
                color = get_fdr_color(fdr)
                return f'background-color: {color}; color: black; font-weight: bold'
            except:
                return ''
        
        # Style the dataframe
        styled_df = fixtures_df.style.applymap(
            color_fdr, 
            subset=['FDR']
        ).format({
            'FDR': '{:.2f}'
        })
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=min(400, len(fixtures_df) * 35 + 38)
        )
        
        # Fixture difficulty chart
        st.markdown("#### Fixture Difficulty Trend")
        
        fig = go.Figure()
        
        # Add line with markers
        fig.add_trace(go.Scatter(
            x=fixtures_df['GW'],
            y=fixtures_df['FDR'],
            mode='lines+markers',
            name='FDR',
            line=dict(color='#3498db', width=3),
            marker=dict(
                size=10,
                color=fixtures_df['FDR'].apply(get_fdr_color),
                line=dict(color='white', width=1)
            ),
            text=fixtures_df['Opponent'],
            hovertemplate='<b>GW%{x}</b><br>' +
                         'vs %{text}<br>' +
                         'FDR: %{y:.2f}<br>' +
                         '<extra></extra>'
        ))
        
        # Add difficulty zones
        fig.add_hline(y=2.5, line_dash="dash", line_color="#40E0D0", line_width=2,
                     annotation_text="Easy/Medium", annotation_position="right")
        fig.add_hline(y=3.5, line_dash="dash", line_color="#FF69B4", line_width=2,
                     annotation_text="Medium/Hard", annotation_position="right")
        
        fig.update_layout(
            xaxis_title="Gameweek",
            yaxis_title="Fixture Difficulty Rating",
            yaxis=dict(range=[1, 5]),
            height=350,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading fixtures: {str(e)}")
        st.info("Fixture analysis requires team stats to be loaded. Try refreshing data.")


def show_season_stats(recent_matches, player_info):
    """Show this season's match history with totals and per 90"""
    
    st.markdown("#### This Season")
    st.caption(f"Showing {len(recent_matches)} matches (most recent first)")
    
    # Determine which opponent column to use
    opponent_col = None
    if 'opponent_short' in recent_matches.columns:
        opponent_col = 'opponent_short'
    elif 'opponent_team_short' in recent_matches.columns:
        opponent_col = 'opponent_team_short'
    elif 'opponent_team' in recent_matches.columns:
        opponent_col = 'opponent_team'
    
    # Calculate totals
    totals = {
        'round': 'Totals',
        opponent_col if opponent_col else 'opponent': '',
        'was_home': '',
        'minutes': recent_matches['minutes'].sum(),
        'total_points': recent_matches['total_points'].sum(),
        'goals_scored': recent_matches['goals_scored'].sum(),
        'assists': recent_matches['assists'].sum(),
        'expected_goals': recent_matches['expected_goals'].sum(),
        'expected_assists': recent_matches['expected_assists'].sum(),
        'expected_goal_involvements': recent_matches['expected_goal_involvements'].sum(),
        'clean_sheets': recent_matches['clean_sheets'].sum(),
        'goals_conceded': recent_matches['goals_conceded'].sum(),
        'expected_goals_conceded': recent_matches['expected_goals_conceded'].sum(),
        'defensive_contribution': recent_matches['defensive_contribution'].sum(),
        'tackles': recent_matches['tackles'].sum(),
        'clearances_blocks_interceptions': recent_matches['clearances_blocks_interceptions'].sum(),
        'recoveries': recent_matches['recoveries'].sum(),
        'bps': recent_matches['bps'].sum(),
        'bonus': recent_matches['bonus'].sum(),
        'influence': recent_matches['influence'].sum(),
        'creativity': recent_matches['creativity'].sum(),
        'threat': recent_matches['threat'].sum()
    }
    
    # Calculate per 90
    total_minutes = recent_matches['minutes'].sum()
    per_90 = totals.copy()
    per_90['round'] = 'Per 90'
    
    if total_minutes > 0:
        for key in per_90.keys():
            if key not in ['round', opponent_col if opponent_col else 'opponent', 'was_home', 'minutes', 'clean_sheets']:
                if isinstance(per_90[key], (int, float)):
                    per_90[key] = per_90[key] * 90 / total_minutes
    
    # Create display dataframe
    display_df = recent_matches.copy()
    
    # Add totals and per 90 rows
    totals_df = pd.DataFrame([totals])
    per_90_df = pd.DataFrame([per_90])
    display_df = pd.concat([display_df, totals_df, per_90_df], ignore_index=True)
    
    # Format display columns
    final_df = pd.DataFrame()
    
    # Basic info
    final_df['GW'] = display_df['round'].apply(lambda x: int(x) if pd.notna(x) and str(x) not in ['Totals', 'Per 90'] else x)
    
    # Create OPP column with proper handling
    if opponent_col:
        final_df['OPP'] = display_df.apply(
            lambda x: '' if x['round'] in ['Totals', 'Per 90'] else 
                     format_opponent_display(x[opponent_col], x.get('was_home', True)),
            axis=1
        )
    else:
        final_df['OPP'] = ''
    
    # Minutes - special handling
    final_df['MP'] = display_df['minutes'].apply(
        lambda x: int(x) if pd.notna(x) else 0
    )
    
    # FPL scoring
    final_df['PTS'] = display_df['total_points'].apply(
        lambda x: f"{x:.1f}" if isinstance(x, float) else int(x) if pd.notna(x) else 0
    )
    final_df['GS'] = display_df['goals_scored'].apply(
        lambda x: f"{x:.1f}" if isinstance(x, float) else int(x) if pd.notna(x) else 0
    )
    final_df['A'] = display_df['assists'].apply(
        lambda x: f"{x:.1f}" if isinstance(x, float) else int(x) if pd.notna(x) else 0
    )
    
    # Expected stats
    final_df['xG'] = display_df['expected_goals'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
    final_df['xA'] = display_df['expected_assists'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
    final_df['xGI'] = display_df['expected_goal_involvements'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
    
    # Defensive
    final_df['CS'] = display_df['clean_sheets'].apply(
        lambda x: '' if isinstance(x, float) else int(x) if pd.notna(x) else 0
    )
    final_df['GC'] = display_df['goals_conceded'].apply(
        lambda x: f"{x:.1f}" if isinstance(x, float) else int(x) if pd.notna(x) else 0
    )
    final_df['xGC'] = display_df['expected_goals_conceded'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
    final_df['DC'] = display_df['defensive_contribution'].apply(
        lambda x: f"{x:.1f}" if isinstance(x, float) else int(x) if pd.notna(x) else 0
    )
    
    # BPS/Bonus
    final_df['BPS'] = display_df['bps'].apply(
        lambda x: f"{x:.1f}" if isinstance(x, float) else int(x) if pd.notna(x) else 0
    )
    final_df['Bonus'] = display_df['bonus'].apply(
        lambda x: f"{x:.1f}" if isinstance(x, float) else int(x) if pd.notna(x) else 0
    )
    
    # Apply styling
    def highlight_totals_per90(row):
        if row['GW'] == 'Totals':
            return ['background-color: #2c3e50; color: white; font-weight: bold'] * len(row)
        elif row['GW'] == 'Per 90':
            return ['background-color: #34495e; color: white; font-weight: bold'] * len(row)
        else:
            return [''] * len(row)
    
    styled_df = final_df.style.apply(highlight_totals_per90, axis=1)
    
    # Display the table
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=min(600, len(final_df) * 35 + 38)
    )
    
    # Performance charts - pass position info
    player_position = player_info.get('position', 'MID')
    show_performance_trends_enhanced(
        recent_matches[recent_matches['minutes'] > 0], 
        player_position
    )


def show(player_data, match_data):
    """Main function to display player detail page"""
    
    # Player selection
    st.title("👤 Player Detail")
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("### 🔧 Player Filters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Position filter
            unique_positions = sorted(player_data['position'].dropna().unique().tolist())
            selected_position = st.selectbox(
                "Position",
                ["All"] + unique_positions,
                key="detail_position"
            )
        
        with col2:
            # Team filter
            if 'team' in player_data.columns:
                unique_teams = sorted(player_data['team'].dropna().astype(str).unique().tolist())
                selected_team = st.selectbox(
                    "Team",
                    ["All"] + unique_teams,
                    key="detail_team"
                )
            else:
                selected_team = "All"
        
        # Price filter (if available)
        if 'price' in player_data.columns:
            player_data['price'] = pd.to_numeric(player_data['price'], errors='coerce').fillna(0)
            
            min_price = float(player_data['price'].min())
            max_price = float(player_data['price'].max())
            
            if max_price > min_price:
                price_range = st.slider(
                    "Price Range (£m)",
                    min_price,
                    max_price,
                    (min_price, max_price),
                    0.5,
                    key="detail_price"
                )
            else:
                price_range = (min_price, max_price)
        else:
            price_range = None
    
    # Apply filters to player data
    filtered_data = player_data.copy()
    
    if selected_position != "All":
        filtered_data = filtered_data[filtered_data['position'] == selected_position]
    
    if selected_team != "All":
        filtered_data = filtered_data[filtered_data['team'] == selected_team]
    
    if price_range is not None:
        filtered_data = filtered_data[
            (filtered_data['price'] >= price_range[0]) & 
            (filtered_data['price'] <= price_range[1])
        ]
    
    # Get unique players sorted by total points from filtered data
    player_list = filtered_data.nlargest(500, 'total_points')['full_name'].unique().tolist()
    
    if len(player_list) == 0:
        st.warning("⚠️ No players match the selected filters")
        return
    
    # Find Haaland's index (default to 0 if not found or not in filtered list)
    default_index = 0
    haaland_names = ['Erling Haaland', 'Haaland', 'E. Haaland']
    for name in haaland_names:
        if name in player_list:
            default_index = player_list.index(name)
            break
    
    selected_player = st.selectbox(
        "Select Player",
        options=player_list,
        index=default_index
    )
    
    # Get player info
    player_info = player_data[player_data['full_name'] == selected_player].iloc[0]
    
    # Display player header
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Team", player_info['team'])
    
    with col2:
        st.metric("Position", player_info['position'])
    
    with col3:
        st.metric("Price", f"£{player_info['price']:.1f}m")
    
    with col4:
        st.metric("Total Points", int(player_info['total_points']))
    
    with col5:
        st.metric("Pts/90", f"{player_info['points_per90_season']:.2f}")
    
    with col6:
        st.metric("Form", f"{player_info['points_per90_last_5']:.2f}", 
                 f"{player_info['form_trend_points']:+.2f}")
    
    st.markdown("---")
    
    # Check if match data is available
    if match_data is None or match_data.empty:
        st.warning("⚠️ Match-by-match data not available")
        return
    
    # Get player's matches
    player_matches = match_data[match_data['full_name'] == selected_player].copy()
    
    if player_matches.empty:
        st.warning("⚠️ No match data available for this player")
        return
    
    # Ensure numeric columns are properly typed
    numeric_cols = ['round', 'total_points', 'goals_scored', 'assists', 
                    'expected_goals', 'expected_assists', 'expected_goal_involvements',
                    'clean_sheets', 'goals_conceded', 'expected_goals_conceded',
                    'minutes', 'defensive_contribution', 'tackles',
                    'clearances_blocks_interceptions', 'recoveries',
                    'bps', 'bonus', 'influence', 'creativity', 'threat']
    
    for col in numeric_cols:
        if col in player_matches.columns:
            player_matches[col] = pd.to_numeric(player_matches[col], errors='coerce').fillna(0)
    
    # Sort by gameweek DESCENDING (most recent first)
    player_matches = player_matches.sort_values('round', ascending=False)
    
    # Show all matches
    recent_matches = player_matches.copy()
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["📊 This Season", "📅 Upcoming Fixtures"])
    
    with tab1:
        show_season_stats(recent_matches, player_info)
    
    with tab2:
        show_upcoming_fixtures(player_info)


# Call the main show function
show(player_data, match_data)