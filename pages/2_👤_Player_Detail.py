"""
Enhanced Player Detail Page - Individual Player Statistics and Match History
Shows comprehensive stats for a single selected player with detailed visualizations

Version: 6.0 - Complete Performance Analysis Dashboard with Cumulative Plots

Features:
- Sidebar filters: Position, Team, Price Range
- Default selection: Haaland
- Enhanced tooltips: Match opponent (H/A), minutes played
- Additional per 90 metrics: xG/90, npXG/90, xGI/90, xA/90, DC/90, minutes/start
- 10 Performance visualizations:
  1. FPL Points by Gameweek (line chart)
  2. Goal Contributions - Goals + Assists stacked bar chart
  3. Goals + Assists vs xGI (line comparison)
  4. Goals vs xG (line comparison)
  5. Assists vs xA (line comparison)
  6. Defensive Contributions bar chart (color-coded by position thresholds)
  7. Goals Conceded vs xGC (for GKP/DEF only)
  8. Cumulative xGI vs Cumulative (Goals + Assists)
  9. Cumulative xG vs Cumulative Goals
  10. Cumulative xA vs Cumulative Assists
  11. Cumulative xGC vs Cumulative Goals Conceded (for GKP/DEF only)
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
    """Show enhanced performance trends with multiple visualizations including cumulative plots"""
    
    st.markdown("---")
    st.markdown("#### 📊 Performance Trends")
    
    # Prepare data - ensure proper sorting and numeric types
    chart_df = chart_df.copy()
    chart_df = chart_df.sort_values('round')
    
    # Ensure numeric types
    numeric_cols = ['round', 'total_points', 'goals_scored', 'assists', 'expected_goals', 
                   'expected_assists', 'expected_goal_involvements', 'defensive_contribution',
                   'goals_conceded', 'expected_goals_conceded', 'minutes']
    
    for col in numeric_cols:
        if col in chart_df.columns:
            chart_df[col] = pd.to_numeric(chart_df[col], errors='coerce').fillna(0)
    
    # Calculate cumulative metrics
    chart_df['cum_goals'] = chart_df['goals_scored'].cumsum()
    chart_df['cum_assists'] = chart_df['assists'].cumsum()
    chart_df['cum_goal_involvements'] = (chart_df['goals_scored'] + chart_df['assists']).cumsum()
    chart_df['cum_xG'] = chart_df['expected_goals'].cumsum()
    chart_df['cum_xA'] = chart_df['expected_assists'].cumsum()
    chart_df['cum_xGI'] = chart_df['expected_goal_involvements'].cumsum()
    
    if player_position in ['GKP', 'DEF']:
        chart_df['cum_goals_conceded'] = chart_df['goals_conceded'].cumsum()
        chart_df['cum_xGC'] = chart_df['expected_goals_conceded'].cumsum()
    
    # Add opponent display
    opponent_col = None
    for col in ['opponent_short', 'opponent_team_short', 'opponent_team']:
        if col in chart_df.columns:
            opponent_col = col
            break
    
    if opponent_col:
        chart_df['opponent_display'] = chart_df.apply(
            lambda row: format_opponent_display(row[opponent_col], row.get('was_home', True)),
            axis=1
        )
    else:
        chart_df['opponent_display'] = chart_df['round'].apply(lambda x: f"GW{int(x)}")
    
    # Row 1: FPL Points
    st.markdown("##### 🎯 FPL Points by Gameweek")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=chart_df['round'],
        y=chart_df['total_points'],
        mode='lines+markers',
        name='FPL Points',
        line=dict(color='#3498db', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{customdata}</b><br>' +
                     'Minutes: %{text}<br>' +
                     'Points: %{y}<br>' +
                     '<extra></extra>',
        customdata=chart_df['opponent_display'],
        text=chart_df['minutes'].astype(int)
    ))
    
    fig.update_layout(
        xaxis_title='Gameweek',
        yaxis_title='Points',
        height=300,
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Row 2: Goal Contributions
    st.markdown("##### ⚽ Goal Contributions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        # Goals
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
        
        # Assists
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
            title='Goals + Assists',
            xaxis_title='Gameweek',
            yaxis_title='Count',
            height=350,
            barmode='stack',
            hovermode='closest',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = go.Figure()
        
        # Goal Involvements (Goals + Assists)
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['goals_scored'] + chart_df['assists'],
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
    
    # Row 3: Goals vs xG and Assists vs xA
    col1, col2 = st.columns(2)
    
    with col1:
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
    
    with col2:
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
    
    # Row 4: Defensive Contributions (for all players, but highlight for DEF)
    st.markdown("##### 🛡️ Defensive Metrics")
    
    # Color bars based on DC threshold by position (per game, not per 90)
    dc_thresholds = {
        'GKP': 10,
        'DEF': 10,
        'MID': 12,
        'FWD': 12
    }
    
    dc_threshold = dc_thresholds.get(player_position, 10)
    
    # Calculate DC hit percentage (% of games where they met/exceeded threshold)
    games_with_minutes = chart_df[chart_df['minutes'] > 0]
    if len(games_with_minutes) > 0:
        dc_hits = len(games_with_minutes[games_with_minutes['defensive_contribution'] >= dc_threshold])
        dc_hit_percentage = (dc_hits / len(games_with_minutes)) * 100
    else:
        dc_hit_percentage = 0
    
    threshold_label = f"{player_position}: ≥{dc_threshold} DC"
    
    # Color bars: green if >= threshold, red if below
    colors = ['#2ecc71' if val >= dc_threshold else '#e74c3c' 
             for val in chart_df['defensive_contribution']]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Display DC hit percentage metric above the chart
        st.metric(
            "DC % Hit", 
            f"{dc_hit_percentage:.1f}%",
            help=f"Percentage of games with {dc_threshold}+ defensive contributions"
        )
        
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
            line_color="gray",
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
    
    # Goals Conceded vs xGC (for GKP and DEF only)
    if player_position in ['GKP', 'DEF']:
        with col2:
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
                title='Goals Conceded vs xGC',
                xaxis_title='Gameweek',
                yaxis_title='Count',
                height=350,
                hovermode='closest',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # === NEW: CUMULATIVE PLOTS ===
    st.markdown("---")
    st.markdown("#### 📈 Cumulative Performance - Expected vs Actual")
    
    # Row 5: Cumulative xGI vs G+A and Cumulative xG vs Goals
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        # Cumulative Goals + Assists
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['cum_goal_involvements'],
            mode='lines+markers',
            name='Cumulative G+A',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=8),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Cumulative G+A: %{y}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display']
        ))
        
        # Cumulative xGI
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['cum_xGI'],
            mode='lines+markers',
            name='Cumulative xGI',
            line=dict(color='#95a5a6', width=2, dash='dash'),
            marker=dict(size=6),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Cumulative xGI: %{y:.2f}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display']
        ))
        
        fig.update_layout(
            title='Cumulative: Goals + Assists vs xGI',
            xaxis_title='Gameweek',
            yaxis_title='Cumulative Count',
            height=350,
            hovermode='closest',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = go.Figure()
        
        # Cumulative Goals
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['cum_goals'],
            mode='lines+markers',
            name='Cumulative Goals',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=8),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Cumulative Goals: %{y}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display']
        ))
        
        # Cumulative xG
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['cum_xG'],
            mode='lines+markers',
            name='Cumulative xG',
            line=dict(color='#95a5a6', width=2, dash='dash'),
            marker=dict(size=6),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Cumulative xG: %{y:.2f}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display']
        ))
        
        fig.update_layout(
            title='Cumulative: Goals vs xG',
            xaxis_title='Gameweek',
            yaxis_title='Cumulative Count',
            height=350,
            hovermode='closest',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Row 6: Cumulative xA vs Assists and (for GKP/DEF) Cumulative xGC vs Goals Conceded
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        # Cumulative Assists
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['cum_assists'],
            mode='lines+markers',
            name='Cumulative Assists',
            line=dict(color='#3498db', width=3),
            marker=dict(size=8),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Cumulative Assists: %{y}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display']
        ))
        
        # Cumulative xA
        fig.add_trace(go.Scatter(
            x=chart_df['round'],
            y=chart_df['cum_xA'],
            mode='lines+markers',
            name='Cumulative xA',
            line=dict(color='#95a5a6', width=2, dash='dash'),
            marker=dict(size=6),
            hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                         'Cumulative xA: %{y:.2f}<br>' +
                         '<extra></extra>',
            customdata=chart_df['opponent_display']
        ))
        
        fig.update_layout(
            title='Cumulative: Assists vs xA',
            xaxis_title='Gameweek',
            yaxis_title='Cumulative Count',
            height=350,
            hovermode='closest',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Cumulative xGC vs Goals Conceded (for GKP/DEF only)
    if player_position in ['GKP', 'DEF']:
        with col2:
            fig = go.Figure()
            
            # Cumulative Goals Conceded
            fig.add_trace(go.Scatter(
                x=chart_df['round'],
                y=chart_df['cum_goals_conceded'],
                mode='lines+markers',
                name='Cumulative GC',
                line=dict(color='#e74c3c', width=3),
                marker=dict(size=8),
                hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                             'Cumulative GC: %{y}<br>' +
                             '<extra></extra>',
                customdata=chart_df['opponent_display']
            ))
            
            # Cumulative xGC
            fig.add_trace(go.Scatter(
                x=chart_df['round'],
                y=chart_df['cum_xGC'],
                mode='lines+markers',
                name='Cumulative xGC',
                line=dict(color='#95a5a6', width=2, dash='dash'),
                marker=dict(size=6),
                hovertemplate='<b>GW%{x}: %{customdata}</b><br>' +
                             'Cumulative xGC: %{y:.2f}<br>' +
                             '<extra></extra>',
                customdata=chart_df['opponent_display']
            ))
            
            fig.update_layout(
                title='Cumulative: Goals Conceded vs xGC',
                xaxis_title='Gameweek',
                yaxis_title='Cumulative Count',
                height=350,
                hovermode='closest',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)

def show_player_overview(player_info, recent_matches):
    """Show player overview with stats and upcoming fixtures"""
    
    # Player header
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"### {player_info['full_name']}")
        st.markdown(f"**Position:** {player_info['position']}")
        st.markdown(f"**Team:** {player_info['team']}")
    
    with col2:
        st.metric("Total Points", f"{player_info['total_points']:.0f}")
        st.metric("Price", f"£{player_info['price']:.1f}m")
    
    with col3:
        st.metric("Pts/90 (Season)", f"{player_info.get('points_per90_season', 0):.2f}")
        st.metric("xGI/90 (Season)", f"{player_info.get('xGI_per90_season', 0):.2f}")
    
    with col4:
        st.metric("Pts/90 (L5)", f"{player_info.get('points_per90_last_5', 0):.2f}")
        st.metric("Form Trend", f"{player_info.get('form_trend_points', 0):+.2f}")
    
    # === NEW: Additional Per 90 Metrics ===
    st.markdown("---")
    st.markdown("#### 📊 Detailed Per 90 Metrics")
    
    # Get total_minutes once for all calculations
    total_minutes = player_info.get('total_minutes', 0)
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    with col1:
        st.metric("Pts/90", f"{player_info.get('points_per90_season', 0):.2f}")
    
    with col2:
        # Calculate xG/90 from total_xG
        total_xg = player_info.get('total_xG', 0)
        xg_per90 = (total_xg * 90 / total_minutes) if total_minutes > 0 else 0
        st.metric("xG/90", f"{xg_per90:.2f}")
    
    with col3:
        # Calculate npXG/90 if available
        total_npxg = player_info.get('total_npxG', 0)
        npxg_per90 = (total_npxg * 90 / total_minutes) if total_minutes > 0 else 0
        st.metric("npXG/90", f"{npxg_per90:.2f}")
    
    with col4:
        st.metric("xGI/90", f"{player_info.get('xGI_per90_season', 0):.2f}")
    
    with col5:
        # Calculate xA/90
        total_xa = player_info.get('total_xA', 0)
        xa_per90 = (total_xa * 90 / total_minutes) if total_minutes > 0 else 0
        st.metric("xA/90", f"{xa_per90:.2f}")
    
    with col6:
        # Calculate DC/90
        total_dc = player_info.get('total_defensive_contribution', 0)
        dc_per90 = (total_dc * 90 / total_minutes) if total_minutes > 0 else 0
        st.metric("DC/90", f"{dc_per90:.2f}")
    
    with col7:
        # Minutes per start
        total_starts = player_info.get('starts', 0)
        mins_per_start = total_minutes / total_starts if total_starts > 0 else 0
        st.metric("Mins/Start", f"{mins_per_start:.0f}")
    
    # Add DC Hit % as a separate metric row
    if not recent_matches.empty:
        st.markdown("---")
        st.markdown("#### 🛡️ Defensive Performance")
        
        # Calculate DC hit percentage
        player_position = player_info.get('position', 'MID')
        dc_thresholds = {
            'GKP': 10,
            'DEF': 10,
            'MID': 12,
            'FWD': 12
        }
        dc_threshold = dc_thresholds.get(player_position, 10)
        
        games_with_minutes = recent_matches[recent_matches['minutes'] > 0]
        if len(games_with_minutes) > 0:
            dc_hits = len(games_with_minutes[games_with_minutes['defensive_contribution'] >= dc_threshold])
            dc_hit_percentage = (dc_hits / len(games_with_minutes)) * 100
        else:
            dc_hit_percentage = 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "DC Threshold", 
                f"{dc_threshold} per game",
                help=f"Target defensive contributions per game for {player_position}"
            )
        with col2:
            st.metric(
                "DC % Hit",
                f"{dc_hit_percentage:.1f}%",
                help=f"Percentage of games with {dc_threshold}+ defensive contributions"
            )
        with col3:
            st.metric(
                "Games Hit Target",
                f"{dc_hits}/{len(games_with_minutes)}",
                help=f"Number of games reaching DC threshold"
            )
    
    # Upcoming fixtures
    st.markdown("---")
    st.markdown("#### 📅 Upcoming Fixtures")
    
    if FixtureAnalyzer:
        try:
            analyzer = FixtureAnalyzer()
            analyzer.initialize()
            
            team = player_info.get('team')
            
            if team:
                # Get team ID
                team_id = None
                for tid, team_info in analyzer.teams.items():
                    if team_info['name'] == team:
                        team_id = tid
                        break
                
                if team_id:
                    # Get ALL upcoming fixtures until GW38
                    all_fixtures = analyzer.get_all_fixtures()
                    
                    # Filter for this team's upcoming fixtures
                    team_fixtures = all_fixtures[
                        (all_fixtures['finished'] == False) &
                        ((all_fixtures['team_h'] == team_id) | (all_fixtures['team_a'] == team_id))
                    ].sort_values('event').copy()
                    
                    if not team_fixtures.empty:
                        fixture_list = []
                        
                        for _, fixture in team_fixtures.iterrows():
                            gw = int(fixture['event'])
                            is_home = fixture['team_h'] == team_id
                            
                            if is_home:
                                opponent_id = fixture['team_a']
                                opponent = analyzer.teams[opponent_id]['short_name']
                                venue = 'H'
                                # For home games, use opponent's away strength and their difficulty rating
                                opp_strength = analyzer.teams[opponent_id].get('strength_overall_away', 1000)
                                fdr = fixture.get('team_h_difficulty', 3)
                            else:
                                opponent_id = fixture['team_h']
                                opponent = analyzer.teams[opponent_id]['short_name']
                                venue = 'A'
                                # For away games, use opponent's home strength and their difficulty rating
                                opp_strength = analyzer.teams[opponent_id].get('strength_overall_home', 1000)
                                fdr = fixture.get('team_a_difficulty', 3)
                            
                            # If FPL difficulty is not available (=0), calculate from strength
                            if fdr == 0 or pd.isna(fdr):
                                # Normalize strength values (typically 1000-1400) to FDR scale (1-5)
                                min_strength = 1000
                                max_strength = 1400
                                
                                # Invert and scale to 1-5 range
                                normalized = (opp_strength - min_strength) / (max_strength - min_strength)
                                fdr = 1 + (normalized * 4)
                                
                                # Adjust for venue
                                if is_home:
                                    fdr = fdr * 0.85
                                else:
                                    fdr = fdr * 1.15
                                
                                # Clamp to 1-5 range
                                fdr = max(1.0, min(5.0, fdr))
                            
                            fixture_list.append({
                                'GW': gw,
                                'OPP': f"{opponent} ({venue})",
                                'FDR': int(round(float(fdr)))  # Integer FDR like in example
                            })
                        
                        if fixture_list:
                            fixtures_df = pd.DataFrame(fixture_list)
                            
                            # Display summary metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                avg_fdr = fixtures_df['FDR'].mean()
                                st.metric("Avg FDR", f"{avg_fdr:.2f}")
                            with col2:
                                easy = len(fixtures_df[fixtures_df['FDR'] <= 2.5])
                                st.metric("Easy Fixtures", easy)
                            with col3:
                                hard = len(fixtures_df[fixtures_df['FDR'] >= 3.5])
                                st.metric("Hard Fixtures", hard)
                            
                            st.markdown("---")
                            
                            # Style only the FDR column with colors
                            def color_fdr_column(val):
                                """Apply background color only to FDR values"""
                                try:
                                    fdr = float(val)
                                    color = get_fdr_color(fdr)
                                    return f'background-color: {color}; color: black; font-weight: bold'
                                except:
                                    return ''
                            
                            # Apply styling only to FDR column
                            styled_fixtures = fixtures_df.style.applymap(
                                color_fdr_column,
                                subset=['FDR']
                            )
                            
                            # Scrollable table showing all fixtures until GW38
                            st.dataframe(
                                styled_fixtures,
                                use_container_width=True,
                                hide_index=True,
                                height=600
                            )
                            
                            # Fixture Difficulty Trend Line Plot
                            st.markdown("---")
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
                                text=fixtures_df['OPP'],
                                hovertemplate='<b>GW%{x}</b><br>' +
                                             'vs %{text}<br>' +
                                             'FDR: %{y:.2f}<br>' +
                                             '<extra></extra>'
                            ))
                            
                            # Add difficulty zone lines
                            fig.add_hline(
                                y=2.5,
                                line_dash="dash",
                                line_color="#40E0D0",
                                line_width=2,
                                annotation_text="Easy/Medium",
                                annotation_position="right"
                            )
                            
                            fig.add_hline(
                                y=3.5,
                                line_dash="dash",
                                line_color="#FF69B4",
                                line_width=2,
                                annotation_text="Medium/Hard",
                                annotation_position="right"
                            )
                            
                            fig.update_layout(
                                xaxis_title="Gameweek",
                                yaxis_title="Fixture Difficulty Rating",
                                yaxis=dict(range=[1, 5]),
                                height=400,
                                showlegend=False,
                                hovermode='closest'
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No upcoming fixtures available")
                    else:
                        st.info("No upcoming fixtures available")
                else:
                    st.warning("Could not find team in fixture data")
            else:
                st.warning("Team information not available")
                
        except Exception as e:
            st.warning(f"Could not load fixture data: {str(e)}")
    else:
        st.info("Fixture analyzer not available")

def show_match_table(recent_matches):
    """Show match-by-match table with Totals and Per 90 rows"""
    
    # Check if we have any match data
    if recent_matches.empty:
        return
    
    st.markdown("---")
    st.markdown("#### 🎯 Match-by-Match Performance")
    
    # Sort by gameweek descending (most recent first)
    display_df = recent_matches.copy()
    display_df = display_df.sort_values('round', ascending=False)
    
    # Select and format columns for display
    final_df = pd.DataFrame()
    
    # GW and Opponent
    final_df['GW'] = display_df['round'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "")
    
    # Opponent with (H)/(A)
    opponent_col = None
    for col in ['opponent_short', 'opponent_team_short', 'opponent_team']:
        if col in display_df.columns:
            opponent_col = col
            break
    
    if opponent_col:
        final_df['OPP'] = display_df.apply(
            lambda row: format_opponent_display(row[opponent_col], row.get('was_home', True)),
            axis=1
        )
    else:
        final_df['OPP'] = 'N/A'
    
    # Started (ST) and Minutes (MP)
    final_df['ST'] = display_df['starts'].apply(lambda x: '✓' if x == 1 or x == True else '-')
    final_df['MP'] = display_df['minutes'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "0")
    
    # Performance metrics
    final_df['Pts'] = display_df['total_points'].apply(
        lambda x: f"{x:.1f}" if isinstance(x, float) else int(x) if pd.notna(x) else 0
    )
    final_df['G'] = display_df['goals_scored'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "0")
    final_df['A'] = display_df['assists'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "0")
    final_df['xG'] = display_df['expected_goals'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
    final_df['xA'] = display_df['expected_assists'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
    final_df['xGI'] = display_df['expected_goal_involvements'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
    
    # Goals Conceded and xGC (for all positions, but mainly relevant for DEF/GK)
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
    
    # Calculate totals
    totals_row = {
        'GW': 'Totals',
        'OPP': '',
        'ST': f"{display_df['starts'].sum():.0f}",
        'MP': f"{display_df['minutes'].sum():.0f}",
        'Pts': f"{display_df['total_points'].sum():.1f}",
        'G': f"{display_df['goals_scored'].sum():.0f}",
        'A': f"{display_df['assists'].sum():.0f}",
        'xG': f"{display_df['expected_goals'].sum():.2f}",
        'xA': f"{display_df['expected_assists'].sum():.2f}",
        'xGI': f"{display_df['expected_goal_involvements'].sum():.2f}",
        'GC': f"{display_df['goals_conceded'].sum():.1f}",
        'xGC': f"{display_df['expected_goals_conceded'].sum():.2f}",
        'DC': f"{display_df['defensive_contribution'].sum():.1f}",
        'BPS': f"{display_df['bps'].sum():.1f}",
        'Bonus': f"{display_df['bonus'].sum():.1f}"
    }
    
    # Calculate per 90
    total_minutes = display_df['minutes'].sum()
    if total_minutes > 0:
        per90_row = {
            'GW': 'Per 90',
            'OPP': '',
            'ST': '',
            'MP': f"{total_minutes / display_df['starts'].sum():.0f}",  # Avg mins per start
            'Pts': f"{(display_df['total_points'].sum() * 90 / total_minutes):.2f}",
            'G': f"{(display_df['goals_scored'].sum() * 90 / total_minutes):.2f}",
            'A': f"{(display_df['assists'].sum() * 90 / total_minutes):.2f}",
            'xG': f"{(display_df['expected_goals'].sum() * 90 / total_minutes):.2f}",
            'xA': f"{(display_df['expected_assists'].sum() * 90 / total_minutes):.2f}",
            'xGI': f"{(display_df['expected_goal_involvements'].sum() * 90 / total_minutes):.2f}",
            'GC': f"{(display_df['goals_conceded'].sum() * 90 / total_minutes):.2f}",
            'xGC': f"{(display_df['expected_goals_conceded'].sum() * 90 / total_minutes):.2f}",
            'DC': f"{(display_df['defensive_contribution'].sum() * 90 / total_minutes):.2f}",
            'BPS': f"{(display_df['bps'].sum() * 90 / total_minutes):.2f}",
            'Bonus': f"{(display_df['bonus'].sum() * 90 / total_minutes):.2f}"
        }
    else:
        per90_row = {col: '0.00' for col in final_df.columns}
        per90_row['GW'] = 'Per 90'
    
    # Append totals and per 90 rows
    final_df = pd.concat([
        final_df,
        pd.DataFrame([totals_row]),
        pd.DataFrame([per90_row])
    ], ignore_index=True)
    
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
                key="player_detail_position"
            )
        
        with col2:
            # Team filter
            unique_teams = sorted(player_data['team'].dropna().unique().tolist())
            selected_team = st.selectbox(
                "Team",
                ["All"] + unique_teams,
                key="player_detail_team"
            )
        
        # Price range filter
        if 'price' in player_data.columns:
            min_price = float(player_data['price'].min())
            max_price = float(player_data['price'].max())
            
            price_range = st.slider(
                "Price Range (£m)",
                min_value=min_price,
                max_value=max_price,
                value=(min_price, max_price),
                step=0.1,
                key="player_detail_price"
            )
        else:
            price_range = None
    
    # Apply filters
    filtered_data = player_data.copy()
    
    if selected_position != "All":
        filtered_data = filtered_data[filtered_data['position'] == selected_position]
    
    if selected_team != "All":
        filtered_data = filtered_data[filtered_data['team'] == selected_team]
    
    if price_range:
        filtered_data = filtered_data[
            (filtered_data['price'] >= price_range[0]) &
            (filtered_data['price'] <= price_range[1])
        ]
    
    # Sort by total points
    filtered_data = filtered_data.sort_values('total_points', ascending=False)
    
    # Player selection
    player_names = filtered_data['full_name'].tolist()
    
    # Default to Haaland if available, otherwise first player
    default_index = 0
    if 'Erling Haaland' in player_names:
        default_index = player_names.index('Erling Haaland')
    
    selected_player_name = st.selectbox(
        "Select Player",
        player_names,
        index=default_index,
        key="player_detail_select"
    )
    
    # Get player data
    player_info = filtered_data[filtered_data['full_name'] == selected_player_name].iloc[0].to_dict()
    
    # Check if match data is available
    if match_data is None or match_data.empty:
        st.warning("⚠️ Match-by-match data not available")
        
        # Show player overview without match data
        show_player_overview(player_info, pd.DataFrame())
        return
    
    # Get player's match history using full_name (most reliable matching)
    player_matches = match_data[match_data['full_name'] == selected_player_name].copy()
    
    if player_matches.empty:
        st.warning(f"⚠️ No match data available for {selected_player_name}")
        
        # Show player overview without match data
        show_player_overview(player_info, pd.DataFrame())
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
    
    # Show player overview
    show_player_overview(player_info, player_matches)
    
    # Show match table
    show_match_table(player_matches)
    
    # Show performance charts - pass position info
    player_position = player_info.get('position', 'MID')
    matches_with_minutes = player_matches[player_matches['minutes'] > 0]
    
    if not matches_with_minutes.empty:
        show_performance_trends_enhanced(matches_with_minutes, player_position)
    else:
        st.info("This player has not played any minutes yet this season")

# Call the main show function
show(player_data, match_data)