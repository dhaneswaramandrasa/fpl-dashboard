"""
Player Comparison Page
Compare 2+ players side-by-side with radar charts and detailed stats
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from math import pi
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Page config
st.set_page_config(
    page_title="Player Comparison - FPL Dashboard",
    page_icon="👥",
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
    """Display player comparison page"""
    
    if player_data is None or player_data.empty:
        st.error("❌ No player data available. Please download data from the sidebar.")
        return
    
    st.header("👥 Player Comparison")
    st.markdown("Compare players head-to-head with radar charts and detailed statistics")
    st.markdown("---")
    
    # Player selection
    st.subheader("Select Players to Compare")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Filter options
        position_filter = st.selectbox(
            "Filter by Position",
            ["All"] + sorted(player_data['position'].unique().tolist()),
            key="comp_position"
        )
    
    with col2:
        min_minutes = st.slider(
            "Minimum Minutes",
            0,
            int(player_data['total_minutes'].max()),
            180,
            90,
            key="comp_minutes"
        )
    
    # Filter player list
    filtered_players = player_data[player_data['total_minutes'] >= min_minutes].copy()
    if position_filter != "All":
        filtered_players = filtered_players[filtered_players['position'] == position_filter]
    
    player_list = sorted(filtered_players['full_name'].unique())
    
    # Multi-select for players (2-5 players)
    selected_players = st.multiselect(
        "Select 2-5 Players",
        player_list,
        max_selections=5,
        help="Select at least 2 players to compare"
    )
    
    if len(selected_players) < 2:
        st.info("👆 Please select at least 2 players to compare")
        
        # Show some suggestions
        st.markdown("### 💡 Suggested Comparisons")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top Scorers**")
            top_scorers = player_data.nlargest(5, 'total_points')[['full_name', 'position', 'total_points']]
            st.dataframe(top_scorers, hide_index=True, use_container_width=True)
        
        with col2:
            st.markdown("**Hot Form Players**")
            hot_form = player_data[player_data['hot_form'] == True].nlargest(5, 'form_trend_points')[
                ['full_name', 'position', 'points_per90_last_5']
            ]
            st.dataframe(hot_form, hide_index=True, use_container_width=True)
        
        return
    
    # Get data for selected players
    comparison_df = player_data[player_data['full_name'].isin(selected_players)].copy()
    
    # Summary metrics
    st.markdown("---")
    st.subheader("📊 Quick Overview")
    
    cols = st.columns(len(selected_players))
    for idx, (col, player_name) in enumerate(zip(cols, selected_players)):
        player = comparison_df[comparison_df['full_name'] == player_name].iloc[0]
        with col:
            st.markdown(f"**{player['full_name']}**")
            st.markdown(f"*{player['position']}*")
            st.metric("Total Points", f"{player['total_points']:.0f}")
            st.metric("Pts/90 (L5)", f"{player['points_per90_last_5']:.2f}")
            st.metric("Form Trend", f"{player['form_trend_points']:+.2f}")
    
    st.markdown("---")
    
    # Create tabs for different comparisons
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Radar Charts",
        "📈 Performance Metrics",
        "🔥 Form Analysis",
        "📋 Detailed Stats"
    ])
    
    with tab1:
        show_radar_charts(comparison_df, player_data)
    
    with tab2:
        show_performance_comparison(comparison_df)
    
    with tab3:
        show_form_comparison(comparison_df, match_data)
    
    with tab4:
        show_detailed_stats(comparison_df)

def show_radar_charts(df, player_data):
    """Show radar chart comparisons"""
    
    st.subheader("Radar Chart Comparisons")
    
    # Color palette
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Overall performance radar
        st.markdown("#### Overall Performance (Percentiles)")
        
        categories = ['Points/90\n(Recent)', 'xGI/90\n(Recent)', 'Minutes/Game', 
                     'Bonus/Game', 'Total Points']
        metrics = ['points_per90_last_5', 'xGI_per90_last_5', 'minutes_per_fixture',
                  'bonus', 'total_points']
        
        fig1 = create_radar_chart(df, categories, metrics, colors, use_percentiles=True, all_players_df=player_data)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Attacking metrics radar
        st.markdown("#### Attacking Output (Season)")
        
        categories = ['Goals', 'Assists', 'xG', 'xA', 'xGI']
        metrics = ['goals_scored', 'assists', 'total_xG', 'total_xA', 'total_xGI']
        
        fig2 = create_radar_chart(df, categories, metrics, colors, use_percentiles=False, all_players_df=player_data)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Recent form radar
    st.markdown("#### Recent Form (Last 5 Games)")
    
    categories = ['Points', 'Goals', 'Assists', 'xGI', 'Minutes', 'Bonus']
    metrics = ['points_last_5', 'goals_last_5', 'assists_last_5', 
              'xGI_last_5', 'minutes_last_5', 'bonus']
    
    fig3 = create_radar_chart(df, categories, metrics, colors, use_percentiles=False, all_players_df=player_data)
    st.plotly_chart(fig3, use_container_width=True)

def create_radar_chart(df, categories, metrics, colors, use_percentiles=True, all_players_df=None):
    """Create a radar chart for player comparison"""
    
    fig = go.Figure()
    
    # Get position for percentile calculation
    position = df.iloc[0]['position']
    
    for idx, (_, player) in enumerate(df.iterrows()):
        values = []
        
        for metric in metrics:
            val = player[metric]
            
            if use_percentiles and position and all_players_df is not None:
                # Calculate percentile within position
                position_data = all_players_df[all_players_df['position'] == position][metric]
                
                if position_data.std() > 0:
                    percentile = (position_data <= val).sum() / len(position_data) * 100
                else:
                    percentile = 50
                values.append(percentile)
            else:
                values.append(val)
        
        # Close the polygon
        values += values[:1]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill='toself',
            name=player['full_name'],
            line=dict(color=colors[idx % len(colors)], width=2),
            fillcolor=colors[idx % len(colors)],
            opacity=0.3
        ))
    
    if use_percentiles:
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickvals=[25, 50, 75, 100],
                    ticktext=['25%', '50%', '75%', '100%']
                )
            ),
            showlegend=True,
            height=450
        )
    else:
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=True,
            height=450
        )
    
    return fig

def show_performance_comparison(df):
    """Show performance comparison charts"""
    
    st.subheader("Performance Comparison")
    
    # Bar charts for key metrics
    col1, col2 = st.columns(2)
    
    with col1:
        # Total points comparison
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['full_name'],
            y=df['total_points'],
            text=df['total_points'].round(0),
            textposition='auto',
            marker_color='#3498db'
        ))
        
        fig.update_layout(
            title='Total FPL Points',
            yaxis_title='Points',
            showlegend=False,
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Points per 90 comparison
        fig = go.Figure()
        
        # Season pts/90
        fig.add_trace(go.Bar(
            name='Season',
            x=df['full_name'],
            y=df['points_per90_season'],
            marker_color='lightblue',
            opacity=0.6
        ))
        
        # Last 5 pts/90
        fig.add_trace(go.Bar(
            name='Last 5',
            x=df['full_name'],
            y=df['points_per90_last_5'],
            marker_color='darkblue'
        ))
        
        fig.update_layout(
            title='Points per 90: Season vs Recent',
            yaxis_title='Points per 90',
            barmode='group',
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Goals and Assists
    st.markdown("#### Goals & Assists Comparison")
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Goals', 'Assists')
    )
    
    # Goals
    fig.add_trace(
        go.Bar(
            x=df['full_name'],
            y=df['goals_scored'],
            name='Actual Goals',
            marker_color='#e74c3c'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=df['full_name'],
            y=df['total_xG'],
            name='xG',
            marker_color='#c0392b',
            opacity=0.5
        ),
        row=1, col=1
    )
    
    # Assists
    fig.add_trace(
        go.Bar(
            x=df['full_name'],
            y=df['assists'],
            name='Actual Assists',
            marker_color='#3498db',
            showlegend=False
        ),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Bar(
            x=df['full_name'],
            y=df['total_xA'],
            name='xA',
            marker_color='#2980b9',
            opacity=0.5,
            showlegend=False
        ),
        row=1, col=2
    )
    
    fig.update_layout(height=400, showlegend=True, barmode='group')
    st.plotly_chart(fig, use_container_width=True)

def show_form_comparison(df, match_data):
    """Show form trends over time"""
    
    st.subheader("Form Trends")
    
    if match_data is None:
        st.warning("Match-by-match data not available")
        return
    
    # Get last 10 games for each player
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    for idx, (_, player) in enumerate(df.iterrows()):
        player_name = player['full_name']
        player_matches = match_data[match_data['full_name'] == player_name].sort_values('round').tail(10)
        
        if not player_matches.empty:
            fig.add_trace(go.Scatter(
                x=player_matches['round'],
                y=player_matches['total_points'],
                mode='lines+markers',
                name=player_name,
                line=dict(color=colors[idx % len(colors)], width=3),
                marker=dict(size=8)
            ))
    
    fig.update_layout(
        title='Points Trend (Last 10 Games)',
        xaxis_title='Gameweek',
        yaxis_title='FPL Points',
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Form metrics comparison
    st.markdown("#### Form Metrics (Last 5 Games)")
    
    form_df = df[['full_name', 'points_last_5', 'goals_last_5', 'assists_last_5',
                  'xGI_last_5', 'minutes_last_5', 'points_per90_last_5']].copy()
    
    form_df.columns = ['Player', 'Points', 'Goals', 'Assists', 'xGI', 'Minutes', 'Pts/90']
    
    st.dataframe(
        form_df.style.format({
            'Points': '{:.0f}',
            'Goals': '{:.0f}',
            'Assists': '{:.0f}',
            'xGI': '{:.2f}',
            'Minutes': '{:.0f}',
            'Pts/90': '{:.2f}'
        }).background_gradient(subset=['Points', 'Pts/90'], cmap='YlGn'),
        use_container_width=True,
        hide_index=True
    )

def show_detailed_stats(df):
    """Show detailed statistical comparison"""
    
    st.subheader("Detailed Statistics Table")
    
    # Prepare comparison table
    stats = {
        'Metric': [],
    }
    
    for player_name in df['full_name']:
        stats[player_name] = []
    
    # Add metrics
    metrics = [
        ('Total Points', 'total_points', '{:.0f}'),
        ('Fixtures Played', 'fixtures_played', '{:.0f}'),
        ('Total Minutes', 'total_minutes', '{:.0f}'),
        ('Minutes/Game', 'minutes_per_fixture', '{:.1f}'),
        ('', None, None),  # Spacer
        ('Points/90 (Season)', 'points_per90_season', '{:.2f}'),
        ('Points/90 (Last 5)', 'points_per90_last_5', '{:.2f}'),
        ('Form Trend', 'form_trend_points', '{:+.2f}'),
        ('', None, None),  # Spacer
        ('Goals', 'goals_scored', '{:.0f}'),
        ('Assists', 'assists', '{:.0f}'),
        ('xG', 'total_xG', '{:.2f}'),
        ('xA', 'total_xA', '{:.2f}'),
        ('xG Overperformance', 'xG_overperformance', '{:+.2f}'),
        ('', None, None),  # Spacer
        ('Goals (Last 5)', 'goals_last_5', '{:.0f}'),
        ('Assists (Last 5)', 'assists_last_5', '{:.0f}'),
        ('xGI (Last 5)', 'xGI_last_5', '{:.2f}'),
        ('Minutes (Last 5)', 'minutes_last_5', '{:.0f}'),
    ]
    
    for metric_name, metric_col, fmt in metrics:
        stats['Metric'].append(metric_name)
        
        if metric_col is None:
            for player_name in df['full_name']:
                stats[player_name].append('')
        else:
            for _, player in df.iterrows():
                player_name = player['full_name']
                value = player[metric_col]
                
                if fmt:
                    stats[player_name].append(fmt.format(value))
                else:
                    stats[player_name].append(str(value))
    
    stats_df = pd.DataFrame(stats)
    
    # Display as table
    st.dataframe(
        stats_df,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Add recommendation
    st.markdown("---")
    st.subheader("💡 Recommendation")
    
    # Find best recent form
    best_recent = df.loc[df['points_per90_last_5'].idxmax()]
    best_season = df.loc[df['points_per90_season'].idxmax()]
    best_form_trend = df.loc[df['form_trend_points'].idxmax()]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success(f"**Best Recent Form**\n\n{best_recent['full_name']}\n\n{best_recent['points_per90_last_5']:.2f} pts/90")
    
    with col2:
        st.info(f"**Best Season Average**\n\n{best_season['full_name']}\n\n{best_season['points_per90_season']:.2f} pts/90")
    
    with col3:
        st.warning(f"**Improving Most**\n\n{best_form_trend['full_name']}\n\n{best_form_trend['form_trend_points']:+.2f} trend")

# Call the main show function
show(player_data, match_data)
