"""
Team Analysis Page with xG/xGC Leaderboard
Shows comprehensive team statistics including expected goals metrics

Features:
- Attack vs Defense scatter plot
- Team categories analysis
- Attacking and defensive statistics
- Team comparison
- NEW: Team xG/xGC Leaderboard with custom filtering
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import the team xG calculator
try:
    from utils.team_xg_aggregator import calculate_team_xg_stats, create_team_xg_leaderboard
except ImportError:
    calculate_team_xg_stats = None
    create_team_xg_leaderboard = None

# Page config
st.set_page_config(
    page_title="Team Analysis - FPL Dashboard",
    page_icon="🏆",
    layout="wide"
)

# Check if data is loaded
if 'team_defensive' not in st.session_state or st.session_state.team_defensive is None:
    st.error("❌ No data loaded. Please go to the Home page and download data first.")
    if st.button("🏠 Go to Home"):
        st.switch_page("app.py")
    st.stop()

# Get data from session state - CORRECTED KEYS
defensive_df = st.session_state.team_defensive
attacking_df = st.session_state.team_attacking
match_data = st.session_state.get('match_data')  # May or may not exist

def show(defensive_df, attacking_df, match_data=None):
    """Main function to show team analysis"""
    
    st.title("🏆 Team Analysis")
    st.markdown("Comprehensive team performance metrics and xG analysis")
    
    # Check if data exists
    if defensive_df is None or attacking_df is None:
        st.warning("⚠️ No team data available. Please download data from the sidebar.")
        return
    
    if defensive_df.empty or attacking_df.empty:
        st.warning("⚠️ Team data is empty. This may be because the season hasn't started yet or there was an error fetching data.")
        return
    
    # Calculate team xG stats if match data is available
    team_xg_stats = None
    if match_data is not None and not match_data.empty and calculate_team_xg_stats is not None:
        try:
            team_xg_stats = calculate_team_xg_stats(match_data)
        except Exception as e:
            st.warning(f"⚠️ Could not calculate xG stats: {str(e)}")
            team_xg_stats = None
    
    # Merge defensive and attacking data
    team_df = defensive_df.merge(
        attacking_df,
        on=['team', 'short_name', 'games_played'],
        how='outer',
        suffixes=('_def', '_att')
    )
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        best_attack = team_df.nlargest(1, 'goals_per_game').iloc[0]
        st.metric(
            "⚡ Best Attack",
            best_attack['short_name'],
            f"{best_attack['goals_per_game']:.2f} goals/game"
        )
    
    with col2:
        best_defense = team_df.nsmallest(1, 'goals_conceded_per_game').iloc[0]
        st.metric(
            "🛡️ Best Defense",
            best_defense['short_name'],
            f"{best_defense['goals_conceded_per_game']:.2f} conceded/game"
        )
    
    with col3:
        most_cs = team_df.nlargest(1, 'clean_sheets').iloc[0]
        st.metric(
            "🚫 Most Clean Sheets",
            most_cs['short_name'],
            f"{most_cs['clean_sheets']:.0f} ({most_cs['clean_sheet_%']:.0f}%)"
        )
    
    with col4:
        avg_goals = team_df['goals_per_game'].mean()
        st.metric(
            "📊 Avg Goals/Game",
            f"{avg_goals:.2f}",
            "League average"
        )
    
    st.markdown("---")
    
    # Create tabs - Add xG/xGC leaderboard tab if data is available
    if team_xg_stats is not None and not team_xg_stats.empty:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎯 Overview",
            "⚡ Attacking Stats",
            "🛡️ Defensive Stats",
            "📊 Team Comparison",
            "📈 xG/xGC Leaderboard"
        ])
    else:
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 Overview",
            "⚡ Attacking Stats",
            "🛡️ Defensive Stats",
            "📊 Team Comparison"
        ])
    
    with tab1:
        show_overview(team_df)
    
    with tab2:
        show_attacking_stats(attacking_df)
    
    with tab3:
        show_defensive_stats(defensive_df)
    
    with tab4:
        show_team_comparison(team_df)
    
    # Show xG/xGC leaderboard if data is available
    if team_xg_stats is not None and not team_xg_stats.empty:
        with tab5:
            show_xg_xgc_leaderboard(team_xg_stats)


"""
Updated show_xg_xgc_leaderboard function with Home/Away columns
"""

def show_xg_xgc_leaderboard(team_xg_stats):
    """Show custom xG/xGC leaderboard with filters - ENHANCED with Home/Away splits"""
    
    st.subheader("📈 Team xG/xGC Leaderboard - Top 20 by Metric")
    st.markdown("Analyze teams by expected goals metrics with custom filters")
    
    # Filter controls
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Metric selector
        metric_options = {
            'xG (Total)': 'xG',
            'xGC (Total)': 'xGC',
            'xG per Match (Season)': 'xG_per_match',
            'xGC per Match (Season)': 'xGC_per_match',
            'xG Differential (Total)': 'xG_differential',
            'xG Differential per Match': 'xG_differential_per_match',
            'xG Home (Total)': 'xG_home',
            'xGC Home (Total)': 'xGC_home',
            'xG Home per Match': 'xG_home_per_match',
            'xGC Home per Match': 'xGC_home_per_match',
            'xG Away (Total)': 'xG_away',
            'xGC Away (Total)': 'xGC_away',
            'xG Away per Match': 'xG_away_per_match',
            'xGC Away per Match': 'xGC_away_per_match',
            'xGI (Total)': 'xGI',
            'xGI per Match': 'xGI_per_match'
        }
        
        selected_metric_name = st.selectbox(
            "Sort by Metric",
            options=list(metric_options.keys()),
            index=2  # Default to xG per Match
        )
        
        selected_metric = metric_options[selected_metric_name]
    
    with col2:
        # Minimum matches filter
        min_matches = st.slider(
            "Min Matches Played",
            min_value=1,
            max_value=int(team_xg_stats['matches_played'].max()) if len(team_xg_stats) > 0 else 38,
            value=5,
            step=1
        )
    
    # Filter data
    filtered_stats = team_xg_stats[team_xg_stats['matches_played'] >= min_matches].copy()
    
    if filtered_stats.empty:
        st.warning("No teams match the selected filters")
        return
    
    # Sort by selected metric
    # Determine sort order based on metric type (xGC should be ascending, others descending)
    ascending = 'xGC' in selected_metric and 'differential' not in selected_metric
    leaderboard = create_team_xg_leaderboard(filtered_stats, selected_metric, ascending=ascending, top_n=20)
    
    st.markdown(f"**Showing {len(leaderboard)} teams | Sorted by {selected_metric_name} | Min {min_matches} matches**")
    
    # Display leaderboard table - ENHANCED with Home/Away columns
    display_columns = [
        'team', 'short_name', 'matches_played',
        'xG', 'xGC', 'xG_per_match', 'xGC_per_match',
        'xG_differential', 'xG_differential_per_match',
        # NEW: Home stats
        'xG_home', 'xGC_home', 'xG_home_per_match', 'xGC_home_per_match',
        # NEW: Away stats
        'xG_away', 'xGC_away', 'xG_away_per_match', 'xGC_away_per_match'
    ]
    
    # Only include columns that exist
    display_columns = [col for col in display_columns if col in leaderboard.columns]
    
    display_df = leaderboard[display_columns].copy()
    
    # Rename columns for better display
    display_df.columns = [
        'Team', 'Short', 'Matches', 
        'xG', 'xGC', 'xG/M', 'xGC/M', 
        'xG Diff', 'xG Diff/M',
        # Home
        'xG Home', 'xGC Home', 'xG/M Home', 'xGC/M Home',
        # Away
        'xG Away', 'xGC Away', 'xG/M Away', 'xGC/M Away'
    ]
    
    # Create color gradient for the sorted column
    if 'xGC' in selected_metric:
        # For xGC metrics, lower is better (green)
        cmap = 'RdYlGn_r'
    else:
        # For xG metrics, higher is better (green)
        cmap = 'RdYlGn'
    
    # Find which display column corresponds to the selected metric
    metric_map = {
        'xG': 'xG',
        'xGC': 'xGC',
        'xG_per_match': 'xG/M',
        'xGC_per_match': 'xGC/M',
        'xG_differential': 'xG Diff',
        'xG_differential_per_match': 'xG Diff/M',
        'xG_home': 'xG Home',
        'xGC_home': 'xGC Home',
        'xG_home_per_match': 'xG/M Home',
        'xGC_home_per_match': 'xGC/M Home',
        'xG_away': 'xG Away',
        'xGC_away': 'xGC Away',
        'xG_away_per_match': 'xG/M Away',
        'xGC_away_per_match': 'xGC/M Away'
    }
    
    gradient_col = metric_map.get(selected_metric)
    
    # Format all numeric columns
    format_dict = {
        'xG': '{:.2f}',
        'xGC': '{:.2f}',
        'xG/M': '{:.2f}',
        'xGC/M': '{:.2f}',
        'xG Diff': '{:.2f}',
        'xG Diff/M': '{:.2f}',
        'xG Home': '{:.2f}',
        'xGC Home': '{:.2f}',
        'xG/M Home': '{:.2f}',
        'xGC/M Home': '{:.2f}',
        'xG Away': '{:.2f}',
        'xGC Away': '{:.2f}',
        'xG/M Away': '{:.2f}',
        'xGC/M Away': '{:.2f}'
    }
    
    styled_df = display_df.style.format(format_dict)
    
    if gradient_col and gradient_col in display_df.columns:
        styled_df = styled_df.background_gradient(subset=[gradient_col], cmap=cmap)
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=700
    )
    
    # Show visualizations
    st.markdown("---")
    st.markdown("#### 📊 Visual Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # xG per Match bar chart
        fig1 = go.Figure()
        
        top_10_xg = leaderboard.nlargest(10, 'xG_per_match')
        
        fig1.add_trace(go.Bar(
            x=top_10_xg['short_name'],
            y=top_10_xg['xG_per_match'],
            marker_color='#2ecc71',
            text=top_10_xg['xG_per_match'].round(2),
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>xG/Match: %{y:.2f}<extra></extra>'
        ))
        
        fig1.update_layout(
            title="Top 10 Teams by xG per Match",
            xaxis_title="Team",
            yaxis_title="xG per Match",
            height=400
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # xGC per Match bar chart
        fig2 = go.Figure()
        
        bottom_10_xgc = leaderboard.nsmallest(10, 'xGC_per_match')
        
        fig2.add_trace(go.Bar(
            x=bottom_10_xgc['short_name'],
            y=bottom_10_xgc['xGC_per_match'],
            marker_color='#3498db',
            text=bottom_10_xgc['xGC_per_match'].round(2),
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>xGC/Match: %{y:.2f}<extra></extra>'
        ))
        
        fig2.update_layout(
            title="Top 10 Teams by xGC per Match (Lower is Better)",
            xaxis_title="Team",
            yaxis_title="xGC per Match",
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    # xG vs xGC scatter plot
    st.markdown("#### Attack vs Defense - Expected Goals")
    
    fig3 = px.scatter(
        leaderboard,
        x='xGC_per_match',
        y='xG_per_match',
        size='matches_played',
        color='xG_differential_per_match',
        hover_name='team',
        hover_data={
            'xG_per_match': ':.2f',
            'xGC_per_match': ':.2f',
            'matches_played': True,
            'xG_differential_per_match': ':.2f'
        },
        labels={
            'xGC_per_match': 'xGC per Match (Lower is Better)',
            'xG_per_match': 'xG per Match',
            'xG_differential_per_match': 'xG Differential/Match'
        },
        title='Team xG vs xGC Performance Map',
        color_continuous_scale='RdYlGn',
        color_continuous_midpoint=0
    )
    
    # Add quadrant lines
    avg_xg = leaderboard['xG_per_match'].mean()
    avg_xgc = leaderboard['xGC_per_match'].mean()
    
    fig3.add_hline(y=avg_xg, line_dash="dash", line_color="gray",
                  annotation_text="Avg xG", annotation_position="right")
    fig3.add_vline(x=avg_xgc, line_dash="dash", line_color="gray",
                  annotation_text="Avg xGC", annotation_position="top")
    
    # Add team labels
    for _, row in leaderboard.iterrows():
        fig3.add_annotation(
            x=row['xGC_per_match'],
            y=row['xG_per_match'],
            text=row['short_name'],
            showarrow=False,
            yshift=15,
            font=dict(size=9)
        )
    
    fig3.update_layout(height=600)
    st.plotly_chart(fig3, use_container_width=True)
    
    # Home vs Away comparison - ENHANCED
    st.markdown("---")
    st.markdown("#### 🏠 ✈️ Home vs Away xG Performance - Detailed")
    
    # Add summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_home_xg = leaderboard['xG_home_per_match'].mean()
        st.metric("Avg Home xG/Match", f"{avg_home_xg:.2f}", "League average")
    
    with col2:
        avg_away_xg = leaderboard['xG_away_per_match'].mean()
        st.metric("Avg Away xG/Match", f"{avg_away_xg:.2f}", "League average")
    
    with col3:
        avg_home_xgc = leaderboard['xGC_home_per_match'].mean()
        st.metric("Avg Home xGC/Match", f"{avg_home_xgc:.2f}", "League average")
    
    with col4:
        avg_away_xgc = leaderboard['xGC_away_per_match'].mean()
        st.metric("Avg Away xGC/Match", f"{avg_away_xgc:.2f}", "League average")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top Home xG/Match**")
        home_leaders = leaderboard.nlargest(10, 'xG_home_per_match')[
            ['short_name', 'home_matches', 'xG_home', 'xG_home_per_match', 'xGC_home_per_match']
        ].copy()
        home_leaders.columns = ['Team', 'Home Games', 'Total xG', 'xG/Match', 'xGC/Match']
        
        st.dataframe(
            home_leaders.style.format({
                'Total xG': '{:.2f}',
                'xG/Match': '{:.2f}',
                'xGC/Match': '{:.2f}'
            }).background_gradient(subset=['xG/Match'], cmap='RdYlGn'),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        st.markdown("**Top Away xG/Match**")
        away_leaders = leaderboard.nlargest(10, 'xG_away_per_match')[
            ['short_name', 'away_matches', 'xG_away', 'xG_away_per_match', 'xGC_away_per_match']
        ].copy()
        away_leaders.columns = ['Team', 'Away Games', 'Total xG', 'xG/Match', 'xGC/Match']
        
        st.dataframe(
            away_leaders.style.format({
                'Total xG': '{:.2f}',
                'xG/Match': '{:.2f}',
                'xGC/Match': '{:.2f}'
            }).background_gradient(subset=['xG/Match'], cmap='RdYlGn'),
            use_container_width=True,
            hide_index=True
        )
    
    # NEW: Best Home Defenses vs Best Away Defenses
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏠 Best Home Defenses (Low xGC)**")
        home_defense = leaderboard.nsmallest(10, 'xGC_home_per_match')[
            ['short_name', 'home_matches', 'xGC_home', 'xGC_home_per_match']
        ].copy()
        home_defense.columns = ['Team', 'Home Games', 'Total xGC', 'xGC/Match']
        
        st.dataframe(
            home_defense.style.format({
                'Total xGC': '{:.2f}',
                'xGC/Match': '{:.2f}'
            }).background_gradient(subset=['xGC/Match'], cmap='RdYlGn_r'),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        st.markdown("**✈️ Best Away Defenses (Low xGC)**")
        away_defense = leaderboard.nsmallest(10, 'xGC_away_per_match')[
            ['short_name', 'away_matches', 'xGC_away', 'xGC_away_per_match']
        ].copy()
        away_defense.columns = ['Team', 'Away Games', 'Total xGC', 'xGC/Match']
        
        st.dataframe(
            away_defense.style.format({
                'Total xGC': '{:.2f}',
                'xGC/Match': '{:.2f}'
            }).background_gradient(subset=['xGC/Match'], cmap='RdYlGn_r'),
            use_container_width=True,
            hide_index=True
        )

def show_overview(df):
    """Show overview with scatter plot and key insights"""
    
    st.subheader("Team Performance Overview")
    
    # Attack vs Defense scatter
    fig = px.scatter(
        df,
        x='goals_conceded_per_game',
        y='goals_per_game',
        size='games_played',
        color='goals_per_game',
        hover_name='team',
        hover_data={
            'goals_per_game': ':.2f',
            'goals_conceded_per_game': ':.2f',
            'games_played': True,
            'clean_sheets': True
        },
        labels={
            'goals_conceded_per_game': 'Goals Conceded per Game (Lower is Better)',
            'goals_per_game': 'Goals Scored per Game',
            'goals_per_game_color': 'Attack Rating'
        },
        title='Attack vs Defense: Team Performance Map',
        color_continuous_scale='RdYlGn'
    )
    
    # Add quadrant lines
    avg_attack = df['goals_per_game'].mean()
    avg_defense = df['goals_conceded_per_game'].mean()
    
    fig.add_hline(y=avg_attack, line_dash="dash", line_color="gray", 
                  annotation_text="Avg Attack", annotation_position="right")
    fig.add_vline(x=avg_defense, line_dash="dash", line_color="gray",
                  annotation_text="Avg Defense", annotation_position="top")
    
    # Add team labels
    for _, row in df.iterrows():
        fig.add_annotation(
            x=row['goals_conceded_per_game'],
            y=row['goals_per_game'],
            text=row['short_name'],
            showarrow=False,
            yshift=15,
            font=dict(size=9)
        )
    
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # Quadrant analysis
    st.markdown("#### 🎯 Team Categories")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Strong teams (good attack, good defense)
        strong = df[
            (df['goals_per_game'] > avg_attack) & 
            (df['goals_conceded_per_game'] < avg_defense)
        ].sort_values('goals_per_game', ascending=False)
        
        st.success("**💪 Strong Teams** (Good Attack + Defense)")
        if len(strong) > 0:
            st.dataframe(
                strong[['team', 'goals_per_game', 'goals_conceded_per_game', 'clean_sheet_%']],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No teams in this category")
    
    with col2:
        # Vulnerable teams (weak attack, weak defense)
        vulnerable = df[
            (df['goals_per_game'] < avg_attack) & 
            (df['goals_conceded_per_game'] > avg_defense)
        ].sort_values('goals_conceded_per_game', ascending=False)
        
        st.error("**⚠️ Vulnerable Teams** (Weak Attack + Defense)")
        if len(vulnerable) > 0:
            st.dataframe(
                vulnerable[['team', 'goals_per_game', 'goals_conceded_per_game', 'clean_sheet_%']],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No teams in this category")
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Attack-focused
        attack_focused = df[
            (df['goals_per_game'] > avg_attack) & 
            (df['goals_conceded_per_game'] > avg_defense)
        ].sort_values('goals_per_game', ascending=False)
        
        st.warning("**⚡ Attack-Focused** (High Scoring)")
        if len(attack_focused) > 0:
            st.dataframe(
                attack_focused[['team', 'goals_per_game', 'goals_conceded_per_game']],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No teams in this category")
    
    with col4:
        # Defense-focused
        defense_focused = df[
            (df['goals_per_game'] < avg_attack) & 
            (df['goals_conceded_per_game'] < avg_defense)
        ].sort_values('goals_conceded_per_game')
        
        st.info("**🛡️ Defense-Focused** (Low Scoring)")
        if len(defense_focused) > 0:
            st.dataframe(
                defense_focused[['team', 'goals_per_game', 'goals_conceded_per_game', 'clean_sheets']],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No teams in this category")


def show_attacking_stats(df):
    """Show attacking statistics"""
    
    st.subheader("⚡ Attacking Performance")
    
    # Sort by goals per game
    df_sorted = df.sort_values('goals_per_game', ascending=False).reset_index(drop=True)
    
    # Bar chart - Goals per game
    fig = go.Figure()
    
    # Color bars based on performance
    colors = ['#27ae60' if x > df['goals_per_game'].mean() else '#e74c3c' 
              for x in df_sorted['goals_per_game']]
    
    fig.add_trace(go.Bar(
        x=df_sorted['short_name'],
        y=df_sorted['goals_per_game'],
        marker_color=colors,
        text=df_sorted['goals_per_game'].round(2),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>' +
                      'Goals/Game: %{y:.2f}<br>' +
                      '<extra></extra>'
    ))
    
    # Add average line
    avg = df['goals_per_game'].mean()
    fig.add_hline(y=avg, line_dash="dash", line_color="gray",
                  annotation_text=f"Avg: {avg:.2f}", annotation_position="right")
    
    fig.update_layout(
        title='Goals Scored per Game',
        xaxis_title='Team',
        yaxis_title='Goals per Game',
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed attacking table
    st.markdown("#### 📊 Detailed Attacking Stats")
    
    display_df = df_sorted[['team', 'short_name', 'games_played', 'goals_scored', 'goals_per_game']].copy()
    display_df.columns = ['Team', 'Short', 'Games', 'Total Goals', 'Goals/Game']
    
    st.dataframe(
        display_df.style.format({
            'Games': '{:.0f}',
            'Total Goals': '{:.0f}',
            'Goals/Game': '{:.2f}'
        }).background_gradient(subset=['Goals/Game'], cmap='RdYlGn'),
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Top 5 and Bottom 5
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⚡ Best Attacks")
        top_5 = df_sorted.head(5)[['team', 'goals_per_game', 'goals_scored']]
        top_5.columns = ['Team', 'Goals/Game', 'Total']
        st.dataframe(
            top_5.style.format({'Goals/Game': '{:.2f}', 'Total': '{:.0f}'}),
            hide_index=True,
            use_container_width=True
        )
    
    with col2:
        st.markdown("#### 🔻 Weakest Attacks")
        bottom_5 = df_sorted.tail(5)[['team', 'goals_per_game', 'goals_scored']]
        bottom_5.columns = ['Team', 'Goals/Game', 'Total']
        st.dataframe(
            bottom_5.style.format({'Goals/Game': '{:.2f}', 'Total': '{:.0f}'}),
            hide_index=True,
            use_container_width=True
        )


def show_defensive_stats(df):
    """Show defensive statistics"""
    
    st.subheader("🛡️ Defensive Performance")
    
    # Sort by goals conceded (ascending = best defense)
    df_sorted = df.sort_values('goals_conceded_per_game').reset_index(drop=True)
    
    # Bar chart - Goals conceded per game (inverted for better visualization)
    fig = go.Figure()
    
    # Color bars based on performance
    avg_conceded = df['goals_conceded_per_game'].mean()
    colors = ['#27ae60' if x < avg_conceded else '#e74c3c' 
              for x in df_sorted['goals_conceded_per_game']]
    
    fig.add_trace(go.Bar(
        x=df_sorted['short_name'],
        y=df_sorted['goals_conceded_per_game'],
        marker_color=colors,
        text=df_sorted['goals_conceded_per_game'].round(2),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>' +
                      'Conceded/Game: %{y:.2f}<br>' +
                      '<extra></extra>'
    ))
    
    # Add average line
    fig.add_hline(y=avg_conceded, line_dash="dash", line_color="gray",
                  annotation_text=f"Avg: {avg_conceded:.2f}", annotation_position="right")
    
    fig.update_layout(
        title='Goals Conceded per Game (Lower is Better)',
        xaxis_title='Team',
        yaxis_title='Goals Conceded per Game',
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Clean sheets chart
    st.markdown("#### 🚫 Clean Sheets")
    
    fig2 = go.Figure()
    
    df_cs = df.sort_values('clean_sheets', ascending=False)
    
    fig2.add_trace(go.Bar(
        x=df_cs['short_name'],
        y=df_cs['clean_sheets'],
        marker_color='#3498db',
        text=df_cs['clean_sheets'],
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>' +
                      'Clean Sheets: %{y}<br>' +
                      'CS Rate: ' + df_cs['clean_sheet_%'].round(1).astype(str) + '%<br>' +
                      '<extra></extra>'
    ))
    
    fig2.update_layout(
        title='Clean Sheets',
        xaxis_title='Team',
        yaxis_title='Clean Sheets',
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Detailed defensive table
    st.markdown("#### 📊 Detailed Defensive Stats")
    
    display_df = df_sorted[['team', 'short_name', 'games_played', 'goals_conceded', 
                             'goals_conceded_per_game', 'clean_sheets', 'clean_sheet_%']].copy()
    display_df.columns = ['Team', 'Short', 'Games', 'Total Conceded', 'Conceded/Game', 'CS', 'CS %']
    
    st.dataframe(
        display_df.style.format({
            'Games': '{:.0f}',
            'Total Conceded': '{:.0f}',
            'Conceded/Game': '{:.2f}',
            'CS': '{:.0f}',
            'CS %': '{:.1f}%'
        }).background_gradient(subset=['Conceded/Game'], cmap='RdYlGn_r'),
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Top 5 and Bottom 5
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🛡️ Best Defenses")
        top_5 = df_sorted.head(5)[['team', 'goals_conceded_per_game', 'clean_sheets', 'clean_sheet_%']]
        top_5.columns = ['Team', 'Conceded/Game', 'CS', 'CS %']
        st.dataframe(
            top_5.style.format({
                'Conceded/Game': '{:.2f}',
                'CS': '{:.0f}',
                'CS %': '{:.1f}%'
            }),
            hide_index=True,
            use_container_width=True
        )
    
    with col2:
        st.markdown("#### 🔻 Weakest Defenses")
        bottom_5 = df_sorted.tail(5)[['team', 'goals_conceded_per_game', 'clean_sheets', 'clean_sheet_%']]
        bottom_5.columns = ['Team', 'Conceded/Game', 'CS', 'CS %']
        st.dataframe(
            bottom_5.style.format({
                'Conceded/Game': '{:.2f}',
                'CS': '{:.0f}',
                'CS %': '{:.1f}%'
            }),
            hide_index=True,
            use_container_width=True
        )


def show_team_comparison(df):
    """Show head-to-head team comparison"""
    
    st.subheader("📊 Team Comparison")
    st.markdown("Select two teams to compare head-to-head")
    
    col1, col2 = st.columns(2)
    
    with col1:
        team1 = st.selectbox("Select Team 1", df['team'].tolist(), key='team1')
    
    with col2:
        team2 = st.selectbox("Select Team 2", df['team'].tolist(), key='team2', 
                            index=1 if len(df) > 1 else 0)
    
    if team1 == team2:
        st.warning("Please select different teams")
        return
    
    t1_data = df[df['team'] == team1].iloc[0]
    t2_data = df[df['team'] == team2].iloc[0]
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {team1}")
        st.markdown(f"**{t1_data['short_name']}**")
        
        st.metric("Goals/Game", f"{t1_data['goals_per_game']:.2f}")
        st.metric("Conceded/Game", f"{t1_data['goals_conceded_per_game']:.2f}")
        st.metric("Clean Sheets", f"{t1_data['clean_sheets']:.0f} ({t1_data['clean_sheet_%']:.0f}%)")
        st.metric("Games Played", f"{t1_data['games_played']:.0f}")
    
    with col2:
        st.markdown(f"### {team2}")
        st.markdown(f"**{t2_data['short_name']}**")
        
        delta1 = t2_data['goals_per_game'] - t1_data['goals_per_game']
        st.metric("Goals/Game", f"{t2_data['goals_per_game']:.2f}", 
                 f"{delta1:+.2f}", delta_color="normal")
        
        delta2 = t2_data['goals_conceded_per_game'] - t1_data['goals_conceded_per_game']
        st.metric("Conceded/Game", f"{t2_data['goals_conceded_per_game']:.2f}",
                 f"{delta2:+.2f}", delta_color="inverse")
        
        delta3 = t2_data['clean_sheets'] - t1_data['clean_sheets']
        st.metric("Clean Sheets", f"{t2_data['clean_sheets']:.0f} ({t2_data['clean_sheet_%']:.0f}%)",
                 f"{delta3:+.0f}")
        
        st.metric("Games Played", f"{t2_data['games_played']:.0f}")
    
    # Comparison chart
    st.markdown("---")
    st.markdown("#### Head-to-Head Comparison")
    
    metrics = ['goals_per_game', 'goals_conceded_per_game', 'clean_sheet_%', 'goals_scored', 'goals_conceded']
    metric_labels = ['Goals/Game', 'Conceded/Game', 'CS %', 'Total Goals', 'Total Conceded']
    
    fig = make_subplots(rows=1, cols=2, subplot_titles=(team1, team2))
    
    fig.add_trace(
        go.Bar(
            x=metric_labels,
            y=[t1_data[m] for m in metrics],
            name=team1,
            marker_color='#3498db'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=metric_labels,
            y=[t2_data[m] for m in metrics],
            name=team2,
            marker_color='#e74c3c'
        ),
        row=1, col=2
    )
    
    fig.update_layout(height=400, showlegend=False)
    fig.update_xaxes(tickangle=45)
    
    st.plotly_chart(fig, use_container_width=True)


# Call the main show function
show(defensive_df, attacking_df, match_data)