"""
Team Analysis Page
Detailed team defensive and attacking statistics
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

# Get data from session state
defensive_df = st.session_state.team_defensive
attacking_df = st.session_state.team_attacking

def show(defensive_df, attacking_df):
    """Display team analysis page"""
    
    st.header("🏆 Team Analysis")
    st.markdown("Analyze team defensive vulnerability and attacking form")
    st.markdown("---")
    
    if defensive_df is None or attacking_df is None:
        st.error("❌ Team data not available. Please download data from the sidebar.")
        return
    
    if defensive_df.empty or attacking_df.empty:
        st.warning("⚠️ Team data is empty. This may be because the season hasn't started yet or there was an error fetching data.")
        return
    
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
    
    # Create tabs
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
            'goals_conceded_per_game': 'Goals Conceded per Game',
            'goals_per_game': 'Goals Scored per Game',
            'team': 'Team'
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
    display_df.columns = ['Team', 'Short', 'Games', 'Conceded', 'Conceded/Game', 'CS', 'CS %']
    
    st.dataframe(
        display_df.style.format({
            'Games': '{:.0f}',
            'Conceded': '{:.0f}',
            'Conceded/Game': '{:.2f}',
            'CS': '{:.0f}',
            'CS %': '{:.1f}'
        }).background_gradient(subset=['Conceded/Game'], cmap='RdYlGn_r')
          .background_gradient(subset=['CS %'], cmap='Greens'),
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Top 5 and Bottom 5 defenses
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🛡️ Best Defenses")
        top_5 = df_sorted.head(5)[['team', 'goals_conceded_per_game', 'clean_sheet_%']]
        top_5.columns = ['Team', 'Conceded/Game', 'CS %']
        st.dataframe(
            top_5.style.format({'Conceded/Game': '{:.2f}', 'CS %': '{:.1f}'}),
            hide_index=True,
            use_container_width=True
        )
    
    with col2:
        st.markdown("#### 🎯 Most Vulnerable")
        bottom_5 = df_sorted.tail(5).sort_values('goals_conceded_per_game', ascending=False)[
            ['team', 'goals_conceded_per_game', 'clean_sheet_%']
        ]
        bottom_5.columns = ['Team', 'Conceded/Game', 'CS %']
        st.dataframe(
            bottom_5.style.format({'Conceded/Game': '{:.2f}', 'CS %': '{:.1f}'}),
            hide_index=True,
            use_container_width=True
        )

def show_team_comparison(df):
    """Show side-by-side team comparison"""
    
    st.subheader("📊 Compare Teams")
    
    # Team selection
    team_list = sorted(df['team'].unique())
    
    col1, col2 = st.columns(2)
    
    with col1:
        team1 = st.selectbox("Select Team 1", team_list, key="team1")
    
    with col2:
        default_idx = 1 if len(team_list) > 1 else 0
        team2 = st.selectbox("Select Team 2", team_list, index=default_idx, key="team2")
    
    if team1 == team2:
        st.warning("Please select different teams to compare")
        return
    
    # Get team data
    t1_data = df[df['team'] == team1].iloc[0]
    t2_data = df[df['team'] == team2].iloc[0]
    
    st.markdown("---")
    
    # Quick comparison
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
show(defensive_df, attacking_df)
