"""
Fixture Analysis Page
Analyze upcoming fixtures and rank teams by fixture difficulty
UPDATED: Calendar first, improved colors, skip nearly-complete gameweeks
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

from utils.fixture_analyzer import analyze_fixtures

# Page config
st.set_page_config(
    page_title="Fixture Analysis - FPL Dashboard",
    page_icon="📅",
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

def show(defensive_df, attacking_df):
    """Display fixture analysis page"""
    
    st.header("📅 Fixture Analysis")
    st.markdown("Analyze upcoming fixtures and find teams with the best fixture runs")
    st.markdown("---")
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("### 🔧 Fixture Settings")
        
        next_n_gw = st.selectbox(
            "Number of Fixtures",
            [3, 5, 8, 10],
            index=1,
            help="Analyze next N gameweeks"
        )
        
        st.markdown("---")
        st.markdown("### 📊 FDR Scale (1-5)")
        st.markdown("""
        **Color Guide:**
        - 🟦 **1.0-2.0**: Easy
        - 🟦 **2.0-2.5**: Moderate-Easy  
        - ⬜ **2.5-3.0**: Medium
        - 🟪 **3.0-4.0**: Difficult
        - 🟥 **4.0-5.0**: Very Hard
        
        **Heatmap:**
        - CAPITAL = Home (e.g., BOU)
        - lowercase = Away (e.g., bou)
        
        **Factors:**
        - Opponent strength (40%)
        - Home/Away (20%)
        - Opponent defense (20%)
        - Opponent attack (10%)
        - Team form (10%)
        """)
    
    # Analyze fixtures
    with st.spinner("Analyzing upcoming fixtures..."):
        fixture_data = analyze_fixtures(
            next_n_gameweeks=next_n_gw,
            defensive_df=defensive_df,
            attacking_df=attacking_df
        )
    
    team_fixtures = fixture_data['team_fixtures']
    detailed_fixtures = fixture_data['detailed_fixtures']
    current_gw = fixture_data['current_gw']
    
    if team_fixtures.empty:
        st.warning("⚠️ No upcoming fixtures available")
        st.info(f"Current gameweek detected: GW{current_gw if current_gw else 'Unknown'}")
        st.info("This may be because:")
        st.markdown("""
        - The season hasn't started yet
        - There's an international break
        - The FPL API is not returning fixture data
        - Try refreshing your data from the home page
        """)
        return
    
    # Add expander to show raw fixture data for verification
    with st.expander("🔍 Verify Fixture Data (click to expand)", expanded=False):
        st.markdown(f"**Current Gameweek:** GW{current_gw}")
        st.markdown(f"**Analyzing:** GW{current_gw} to GW{current_gw + next_n_gw - 1}")
        st.markdown("**Sample Team Fixtures:**")
        
        # Show sample for a few teams
        sample_teams = team_fixtures.head(3)
        for _, team in sample_teams.iterrows():
            st.markdown(f"**{team['team']}:** {team['fixtures']}")
        
        st.markdown("**All Upcoming Fixtures (Raw Data):**")
        if not detailed_fixtures.empty:
            st.dataframe(
                detailed_fixtures[['gameweek', 'fixture', 'home_team', 'away_team']],
                use_container_width=True,
                hide_index=True,
                height=200
            )
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        easiest_team = team_fixtures.iloc[0]
        st.metric(
            "✅ Easiest Fixtures",
            easiest_team['short_name'],
            f"FDR: {easiest_team['avg_difficulty']:.2f}"
        )
    
    with col2:
        hardest_team = team_fixtures.iloc[-1]
        st.metric(
            "🔴 Hardest Fixtures",
            hardest_team['short_name'],
            f"FDR: {hardest_team['avg_difficulty']:.2f}"
        )
    
    with col3:
        avg_difficulty = team_fixtures['avg_difficulty'].mean()
        st.metric(
            "📊 Avg Difficulty",
            f"{avg_difficulty:.2f}",
            "League average"
        )
    
    with col4:
        st.metric(
            "📅 Gameweeks",
            f"GW {current_gw} - {current_gw + next_n_gw - 1}",
            f"{next_n_gw} fixtures"
        )
    
    st.markdown("---")
    
    # Create tabs - FIXTURE CALENDAR FIRST as requested
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗓️ Fixture Calendar",
        "📊 Fixture Difficulty Rankings",
        "🎯 Best Picks",
        "📈 Advanced Stats",
        "📋 Detailed Breakdown"
    ])
    
    with tab1:
        show_fixture_calendar(team_fixtures, next_n_gw, current_gw)
    
    with tab2:
        show_fixture_rankings(team_fixtures, next_n_gw)
    
    with tab3:
        show_best_picks(team_fixtures, defensive_df, attacking_df, next_n_gw)
    
    with tab4:
        show_advanced_stats(team_fixtures, defensive_df, attacking_df, next_n_gw, current_gw)
    
    with tab5:
        show_detailed_breakdown(detailed_fixtures, team_fixtures)

def show_fixture_calendar(df, next_n_gw, current_gw):
    """Show fixture calendar heatmap with improved colors"""
    
    st.subheader("🗓️ Fixture Difficulty Calendar")
    
    # Create heatmap data
    heatmap_data = []
    heatmap_text = []
    teams = []
    
    for _, row in df.iterrows():
        teams.append(row['short_name'])
        heatmap_data.append(row['difficulty_scores'])
        
        # Create text labels showing opponent
        text_labels = []
        for fixture in row['fixture_list']:
            opponent = fixture.split('(')[0].strip()
            venue = fixture.split('(')[1].replace(')', '').strip()
            
            if venue == 'H':
                # Home fixture - CAPITAL
                text_labels.append(opponent.upper())
            else:
                # Away fixture - lowercase
                text_labels.append(opponent.lower())
        
        heatmap_text.append(text_labels)
    
    # Pad shorter lists with None
    max_len = max(len(scores) for scores in heatmap_data)
    heatmap_data = [scores + [None] * (max_len - len(scores)) for scores in heatmap_data]
    heatmap_text = [text + [''] * (max_len - len(text)) for text in heatmap_text]
    
    # Create heatmap with new turquoise-to-pink color scheme
    gw_labels = [f"GW{current_gw + i}" for i in range(max_len)]
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=gw_labels,
        y=teams,
        # New color scale: Turquoise (easy) -> White (medium) -> Pink (hard)
        colorscale=[
            [0.0, '#40E0D0'],    # 1.0 = Turquoise (Easy)
            [0.25, '#7FFFD4'],   # 2.0 = Aquamarine
            [0.4, '#E0E0E0'],    # 2.5 = Light Gray (Medium)
            [0.6, '#FFB6C1'],    # 3.0 = Light Pink
            [0.8, '#FF69B4'],    # 4.0 = Hot Pink (Hard)
            [1.0, '#FF1493']     # 5.0 = Deep Pink (Very Hard)
        ],
        zmin=1,
        zmax=5,
        text=heatmap_text,
        texttemplate="%{text}",
        textfont={"size": 11, "color": "black", "family": "Arial Black"},
        hovertemplate='<b>%{y}</b><br>' +
                      'GW: %{x}<br>' +
                      'vs %{text}<br>' +
                      'FDR: %{z:.1f}<br>' +
                      '<extra></extra>',
        colorbar=dict(
            title="FDR",
            tickvals=[1, 2, 3, 4, 5],
            ticktext=['1-Easy', '2', '3-Med', '4', '5-Hard']
        )
    ))
    
    fig.update_layout(
        title=f'Fixture Difficulty Heatmap (Next {next_n_gw} Gameweeks)<br><sub>CAPITAL = Home | lowercase = away</sub>',
        xaxis_title='Gameweek',
        yaxis_title='Team',
        height=800
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Fixture details table with additional stats
    st.markdown("#### 📝 Detailed Fixture Stats")
    
    # Create detailed fixture table
    fixture_table = []
    for _, row in df.head(10).iterrows():
        for i, (fixture, difficulty) in enumerate(zip(row['fixture_list'], row['difficulty_scores'])):
            opponent = fixture.split('(')[0].strip()
            venue = '🏠' if '(H)' in fixture else '✈️'
            
            fixture_table.append({
                'Team': row['short_name'],
                'GW': current_gw + i,
                'Venue': venue,
                'Opponent': opponent,
                'FDR': difficulty
            })
    
    fixture_df = pd.DataFrame(fixture_table)
    
    if not fixture_df.empty:
        st.dataframe(
            fixture_df.style.format({
                'FDR': '{:.2f}'
            }).background_gradient(subset=['FDR'], cmap='RdYlGn_r', vmin=1, vmax=5),
            use_container_width=True,
            hide_index=True,
            height=400
        )

def show_fixture_rankings(df, next_n_gw):
    """Show fixture difficulty rankings with improved colors"""
    
    st.subheader("📊 Team Fixture Difficulty Rankings")
    
    # Bar chart of average difficulty with new color scheme
    fig = go.Figure()
    
    colors = [get_fdr_color(diff) for diff in df['avg_difficulty']]
    
    fig.add_trace(go.Bar(
        x=df['short_name'],
        y=df['avg_difficulty'],
        marker_color=colors,
        text=df['avg_difficulty'].round(2),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>' +
                      'Avg Difficulty: %{y:.2f}<br>' +
                      '<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'Average Fixture Difficulty (Next {next_n_gw} Gameweeks)',
        xaxis_title='Team',
        yaxis_title='Difficulty Rating (1=Easy, 5=Hard)',
        showlegend=False,
        height=500,
        yaxis=dict(range=[0, 5])
    )
    
    # Add reference lines
    fig.add_hline(y=2.0, line_dash="dash", line_color="#40E0D0", line_width=2,
                  annotation_text="Easy (1-2)", annotation_position="right")
    fig.add_hline(y=3.0, line_dash="dash", line_color="#E0E0E0", line_width=2,
                  annotation_text="Medium (2-3)", annotation_position="right")
    fig.add_hline(y=4.0, line_dash="dash", line_color="#FF69B4", line_width=2,
                  annotation_text="Hard (4-5)", annotation_position="right")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Rankings table
    st.markdown("#### 📋 Full Rankings Table")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🟦 Easiest Fixtures (Top 10)")
        easy_teams = df.head(10)[['rank', 'short_name', 'fixtures', 'avg_difficulty']].copy()
        easy_teams.columns = ['Rank', 'Team', 'Upcoming Fixtures', 'Avg FDR']
        
        st.dataframe(
            easy_teams.style.format({
                'Avg FDR': '{:.2f}'
            }).background_gradient(subset=['Avg FDR'], cmap='RdYlGn_r'),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        st.markdown("##### 🟥 Hardest Fixtures (Bottom 10)")
        hard_teams = df.tail(10).sort_values('rank')[['rank', 'short_name', 'fixtures', 'avg_difficulty']].copy()
        hard_teams.columns = ['Rank', 'Team', 'Upcoming Fixtures', 'Avg FDR']
        
        st.dataframe(
            hard_teams.style.format({
                'Avg FDR': '{:.2f}'
            }).background_gradient(subset=['Avg FDR'], cmap='RdYlGn_r'),
            use_container_width=True,
            hide_index=True
        )

def show_best_picks(team_fixtures, defensive_df, attacking_df, next_n_gw):
    """Show best FPL picks based on fixtures"""
    
    st.subheader("🎯 Best FPL Picks by Fixtures")
    
    st.markdown(f"""
    Teams with the easiest upcoming {next_n_gw} fixtures are highlighted.
    Consider targeting players from these teams for:
    - **Transfers in**
    - **Captain picks**
    - **Bench boost planning**
    """)
    
    # Top 5 teams with easiest fixtures
    best_fixtures = team_fixtures.head(5)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⚡ Best for Attackers")
        st.markdown("*Target teams with weak defenses ahead*")
        
        # Combine with defensive weakness
        attacker_targets = []
        for _, team in best_fixtures.iterrows():
            team_name = team['team']
            # Check which teams they're playing
            fixture_opponents = team['fixture_list']
            
            # Get average goals conceded of opponents
            avg_conceded = 0
            opponent_count = 0
            for fixture in fixture_opponents:
                opponent_short = fixture.split('(')[0].strip()
                opponent_data = defensive_df[defensive_df['short_name'] == opponent_short]
                if not opponent_data.empty:
                    avg_conceded += opponent_data.iloc[0].get('goals_conceded_per_game', 0)
                    opponent_count += 1
            
            if opponent_count > 0:
                avg_conceded /= opponent_count
                
                attacker_targets.append({
                    'Team': team['short_name'],
                    'Avg FDR': team['avg_difficulty'],
                    'Opponent Avg Conceded': avg_conceded,
                    'Fixtures': team['fixtures']
                })
        
        if attacker_targets:
            attacker_df = pd.DataFrame(attacker_targets).sort_values('Opponent Avg Conceded', ascending=False)
            st.dataframe(
                attacker_df.style.format({
                    'Avg FDR': '{:.2f}',
                    'Opponent Avg Conceded': '{:.2f}'
                }).background_gradient(subset=['Opponent Avg Conceded'], cmap='RdYlGn'),
                use_container_width=True,
                hide_index=True
            )
    
    with col2:
        st.markdown("#### 🛡️ Best for Defenders")
        st.markdown("*Target teams with weak attacks ahead*")
        
        # Combine with opponent attacking weakness
        defender_targets = []
        for _, team in best_fixtures.iterrows():
            team_name = team['team']
            fixture_opponents = team['fixture_list']
            
            # Get average goals scored of opponents
            avg_scored = 0
            opponent_count = 0
            for fixture in fixture_opponents:
                opponent_short = fixture.split('(')[0].strip()
                opponent_data = attacking_df[attacking_df['short_name'] == opponent_short]
                if not opponent_data.empty:
                    avg_scored += opponent_data.iloc[0].get('goals_per_game', 0)
                    opponent_count += 1
            
            if opponent_count > 0:
                avg_scored /= opponent_count
                
                defender_targets.append({
                    'Team': team['short_name'],
                    'Avg FDR': team['avg_difficulty'],
                    'Opponent Avg Scored': avg_scored,
                    'Fixtures': team['fixtures']
                })
        
        if defender_targets:
            defender_df = pd.DataFrame(defender_targets).sort_values('Opponent Avg Scored', ascending=True)
            st.dataframe(
                defender_df.style.format({
                    'Avg FDR': '{:.2f}',
                    'Opponent Avg Scored': '{:.2f}'
                }).background_gradient(subset=['Opponent Avg Scored'], cmap='RdYlGn_r'),
                use_container_width=True,
                hide_index=True
            )
    
    # Transfer targets
    st.markdown("---")
    st.markdown("#### 💡 Transfer Strategy")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("**✅ Target Now**")
        target_teams = best_fixtures.head(3)
        for _, team in target_teams.iterrows():
            st.markdown(f"**{team['short_name']}** - FDR: {team['avg_difficulty']:.2f}")
            st.caption(f"{team['fixtures']}")
    
    with col2:
        st.warning("**⏳ Watch List**")
        watch_teams = team_fixtures.iloc[3:6]
        for _, team in watch_teams.iterrows():
            st.markdown(f"**{team['short_name']}** - FDR: {team['avg_difficulty']:.2f}")
            st.caption(f"{team['fixtures']}")
    
    with col3:
        st.error("**❌ Avoid**")
        avoid_teams = team_fixtures.tail(3).sort_values('avg_difficulty', ascending=False)
        for _, team in avoid_teams.iterrows():
            st.markdown(f"**{team['short_name']}** - FDR: {team['avg_difficulty']:.2f}")
            st.caption(f"{team['fixtures']}")

def show_advanced_stats(team_fixtures, defensive_df, attacking_df, next_n_gw, current_gw):
    """Show advanced fixture statistics with xG and form data"""
    
    st.subheader("📈 Advanced Fixture Statistics")
    
    st.markdown("""
    Detailed breakdown of fixture difficulty factors including:
    - Opponent's defensive form (goals conceded)
    - Opponent's attacking threat (goals scored)
    - Home/Away form splits
    - Recent performance trends
    """)
    
    # Team selector
    team_options = team_fixtures['team'].tolist()
    selected_teams = st.multiselect(
        "Select teams to analyze (max 5)",
        team_options,
        default=team_options[:3],
        max_selections=5
    )
    
    if not selected_teams:
        st.info("👆 Select teams to see detailed statistics")
        return
    
    for team_name in selected_teams:
        team_data = team_fixtures[team_fixtures['team'] == team_name].iloc[0]
        
        with st.expander(f"**{team_data['short_name']}** - Avg FDR: {team_data['avg_difficulty']:.2f}", expanded=True):
            
            # Get team stats
            team_def = defensive_df[defensive_df['team'] == team_name]
            team_att = attacking_df[attacking_df['team'] == team_name]
            
            # Team overview stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if not team_att.empty:
                    st.metric("Goals/Game", f"{team_att.iloc[0]['goals_per_game']:.2f}")
                else:
                    st.metric("Goals/Game", "N/A")
            
            with col2:
                if not team_def.empty:
                    st.metric("Conceded/Game", f"{team_def.iloc[0]['goals_conceded_per_game']:.2f}")
                else:
                    st.metric("Conceded/Game", "N/A")
            
            with col3:
                if not team_def.empty:
                    st.metric("Clean Sheets", f"{team_def.iloc[0]['clean_sheet_%']:.0f}%")
                else:
                    st.metric("Clean Sheets", "N/A")
            
            with col4:
                st.metric("Upcoming FDR", f"{team_data['avg_difficulty']:.2f}")
            
            st.markdown("---")
            
            # Fixture-by-fixture breakdown
            st.markdown(f"#### Next {next_n_gw} Fixtures")
            
            fixture_stats = []
            
            for i, (fixture, difficulty) in enumerate(zip(team_data['fixture_list'], team_data['difficulty_scores'])):
                opponent = fixture.split('(')[0].strip()
                venue = fixture.split('(')[1].replace(')', '').strip()
                gw = current_gw + i
                
                # Get opponent stats
                opp_def = defensive_df[defensive_df['short_name'] == opponent]
                opp_att = attacking_df[attacking_df['short_name'] == opponent]
                
                # Venue emoji
                venue_emoji = '🏠' if venue == 'H' else '✈️'
                venue_text = 'Home' if venue == 'H' else 'Away'
                
                # Calculate key metrics
                if venue == 'H':
                    # Home fixture
                    opp_goals_conceded = opp_def.iloc[0]['goals_conceded_per_game'] if not opp_def.empty else 0
                    opp_goals_scored = opp_att.iloc[0]['goals_per_game'] if not opp_att.empty else 0
                    attacking_potential = "High" if opp_goals_conceded > 1.5 else "Medium" if opp_goals_conceded > 1.0 else "Low"
                    defensive_risk = "High" if opp_goals_scored > 1.5 else "Medium" if opp_goals_scored > 1.0 else "Low"
                else:
                    # Away fixture
                    opp_goals_conceded = opp_def.iloc[0]['goals_conceded_per_game'] if not opp_def.empty else 0
                    opp_goals_scored = opp_att.iloc[0]['goals_per_game'] if not opp_att.empty else 0
                    attacking_potential = "Medium" if opp_goals_conceded > 1.3 else "Low" if opp_goals_conceded > 0.8 else "Very Low"
                    defensive_risk = "High" if opp_goals_scored > 1.8 else "Medium" if opp_goals_scored > 1.3 else "Low"
                
                clean_sheet_prob = "High" if defensive_risk == "Low" else "Medium" if defensive_risk == "Medium" else "Low"
                
                fixture_stats.append({
                    'GW': gw,
                    'Venue': f"{venue_emoji} {venue_text}",
                    'Opponent': opponent,
                    'FDR': difficulty,
                    'Opp Conceded/G': opp_goals_conceded,
                    'Opp Scored/G': opp_goals_scored,
                    'Attack Potential': attacking_potential,
                    'CS Probability': clean_sheet_prob
                })
            
            fixture_df = pd.DataFrame(fixture_stats)
            
            if not fixture_df.empty:
                # Color coding for metrics
                def color_fdr(val):
                    if val < 2.5:
                        return 'background-color: #40E0D0; color: black'
                    elif val < 3.5:
                        return 'background-color: #E0E0E0; color: black'
                    else:
                        return 'background-color: #FF69B4; color: black'
                
                def color_potential(val):
                    if val == 'High':
                        return 'background-color: #40E0D0; color: black'
                    elif val == 'Medium':
                        return 'background-color: #E0E0E0; color: black'
                    else:
                        return 'background-color: #FF69B4; color: black'
                
                styled_df = fixture_df.style.format({
                    'FDR': '{:.2f}',
                    'Opp Conceded/G': '{:.2f}',
                    'Opp Scored/G': '{:.2f}'
                }).applymap(color_fdr, subset=['FDR']) \
                  .applymap(color_potential, subset=['Attack Potential', 'CS Probability'])
                
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Visualizations
            st.markdown("#### 📊 Fixture Difficulty Trend")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # FDR trend line
                fig_fdr = go.Figure()
                
                fig_fdr.add_trace(go.Scatter(
                    x=[f"GW{current_gw + i}" for i in range(len(team_data['difficulty_scores']))],
                    y=team_data['difficulty_scores'],
                    mode='lines+markers',
                    name='FDR',
                    line=dict(color='#3498db', width=3),
                    marker=dict(size=10)
                ))
                
                # Add difficulty zones
                fig_fdr.add_hline(y=2.5, line_dash="dash", line_color="#40E0D0",
                                 annotation_text="Easy", annotation_position="right")
                fig_fdr.add_hline(y=3.5, line_dash="dash", line_color="#FF69B4",
                                 annotation_text="Hard", annotation_position="right")
                
                fig_fdr.update_layout(
                    title="Fixture Difficulty Over Time",
                    yaxis_title="FDR",
                    yaxis=dict(range=[0, 5]),
                    height=300
                )
                
                st.plotly_chart(fig_fdr, use_container_width=True)
            
            with col2:
                # Opponent quality breakdown
                if not fixture_df.empty:
                    fig_opp = go.Figure()
                    
                    fig_opp.add_trace(go.Bar(
                        x=fixture_df['Opponent'],
                        y=fixture_df['Opp Conceded/G'],
                        name='Conceded/G',
                        marker_color='#FF69B4'
                    ))
                    
                    fig_opp.add_trace(go.Bar(
                        x=fixture_df['Opponent'],
                        y=fixture_df['Opp Scored/G'],
                        name='Scored/G',
                        marker_color='#40E0D0'
                    ))
                    
                    fig_opp.update_layout(
                        title="Opponent Form",
                        yaxis_title="Goals per Game",
                        barmode='group',
                        height=300
                    )
                    
                    st.plotly_chart(fig_opp, use_container_width=True)
    
    # Summary comparison
    if len(selected_teams) > 1:
        st.markdown("---")
        st.markdown("### 📊 Team Comparison")
        
        comparison_data = []
        for team_name in selected_teams:
            team_data = team_fixtures[team_fixtures['team'] == team_name].iloc[0]
            team_att = attacking_df[attacking_df['team'] == team_name]
            team_def = defensive_df[defensive_df['team'] == team_name]
            
            comparison_data.append({
                'Team': team_data['short_name'],
                'Avg FDR': team_data['avg_difficulty'],
                'Goals/G': team_att.iloc[0]['goals_per_game'] if not team_att.empty else 0,
                'Conceded/G': team_def.iloc[0]['goals_conceded_per_game'] if not team_def.empty else 0,
                'CS%': team_def.iloc[0]['clean_sheet_%'] if not team_def.empty else 0,
                'Fixtures': team_data['fixtures']
            })
        
        comp_df = pd.DataFrame(comparison_data)
        
        st.dataframe(
            comp_df.style.format({
                'Avg FDR': '{:.2f}',
                'Goals/G': '{:.2f}',
                'Conceded/G': '{:.2f}',
                'CS%': '{:.1f}%'
            }).background_gradient(subset=['Avg FDR'], cmap='RdYlGn_r', vmin=1, vmax=5),
            use_container_width=True,
            hide_index=True
        )

def show_detailed_breakdown(detailed_fixtures, team_fixtures):
    """Show detailed fixture breakdown"""
    
    st.subheader("📋 Detailed Fixture Breakdown")
    
    # Group by gameweek
    for gw in sorted(detailed_fixtures['gameweek'].unique()):
        gw_fixtures = detailed_fixtures[detailed_fixtures['gameweek'] == gw]
        
        with st.expander(f"**Gameweek {gw}** - {len(gw_fixtures)} Fixtures", expanded=(gw == detailed_fixtures['gameweek'].min())):
            
            # Create columns for each fixture
            cols_per_row = 3
            rows = (len(gw_fixtures) + cols_per_row - 1) // cols_per_row
            
            fixture_list = gw_fixtures.to_dict('records')
            
            for row in range(rows):
                cols = st.columns(cols_per_row)
                for col_idx in range(cols_per_row):
                    fixture_idx = row * cols_per_row + col_idx
                    if fixture_idx < len(fixture_list):
                        fixture = fixture_list[fixture_idx]
                        
                        with cols[col_idx]:
                            # Color code based on difficulty
                            h_diff = fixture['home_difficulty']
                            a_diff = fixture['away_difficulty']
                            
                            h_color = get_fdr_color(h_diff)
                            a_color = get_fdr_color(a_diff)
                            
                            st.markdown(f"**{fixture['fixture']}**")
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown(f"<span style='color: {h_color}'>●</span> {fixture['home_team']}: {h_diff:.1f}", 
                                          unsafe_allow_html=True)
                            with col_b:
                                st.markdown(f"<span style='color: {a_color}'>●</span> {fixture['away_team']}: {a_diff:.1f}", 
                                          unsafe_allow_html=True)
    
    # Summary table
    st.markdown("#### 📊 All Fixtures Summary")
    
    display_df = detailed_fixtures[['gameweek', 'fixture', 'home_difficulty', 'away_difficulty']].copy()
    display_df.columns = ['GW', 'Fixture', 'Home FDR', 'Away FDR']
    
    st.dataframe(
        display_df.style.format({
            'Home FDR': '{:.2f}',
            'Away FDR': '{:.2f}'
        }).background_gradient(subset=['Home FDR', 'Away FDR'], cmap='RdYlGn_r'),
        use_container_width=True,
        hide_index=True,
        height=400
    )

# Call the main show function
show(defensive_df, attacking_df)
