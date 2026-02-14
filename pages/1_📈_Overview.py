"""
Overview Page - High Level FPL Statistics
Shows top performers, trends, and key metrics

ENHANCED: Custom Leaderboard includes comprehensive home/away metrics + npxG metrics
Version: With npxG/90 (Season, Last 5, Home, Away) + Understat Integration
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Page config
st.set_page_config(
    page_title="Overview - FPL Dashboard",
    page_icon="📈",
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


def show(player_data, match_data):
    """Display overview page"""
    
    if player_data is None or player_data.empty:
        st.error("❌ No player data available. Please download data from the sidebar.")
        return
    
    st.header("📈 FPL Overview - Season Performance")
    st.markdown("---")
    
    # Filters in sidebar
    with st.sidebar:
        st.markdown("### 🔧 Filters")
        
        # Position filter
        unique_positions = player_data['position'].dropna().unique().tolist()

        selected_position = st.selectbox(
            "Filter by Position",
            ["All"] + sorted(unique_positions),
            key="comp_position"
        )
        
        # Minimum minutes filter
        min_minutes = st.slider(
            "Minimum Minutes", 
            0, 
            int(player_data['total_minutes'].max()), 
            200,
            50,
            key="overview_minutes"
        )
    
    # Filter data
    filtered_df = player_data.copy()
    if selected_position != "All":
        filtered_df = filtered_df[filtered_df['position'] == selected_position]
    filtered_df = filtered_df[filtered_df['total_minutes'] >= min_minutes]
    
    # Create hot_form flag if it doesn't exist
    if 'hot_form' not in filtered_df.columns:
        filtered_df['hot_form'] = (
            (filtered_df['form_trend_points'] > 1.0) & 
            (filtered_df['minutes_last_5'] >= 270)
        )
    
    # Key metrics at the top
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        top_scorer = filtered_df.nlargest(1, 'total_points').iloc[0]
        st.metric(
            "🏆 Top Scorer",
            top_scorer['player_name'],
            f"{top_scorer['total_points']:.0f} pts"
        )
    
    with col2:
        hot_form = filtered_df[filtered_df['hot_form'] == True]
        st.metric(
            "🔥 Players in Hot Form",
            len(hot_form),
            f"{len(hot_form)/len(filtered_df)*100:.1f}%"
        )
    
    with col3:
        avg_price = filtered_df['total_points'].sum() / len(filtered_df)
        st.metric(
            "📊 Avg Points",
            f"{avg_price:.1f}",
            "per player"
        )
    
    with col4:
        total_players = len(filtered_df)
        st.metric(
            "👥 Players",
            total_players,
            f"with {min_minutes}+ mins"
        )
    
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["🎯 Performance Analysis", "🔥 Form Trends", "💎 Value Analysis"])
    
    with tab1:
        show_performance_analysis(filtered_df)
    
    with tab2:
        show_form_trends(filtered_df, match_data)
    
    with tab3:
        show_value_analysis(filtered_df)
    
    # ============================================================================
    # ADD UNDERSTAT TABLES HERE - Inside the show() function, after the tabs
    # ============================================================================
    st.markdown("---")
    st.markdown("### 🎯 Statistical Analysis - Goals & Assists Imminent")
    
    # Try to import and use Understat integration
    try:
        from utils.smart_understat_integration import UnderstatPackageIntegration
        
        understat = UnderstatPackageIntegration()
        
        col1, col2 = st.columns(2)
        
        with col1:
            goals_imm = understat.get_goals_imminent(filtered_df)  # Use filtered_df here
            if len(goals_imm) > 0:
                st.subheader("⚽ Goals Imminent")
                st.caption("High shots, low goals - due to score soon")
                st.dataframe(
                    goals_imm.head(10).style.format({
                        'price': '{:.1f}',
                        'total_shots': '{:.0f}',
                        'shots_per_90': '{:.2f}',
                        'goals_scored': '{:.0f}',
                        'expected_goals': '{:.2f}',
                        'xG_delta': '{:+.2f}',
                        'shot_conversion': '{:.1f}'
                    }),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("⚽ No players currently meet 'Goals Imminent' criteria")
        
        with col2:
            assists_imm = understat.get_assists_imminent(filtered_df)  # Use filtered_df here
            if len(assists_imm) > 0:
                st.subheader("🅰️ Assists Imminent")
                st.caption("High chances created, low assists - due to assist soon")
                st.dataframe(
                    assists_imm.head(10).style.format({
                        'price': '{:.1f}',
                        'chances_created': '{:.0f}',
                        'chances_created_per_90': '{:.2f}',
                        'assists': '{:.0f}',
                        'expected_assists': '{:.2f}',
                        'xA_delta': '{:+.2f}'
                    }),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("🅰️ No players currently meet 'Assists Imminent' criteria")
    
    except ImportError:
        st.info("💡 Install understatapi for shot and chance data: `pip install understatapi`")
    except Exception as e:
        st.warning(f"⚠️ Could not load shot data: {str(e)[:100]}")


def show_performance_analysis(df):
    """Show performance scatter plots and top performers"""
    
    st.subheader("🎯 Performance Analysis")
    
    # Performance scatter plot
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Total Points vs Expected Goal Involvements")
        
        fig = px.scatter(
            df,
            x='total_xGI',
            y='total_points',
            size='total_minutes',
            color='position',
            hover_data=['player_name', 'price', 'team_short', 'points_per90_season'],
            labels={
                'total_xGI': 'Expected Goal Involvements (xGI)',
                'total_points': 'Total Points',
                'total_minutes': 'Minutes',
                'price': 'Price',
                'position': 'Position'
            },
            color_discrete_map={
                'FWD': '#e74c3c',
                'MID': '#3498db', 
                'DEF': '#2ecc71',
                'GKP': '#f39c12'
            }
        )
        
        fig.update_traces(marker=dict(line=dict(width=1, color='white')))
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Recent Form (Last 5 Games)")
        
        # Filter for players with minutes in last 5 games
        recent_df = df[df['minutes_last_5'] >= 90].copy()
        
        if len(recent_df) > 0:
            fig2 = px.scatter(
                recent_df,
                x='xGI_per90_last_5',
                y='points_per90_last_5',
                size='minutes_last_5',
                color='position',
                hover_data=['player_name', 'price', 'team_short'],
                labels={
                    'xGI_per90_last_5': 'xGI/90',
                    'points_per90_last_5': 'Points/90',
                    'minutes_last_5': 'Minutes L5'
                },
                color_discrete_map={
                    'FWD': '#e74c3c',
                    'MID': '#3498db',
                    'DEF': '#2ecc71',
                    'GKP': '#f39c12'
                }
            )
            fig2.update_traces(marker=dict(line=dict(width=1, color='white')))
            fig2.update_layout(height=500)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Not enough data for recent form analysis")
    
    # Top performers table
    st.subheader("🏆 Top Performers (Season)")
    
    df_copy = df.copy()
    
    if 'xG_per90_season' not in df_copy.columns:
        df_copy['xG_per90_season'] = np.where(
            df_copy['total_minutes'] > 0,
            (df_copy['total_xG'] * 90 / df_copy['total_minutes']),
            0
        )
    
    base_cols = ['player_name', 'price', 'team_short', 'position', 'total_points', 'total_minutes', 
                 'points_per90_season', 'total_xGI', 'xGI_per90_season']
    optional_cols = []
    col_names = ['Player', 'Price', 'Team', 'Pos', 'Points', 'Minutes', 'Pts/90', 'xGI', 'xGI/90']
    format_dict = {
        'Points': '{:.0f}',
        'Price': '{:.1f}',
        'Minutes': '{:.0f}',
        'Pts/90': '{:.2f}',
        'xGI': '{:.2f}',
        'xGI/90': '{:.2f}'
    }
    
    if 'xG_per90_season' in df_copy.columns:
        optional_cols.append('xG_per90_season')
        col_names.append('xG/90')
        format_dict['xG/90'] = '{:.2f}'
    
    if 'xG_per90_last_5' in df_copy.columns:
        optional_cols.append('xG_per90_last_5')
        col_names.append('xG/90 L5')
        format_dict['xG/90 L5'] = '{:.2f}'
    
    if 'xGI_per90_last_5' in df_copy.columns:
        optional_cols.append('xGI_per90_last_5')
        col_names.append('xGI/90 L5')
        format_dict['xGI/90 L5'] = '{:.2f}'
    
    all_cols = base_cols + optional_cols
    top_performers = df_copy.nlargest(20, 'total_points')[all_cols].copy()
    top_performers.columns = col_names
    
    st.dataframe(
        top_performers.style.format(format_dict).background_gradient(subset=['Points'], cmap='YlGn'),
        use_container_width=True,
        hide_index=True
    )
    
    # === ENHANCED: Custom Leaderboard with npxG metrics ===
    st.markdown("---")
    st.subheader("📊 Custom Leaderboard - Top 20 by Metric")
    
    all_data = player_data.copy()
    
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    
    with filter_col1:
        # METRIC OPTIONS with npxG added
        metric_options = {
            # Season Metrics
            'xGI/90 (Season)': 'xGI_per90_season',
            'xG/90 (Season)': 'xG_per90_season',
            'xA/90 (Season)': 'xA_per90_season',
            'npxG/90 (Season)': 'npxG_per90_season',
            'npxGI/90 (Season)': 'npxGI_per90_season',
            'Points/90 (Season)': 'points_per90_season',
            'BPS/90 (Season)': 'bps_per90_season',
            'Bonus/90 (Season)': 'bonus_per90_season',
            'Defensive Contrib/90 (Season)': 'defensive_contribution_per90_season',
            
            # Last 5 Games
            'xGI/90 (Last 5)': 'xGI_per90_last_5',
            'xG/90 (Last 5)': 'xG_per90_last_5',
            'xA/90 (Last 5)': 'xA_per90_last_5',
            'npxG/90 (Last 5)': 'npxG_per90_last_5',
            'npxGI/90 (Last 5)': 'npxGI_per90_last_5',
            'Points/90 (Last 5)': 'points_per90_last_5',
            
            # HOME Performance
            'xG/90 (Home)': 'xG_home_per90',
            'xGI/90 (Home)': 'xGI_home_per90',
            'npxG/90 (Home)': 'npxG_home_per90',
            'npxGI/90 (Home)': 'npxGI_home_per90',
            'Points/90 (Home)': 'points_home_per90',
            'BPS/90 (Home)': 'bps_home_per90',
            'Bonus/90 (Home)': 'bonus_home_per90',
            'Defensive Contrib/90 (Home)': 'def_contrib_home_per90',
            
            # AWAY Performance
            'xG/90 (Away)': 'xG_away_per90',
            'xGI/90 (Away)': 'xGI_away_per90',
            'npxG/90 (Away)': 'npxG_away_per90',
            'npxGI/90 (Away)': 'npxGI_away_per90',
            'Points/90 (Away)': 'points_away_per90',
            'BPS/90 (Away)': 'bps_away_per90',
            'Bonus/90 (Away)': 'bonus_away_per90',
            'Defensive Contrib/90 (Away)': 'def_contrib_away_per90',
            
            # Differentials
            'Home/Away Points Diff': 'home_away_points_diff',
            'Home/Away xGI Diff': 'home_away_xGI_diff',

            # Shooting & Creation (if available)
            '---SHOOTING---': None,
            'Total Shots': 'total_shots',
            'Shots/90': 'shots_per_90',
            'Shot Conversion %': 'shot_conversion',
            'xG per Shot': 'xG_per_shot',
            
            '---CREATION---': None,
            'Chances Created': 'chances_created',
            'Chances/90': 'chances_created_per_90',
            'xGChain': 'xGChain',
            'xGBuildup': 'xGBuildup'
        }
        
        # Filter to only show available metrics
        available_metrics = {k: v for k, v in metric_options.items() if v is None or v in all_data.columns}
        
        if not available_metrics:
            st.warning("No per 90 metrics available in data")
            return
        
        sort_metric_label = st.selectbox(
            "Sort by Metric",
            list(available_metrics.keys()),
            key="leaderboard_metric"
        )
        sort_metric = available_metrics[sort_metric_label]
    
    # Only continue if a valid metric is selected (not a divider)
    if sort_metric is None:
        st.info("Please select a metric (not a divider)")
        return
    
    with filter_col2:
        positions = ['All'] + sorted(all_data['position'].dropna().unique().tolist())
        selected_pos = st.selectbox("Position", positions, key="leaderboard_position")
    
    with filter_col3:
        teams = ['All'] + sorted(all_data['team_short'].dropna().unique().tolist())
        selected_team = st.selectbox("Team", teams, key="leaderboard_team")
    
    with filter_col4:
        min_mins_options = [0, 180, 360, 450, 540, 900]
        leaderboard_min_mins = st.selectbox("Min Minutes", min_mins_options, index=3, key="leaderboard_minutes")
    
    price_col1, price_col2, price_col3 = st.columns([1, 1, 2])
    
    with price_col1:
        min_price = st.number_input("Min Price (£m)", 3.5, 15.0, 3.5, 0.5, key="leaderboard_min_price")
    
    with price_col2:
        max_price = st.number_input("Max Price (£m)", 3.5, 15.0, 15.0, 0.5, key="leaderboard_max_price")
    
    # Apply filters
    leaderboard_df = all_data.copy()
    
    if selected_pos != 'All':
        leaderboard_df = leaderboard_df[leaderboard_df['position'] == selected_pos]
    
    if selected_team != 'All':
        leaderboard_df = leaderboard_df[leaderboard_df['team_short'] == selected_team]
    
    leaderboard_df = leaderboard_df[leaderboard_df['total_minutes'] >= leaderboard_min_mins]
    leaderboard_df = leaderboard_df[(leaderboard_df['price'] >= min_price) & (leaderboard_df['price'] <= max_price)]
    
    if len(leaderboard_df) > 0:
        leaderboard_df = leaderboard_df.sort_values(sort_metric, ascending=False).head(20)
        
        display_cols = ['player_name', 'team_short', 'position', 'price', 'total_points', 'total_minutes']
        
        if sort_metric not in display_cols:
            display_cols.append(sort_metric)
        
        # ENHANCED RELATED METRICS with npxG context
        related_metrics = {
            'xGI_per90_season': ['xG_per90_season', 'npxG_per90_season', 'points_per90_season', 'total_xGI'],
            'xG_per90_season': ['xGI_per90_season', 'npxG_per90_season', 'points_per90_season', 'goals_scored'],
            'xA_per90_season': ['xGI_per90_season', 'points_per90_season', 'assists'],
            'npxG_per90_season': ['xG_per90_season', 'npxGI_per90_season', 'goals_scored', 'total_npxG'],
            'npxGI_per90_season': ['npxG_per90_season', 'xGI_per90_season', 'points_per90_season', 'total_npxGI'],
            'points_per90_season': ['xGI_per90_season', 'npxGI_per90_season', 'total_points'],
            
            'xGI_per90_last_5': ['xG_per90_last_5', 'npxG_per90_last_5', 'points_per90_last_5', 'xGI_last_5'],
            'xG_per90_last_5': ['xGI_per90_last_5', 'npxG_per90_last_5', 'points_per90_last_5', 'goals_last_5'],
            'xA_per90_last_5': ['xGI_per90_last_5', 'points_per90_last_5', 'assists_last_5'],
            'npxG_per90_last_5': ['xG_per90_last_5', 'npxGI_per90_last_5', 'goals_last_5'],
            'npxGI_per90_last_5': ['npxG_per90_last_5', 'xGI_per90_last_5', 'points_per90_last_5'],
            'points_per90_last_5': ['xGI_per90_last_5', 'npxGI_per90_last_5', 'points_last_5'],
            
            'bps_per90_season': ['bonus_per90_season', 'points_per90_season', 'bps'],
            'bonus_per90_season': ['bps_per90_season', 'points_per90_season', 'bonus'],
            'defensive_contribution_per90_season': ['points_per90_season', 'tackles_per90_season', 'defensive_contribution'],
            
            # Home metrics with npxG
            'xG_home_per90': ['xG_away_per90', 'npxG_home_per90', 'xG_per90_season', 'goals_home'],
            'xGI_home_per90': ['xGI_away_per90', 'npxGI_home_per90', 'xGI_per90_season', 'xGI_home'],
            'npxG_home_per90': ['npxG_away_per90', 'xG_home_per90', 'npxG_per90_season', 'npxG_home'],
            'npxGI_home_per90': ['npxGI_away_per90', 'xGI_home_per90', 'npxGI_per90_season', 'npxGI_home'],
            'points_home_per90': ['points_away_per90', 'points_per90_season', 'points_home'],
            'bps_home_per90': ['bps_away_per90', 'bps_per90_season', 'bps_home'],
            'bonus_home_per90': ['bonus_away_per90', 'bonus_per90_season', 'bonus_home'],
            'def_contrib_home_per90': ['def_contrib_away_per90', 'defensive_contribution_per90_season', 'def_contrib_home'],
            
            # Away metrics with npxG
            'xG_away_per90': ['xG_home_per90', 'npxG_away_per90', 'xG_per90_season', 'goals_away'],
            'xGI_away_per90': ['xGI_home_per90', 'npxGI_away_per90', 'xGI_per90_season', 'xGI_away'],
            'npxG_away_per90': ['npxG_home_per90', 'xG_away_per90', 'npxG_per90_season', 'npxG_away'],
            'npxGI_away_per90': ['npxGI_home_per90', 'xGI_away_per90', 'npxGI_per90_season', 'npxGI_away'],
            'points_away_per90': ['points_home_per90', 'points_per90_season', 'points_away'],
            'bps_away_per90': ['bps_home_per90', 'bps_per90_season', 'bps_away'],
            'bonus_away_per90': ['bonus_home_per90', 'bonus_per90_season', 'bonus_away'],
            'def_contrib_away_per90': ['def_contrib_home_per90', 'defensive_contribution_per90_season', 'def_contrib_away'],
            
            'home_away_points_diff': ['points_home_per90', 'points_away_per90', 'points_per90_season'],
            'home_away_xGI_diff': ['xGI_home_per90', 'xGI_away_per90', 'xGI_per90_season']
        }
        
        if sort_metric in related_metrics:
            for metric in related_metrics[sort_metric]:
                if metric in leaderboard_df.columns and metric not in display_cols:
                    display_cols.append(metric)
        
        display_cols = [col for col in display_cols if col in leaderboard_df.columns]
        leaderboard_display = leaderboard_df[display_cols].copy()
        
        # COLUMN NAME MAPPING with npxG
        col_name_mapping = {
            'player_name': 'Player',
            'team_short': 'Team',
            'position': 'Pos',
            'price': 'Price',
            'total_points': 'Points',
            'total_minutes': 'Mins',
            
            'xGI_per90_season': 'xGI/90',
            'xG_per90_season': 'xG/90',
            'xA_per90_season': 'xA/90',
            'npxG_per90_season': 'npxG/90',
            'npxGI_per90_season': 'npxGI/90',
            'points_per90_season': 'Pts/90',
            'bps_per90_season': 'BPS/90',
            'bonus_per90_season': 'Bonus/90',
            'defensive_contribution_per90_season': 'DC/90',
            'tackles_per90_season': 'Tackles/90',
            
            'xGI_per90_last_5': 'xGI/90 L5',
            'xG_per90_last_5': 'xG/90 L5',
            'xA_per90_last_5': 'xA/90 L5',
            'npxG_per90_last_5': 'npxG/90 L5',
            'npxGI_per90_last_5': 'npxGI/90 L5',
            'points_per90_last_5': 'Pts/90 L5',
            
            'xG_home_per90': 'xG/90 🏠',
            'xGI_home_per90': 'xGI/90 🏠',
            'npxG_home_per90': 'npxG/90 🏠',
            'npxGI_home_per90': 'npxGI/90 🏠',
            'points_home_per90': 'Pts/90 🏠',
            'bps_home_per90': 'BPS/90 🏠',
            'bonus_home_per90': 'Bonus/90 🏠',
            'def_contrib_home_per90': 'DC/90 🏠',
            'goals_home': 'Goals (H)',
            'assists_home': 'Assists (H)',
            'xGI_home': 'xGI (H)',
            'npxG_home': 'npxG (H)',
            'npxGI_home': 'npxGI (H)',
            'points_home': 'Pts (H)',
            'bps_home': 'BPS (H)',
            'bonus_home': 'Bonus (H)',
            'def_contrib_home': 'DC (H)',
            'games_home': 'Games (H)',
            'minutes_home': 'Mins (H)',
            
            'xG_away_per90': 'xG/90 ✈️',
            'xGI_away_per90': 'xGI/90 ✈️',
            'npxG_away_per90': 'npxG/90 ✈️',
            'npxGI_away_per90': 'npxGI/90 ✈️',
            'points_away_per90': 'Pts/90 ✈️',
            'bps_away_per90': 'BPS/90 ✈️',
            'bonus_away_per90': 'Bonus/90 ✈️',
            'def_contrib_away_per90': 'DC/90 ✈️',
            'goals_away': 'Goals (A)',
            'assists_away': 'Assists (A)',
            'xGI_away': 'xGI (A)',
            'npxG_away': 'npxG (A)',
            'npxGI_away': 'npxGI (A)',
            'points_away': 'Pts (A)',
            'bps_away': 'BPS (A)',
            'bonus_away': 'Bonus (A)',
            'def_contrib_away': 'DC (A)',
            'games_away': 'Games (A)',
            'minutes_away': 'Mins (A)',
            
            'home_away_points_diff': 'H/A Pts Diff',
            'home_away_xGI_diff': 'H/A xGI Diff',
            
            'total_xGI': 'xGI',
            'total_npxG': 'npxG',
            'total_npxGI': 'npxGI',
            'goals_scored': 'Goals',
            'assists': 'Assists',
            'goals_last_5': 'Goals L5',
            'assists_last_5': 'Assists L5',
            'xGI_last_5': 'xGI L5',
            'points_last_5': 'Pts L5',
            'bps': 'BPS',
            'bonus': 'Bonus',
            'defensive_contribution': 'DC',
            
            # Understat columns
            'total_shots': 'Shots',
            'shots_per_90': 'Shots/90',
            'shot_conversion': 'Conv%',
            'xG_per_shot': 'xG/Shot',
            'chances_created': 'Chances',
            'chances_created_per_90': 'Chances/90',
            'xGChain': 'xGChain',
            'xGBuildup': 'xGBuildup'
        }
        
        leaderboard_display.columns = [col_name_mapping.get(col, col) for col in leaderboard_display.columns]
        
        format_spec = {
            'Price': '{:.1f}',
            'Points': '{:.0f}',
            'Mins': '{:.0f}',
            'Goals': '{:.0f}',
            'Assists': '{:.0f}',
            'Goals L5': '{:.0f}',
            'Assists L5': '{:.0f}',
            'BPS': '{:.0f}',
            'Bonus': '{:.0f}',
            'DC': '{:.0f}',
            'Goals (H)': '{:.0f}',
            'Assists (H)': '{:.0f}',
            'Goals (A)': '{:.0f}',
            'Assists (A)': '{:.0f}',
            'BPS (H)': '{:.0f}',
            'BPS (A)': '{:.0f}',
            'Bonus (H)': '{:.0f}',
            'Bonus (A)': '{:.0f}',
            'DC (H)': '{:.0f}',
            'DC (A)': '{:.0f}',
            'Games (H)': '{:.0f}',
            'Games (A)': '{:.0f}',
            'Mins (H)': '{:.0f}',
            'Mins (A)': '{:.0f}',
            'Pts (H)': '{:.0f}',
            'Pts (A)': '{:.0f}',
            'Shots': '{:.0f}',
            'Chances': '{:.0f}',
            'Conv%': '{:.1f}'
        }
        
        for col in leaderboard_display.columns:
            if '/90' in col or col in ['xGI', 'xGI L5', 'Pts L5', 'xGI (H)', 'xGI (A)', 
                                       'npxG', 'npxGI', 'npxG (H)', 'npxG (A)', 
                                       'npxGI (H)', 'npxGI (A)', 'H/A Pts Diff', 'H/A xGI Diff',
                                       'xG/Shot', 'xGChain', 'xGBuildup']:
                format_spec[col] = '{:.2f}'
        
        sort_metric_display = col_name_mapping.get(sort_metric, sort_metric)
        
        st.dataframe(
            leaderboard_display.style.format(format_spec).background_gradient(
                subset=[sort_metric_display] if sort_metric_display in leaderboard_display.columns else None, 
                cmap='RdYlGn'
            ),
            use_container_width=True,
            hide_index=True,
            height=600
        )
        
        st.caption(f"Showing {len(leaderboard_display)} players | Sorted by **{sort_metric_label}** | Min {leaderboard_min_mins} minutes")
    else:
        st.info("No players match the current filters. Try adjusting your selections.")


def show_form_trends(df, match_data):
    """Show form trends and hot/cold players"""
    
    st.subheader("🔥 Form Analysis")
    
    df = df.copy()
    
    if 'hot_form' not in df.columns:
        df['hot_form'] = (df['form_trend_points'] > 1.0) & (df['minutes_last_5'] >= 270)
    
    if 'cold_form' not in df.columns:
        df['cold_form'] = (df['form_trend_points'] < -1.0) & (df['minutes_last_5'] >= 270)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Players in Hot Form")
        hot_df = df[df['hot_form'] == True]
        
        if len(hot_df) > 0:
            hot_players = hot_df.nlargest(10, 'form_trend_points')[
                ['player_name', 'position', 'points_per90_season', 'points_per90_last_5', 
                 'form_trend_points', 'minutes_last_5']
            ].copy()
            hot_players.columns = ['Player', 'Pos', 'Season Pts/90', 'Recent Pts/90', 'Trend', 'Mins L5']
            st.dataframe(
                hot_players.style.format({
                    'Season Pts/90': '{:.2f}',
                    'Recent Pts/90': '{:.2f}',
                    'Trend': '{:+.2f}',
                    'Mins L5': '{:.0f}'
                }).background_gradient(subset=['Trend'], cmap='RdYlGn'),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No players currently in hot form (min 3 games, +1.0 pts/90 improvement)")
    
    with col2:
        st.markdown("#### 📉 Cold Form Players")
        cold_df = df[df['cold_form'] == True]
        
        if len(cold_df) > 0:
            cold_players = cold_df.nsmallest(10, 'form_trend_points')[
                ['player_name', 'position', 'points_per90_season', 'points_per90_last_5', 
                 'form_trend_points', 'minutes_last_5']
            ].copy()
            cold_players.columns = ['Player', 'Pos', 'Season Pts/90', 'Recent Pts/90', 'Trend', 'Mins L5']
            st.dataframe(
                cold_players.style.format({
                    'Season Pts/90': '{:.2f}',
                    'Recent Pts/90': '{:.2f}',
                    'Trend': '{:+.2f}',
                    'Mins L5': '{:.0f}'
                }).background_gradient(subset=['Trend'], cmap='RdYlGn'),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No players currently in cold form (min 3 games, -1.0 pts/90 decline)")
    
    st.markdown("---")
    st.markdown("#### 📊 Form Distribution by Position")
    
    form_df = df[df['total_minutes'] >= 450].copy()
    
    if len(form_df) > 0:
        fig = px.box(
            form_df,
            x='position',
            y='form_trend_points',
            color='position',
            points='all',
            hover_data=['player_name', 'points_per90_season', 'points_per90_last_5'],
            labels={
                'form_trend_points': 'Form Trend (Pts/90)',
                'position': 'Position'
            },
            color_discrete_map={
                'FWD': '#e74c3c',
                'MID': '#3498db',
                'DEF': '#2ecc71',
                'GKP': '#f39c12'
            }
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


def show_value_analysis(df):
    """Show value analysis"""
    st.subheader("💎 Value Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Goals vs xG (Overperformers)")
        xg_df = df[(df['total_xG'] >= 1.0) & (df['total_minutes'] >= 450)].copy()
        
        if len(xg_df) > 0:
            fig = px.scatter(
                xg_df,
                x='total_xG',
                y='goals_scored',
                color='xG_overperformance',
                size='total_minutes',
                hover_data=['player_name', 'position', 'price', 'team_short'],
                labels={
                    'total_xG': 'Expected Goals (xG)',
                    'goals_scored': 'Actual Goals',
                    'xG_overperformance': 'xG Overperformance'
                },
                color_continuous_scale='RdYlGn'
            )
            
            max_val = max(xg_df['total_xG'].max(), xg_df['goals_scored'].max())
            fig.add_trace(
                go.Scatter(
                    x=[0, max_val],
                    y=[0, max_val],
                    mode='lines',
                    line=dict(color='gray', dash='dash'),
                    showlegend=False
                )
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("##### Top 5 xG Overperformers")
            top_over = xg_df.nlargest(5, 'xG_overperformance')[
                ['player_name', 'position', 'goals_scored', 'total_xG', 'xG_overperformance']
            ].copy()
            top_over.columns = ['Player', 'Pos', 'Goals', 'xG', 'Diff']
            st.dataframe(
                top_over.style.format({
                    'Goals': '{:.0f}',
                    'xG': '{:.2f}',
                    'Diff': '{:+.2f}'
                }),
                use_container_width=True,
                hide_index=True
            )
    
    with col2:
        st.markdown("#### 📉 Goals vs xG (Underperformers)")
        
        if len(xg_df) > 0:
            st.markdown("##### Top 5 xG Underperformers (Due a Goal)")
            under_df = xg_df[xg_df['xG_overperformance'] < 0]
            if len(under_df) > 0:
                top_under = under_df.nsmallest(5, 'xG_overperformance')[
                    ['player_name', 'position', 'goals_scored', 'total_xG', 'xG_overperformance']
                ].copy()
                top_under.columns = ['Player', 'Pos', 'Goals', 'xG', 'Diff']
                st.dataframe(
                    top_under.style.format({
                        'Goals': '{:.0f}',
                        'xG': '{:.2f}',
                        'Diff': '{:+.2f}'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No significant xG underperformers")
        
        st.markdown("---")
        st.markdown("##### Assists vs xA")
        xa_df = df[(df['total_xA'] >= 1.0) & (df['total_minutes'] >= 450)].copy()
        
        if len(xa_df) > 0:
            top_xa_over = xa_df.nlargest(5, 'xA_overperformance')[
                ['player_name', 'position', 'assists', 'total_xA', 'xA_overperformance']
            ].copy()
            top_xa_over.columns = ['Player', 'Pos', 'Assists', 'xA', 'Diff']
            
            st.markdown("**Top 5 xA Overperformers**")
            st.dataframe(
                top_xa_over.style.format({
                    'Assists': '{:.0f}',
                    'xA': '{:.2f}',
                    'Diff': '{:+.2f}'
                }),
                use_container_width=True,
                hide_index=True
            )
    
    st.markdown("---")
    st.markdown("#### 💰 Points per Million (Efficiency)")
    
    efficiency_df = df[df['total_minutes'] >= 450].copy()
    efficiency_df['pts_per_million'] = efficiency_df['total_points'] / efficiency_df['price']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Best Value Players (All)")
        best_value = efficiency_df.nlargest(10, 'pts_per_million')[
            ['player_name', 'position', 'price', 'total_points', 'pts_per_million']
        ].copy()
        best_value.columns = ['Player', 'Pos', 'Price', 'Points', 'Pts/£m']
        st.dataframe(
            best_value.style.format({
                'Price': '{:.1f}',
                'Points': '{:.0f}',
                'Pts/£m': '{:.1f}'
            }).background_gradient(subset=['Pts/£m'], cmap='YlGn'),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        st.markdown("##### Best Value by Position")
        
        for pos in ['FWD', 'MID', 'DEF']:
            pos_df = efficiency_df[efficiency_df['position'] == pos]
            if len(pos_df) > 0:
                best_pos = pos_df.nlargest(3, 'pts_per_million')[
                    ['player_name', 'price', 'total_points', 'pts_per_million']
                ].copy()
                best_pos.columns = ['Player', 'Price', 'Points', 'Pts/£m']
                
                st.markdown(f"**{pos}**")
                st.dataframe(
                    best_pos.style.format({
                        'Price': '{:.1f}',
                        'Points': '{:.0f}',
                        'Pts/£m': '{:.1f}'
                    }),
                    use_container_width=True,
                    hide_index=True,
                    height=140
                )


# Call the main function
show(player_data, match_data)