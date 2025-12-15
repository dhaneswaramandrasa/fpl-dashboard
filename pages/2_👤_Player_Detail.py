"""
Player Detail Page - Individual Player Statistics and Match History
Shows comprehensive stats for a single selected player
Version: 3.0 - Recent first, Totals/Per90, Full fixtures with FDR
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

def show(player_data, match_data):
    """Display player detail page"""
    
    if player_data is None or player_data.empty:
        st.error("❌ No player data available. Please download data from the sidebar.")
        return
    
    st.header("👤 Player Detail")
    st.markdown("Detailed statistics and match history for individual players")
    st.markdown("---")
    
    # Filters in sidebar
    with st.sidebar:
        st.markdown("### 🔧 Player Filters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Position filter
            unique_positions = player_data['position'].dropna().unique().tolist()
            selected_position = st.selectbox(
                "Position",
                ["All"] + sorted(unique_positions),
                key="detail_position"
            )
        
        with col2:
            # Team filter
            if 'team' in player_data.columns:
                unique_teams = player_data['team'].dropna().astype(str).unique().tolist()
                selected_team = st.selectbox(
                    "Team",
                    ["All"] + sorted(unique_teams),
                    key="detail_team"
                )
            else:
                selected_team = "All"
        
        # Price filter (if available)
        if 'price' in player_data.columns or 'player_price' in player_data.columns:
            price_col = 'price' if 'price' in player_data.columns else 'player_price'
            player_data[price_col] = pd.to_numeric(player_data[price_col], errors='coerce').fillna(0)
            
            min_price = float(player_data[price_col].min())
            max_price = float(player_data[price_col].max())
            
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
    
    # Filter player list
    filtered_players = player_data.copy()
    
    if selected_position != "All":
        filtered_players = filtered_players[filtered_players['position'] == selected_position]
    
    if selected_team != "All":
        if 'team' in filtered_players.columns:
            filtered_players = filtered_players[filtered_players['team'] == selected_team]
    
    if price_range:
        price_col = 'price' if 'price' in filtered_players.columns else 'player_price'
        filtered_players = filtered_players[
            (filtered_players[price_col] >= price_range[0]) &
            (filtered_players[price_col] <= price_range[1])
        ]
    
    # Player selection
    player_list = sorted(filtered_players['full_name'].unique())
    
    if not player_list:
        st.warning("No players match the selected filters")
        return
    
    selected_player = st.selectbox(
        "Select Player",
        player_list,
        key="player_detail_select"
    )
    
    if not selected_player:
        st.info("👆 Please select a player to view details")
        return
    
    # Get player data
    player_info = player_data[player_data['full_name'] == selected_player].iloc[0]
    
    # Player header with key info
    st.markdown("---")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"### {player_info['full_name']}")
        st.caption(f"**{player_info['position']}**")
    
    with col2:
        if 'team' in player_info.index or 'player_team' in player_info.index:
            team = player_info.get('team', player_info.get('player_team', 'N/A'))
            st.metric("Team", team)
        else:
            st.metric("Team", "N/A")
    
    with col3:
        if 'price' in player_info.index or 'player_price' in player_info.index:
            price = player_info.get('price', player_info.get('player_price', 0))
            st.metric("Price", f"£{price:.1f}m")
        else:
            st.metric("Price", "N/A")
    
    with col4:
        st.metric("Total Points", f"{player_info['total_points']:.0f}")
    
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

def show_season_stats(recent_matches, player_info):
    """Show this season's match history with totals and per 90"""
    
    st.markdown("#### This Season")
    st.caption(f"Showing {len(recent_matches)} matches (Most recent first)")
    
    # Prepare display dataframe
    display_df = recent_matches.copy()
    
    # Build the OPP column with home/away indicator
    try:
        if 'opponent_short' in display_df.columns:
            display_df['OPP'] = display_df.apply(
                lambda x: f"{x['opponent_short']} ({'H' if x.get('was_home', True) else 'A'})",
                axis=1
            )
        elif 'opponent_team' in display_df.columns:
            display_df['OPP'] = display_df.apply(
                lambda x: f"{x['opponent_team']} ({'H' if x.get('was_home', True) else 'A'})",
                axis=1
            )
        else:
            display_df['OPP'] = 'N/A'
    except Exception as e:
        display_df['OPP'] = 'N/A'
    
    # Add win/loss/draw indicator
    try:
        if 'was_home' in display_df.columns and 'team_h_score' in display_df.columns:
            def get_result(row):
                if pd.isna(row['team_h_score']) or pd.isna(row['team_a_score']):
                    return ''
                if row['was_home']:
                    if row['team_h_score'] > row['team_a_score']:
                        return 'W'
                    elif row['team_h_score'] < row['team_a_score']:
                        return 'L'
                    else:
                        return 'D'
                else:
                    if row['team_a_score'] > row['team_h_score']:
                        return 'W'
                    elif row['team_a_score'] < row['team_h_score']:
                        return 'L'
                    else:
                        return 'D'
            
            display_df['Result'] = display_df.apply(get_result, axis=1)
        else:
            display_df['Result'] = ''
    except:
        display_df['Result'] = ''
    
    # Create column mapping based on screenshot
    column_mapping = {
        'round': 'GW',
        'OPP': 'OPP',
        'Result': 'ST',  # Status (W/L/D)
        'minutes': 'MP',  # Minutes Played
        'goals_scored': 'GS',
        'assists': 'A',
        'expected_goals': 'xG',
        'expected_assists': 'xA',
        'expected_goal_involvements': 'xGI',
        'clean_sheets': 'CS',
        'goals_conceded': 'GC',
        'expected_goals_conceded': 'xGC',
        'tackles': 'T',
        'clearances_blocks_interceptions': 'CBI',
        'recoveries': 'R',
        'defensive_contribution': 'DC',
        'own_goals': 'OG',
        'total_points': 'PTS',
        'bps': 'BPS',
        'bonus': 'B'
    }
    
    # Select available columns
    available_cols = []
    new_col_names = []
    for old_col, new_col in column_mapping.items():
        if old_col in display_df.columns:
            available_cols.append(old_col)
            new_col_names.append(new_col)
    
    # Keep only available columns
    display_df = display_df[available_cols].copy()
    display_df.columns = new_col_names
    
    # Calculate Totals row
    totals_row = {}
    totals_row['GW'] = 'Totals'
    
    for col in display_df.columns[1:]:  # Skip GW column
        if col in ['OPP', 'ST']:
            totals_row[col] = '-'
        else:
            try:
                totals_row[col] = display_df[col].sum()
            except:
                totals_row[col] = '-'
    
    # Calculate Per 90 row
    per90_row = {}
    per90_row['GW'] = 'Per 90'
    total_minutes = totals_row.get('MP', 0)
    
    for col in display_df.columns[1:]:  # Skip GW column
        if col in ['OPP', 'ST', 'MP']:
            per90_row[col] = '-'
        else:
            try:
                if total_minutes > 0:
                    per90_row[col] = round((totals_row[col] * 90) / total_minutes, 2)
                else:
                    per90_row[col] = 0
            except:
                per90_row[col] = '-'
    
    # Add totals and per 90 rows to dataframe
    totals_df = pd.DataFrame([totals_row])
    per90_df = pd.DataFrame([per90_row])
    final_df = pd.concat([display_df, totals_df, per90_df], ignore_index=True)
    
    # Display the table
    st.dataframe(
        final_df,
        use_container_width=True,
        hide_index=True,
        height=min(600, len(final_df) * 35 + 38)
    )
    
    # Performance charts
    st.markdown("---")
    st.markdown("#### Performance Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Points trend (reversed for chronological order in chart)
        chart_df = display_df[display_df['GW'] != 'Totals'].copy()
        chart_df = chart_df[chart_df['GW'] != 'Per 90']
        chart_df = chart_df.sort_values('GW')
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=chart_df['GW'],
            y=chart_df['PTS'],
            mode='lines+markers',
            name='Points',
            line=dict(color='#3498db', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='FPL Points by Gameweek',
            xaxis_title='Gameweek',
            yaxis_title='Points',
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Goal contributions
        if 'GS' in chart_df.columns and 'A' in chart_df.columns:
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=chart_df['GW'],
                y=chart_df['GS'],
                name='Goals',
                marker_color='#e74c3c'
            ))
            
            fig.add_trace(go.Bar(
                x=chart_df['GW'],
                y=chart_df['A'],
                name='Assists',
                marker_color='#3498db'
            ))
            
            fig.update_layout(
                title='Goal Contributions',
                xaxis_title='Gameweek',
                yaxis_title='Count',
                barmode='stack',
                height=350
            )
            
            st.plotly_chart(fig, use_container_width=True)

# Call the main show function
show(player_data, match_data)