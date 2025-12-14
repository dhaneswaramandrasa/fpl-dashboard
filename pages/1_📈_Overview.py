"""
Overview Page - High Level FPL Statistics
Shows top performers, trends, and key metrics
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
    
    # Key metrics at the top
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        top_scorer = filtered_df.nlargest(1, 'total_points').iloc[0]
        st.metric(
            "🏆 Top Scorer",
            top_scorer['full_name'],
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

def show_performance_analysis(df):
    """Show performance scatter plots"""
    
    st.subheader("Performance Scatter Plots")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Points vs xGI
        fig1 = px.scatter(
            df,
            x='total_xGI',
            y='total_points',
            color='position',
            size='total_minutes',
            hover_name='full_name',
            hover_data={
                'total_xGI': ':.2f',
                'total_points': ':.0f',
                'fixtures_played': True,
                'total_minutes': True
            },
            title='Total Points vs Expected Goal Involvements (xGI)',
            labels={
                'total_xGI': 'Expected Goal Involvements (xGI)',
                'total_points': 'Total FPL Points',
                'position': 'Position'
            },
            color_discrete_map={
                'FWD': '#e74c3c',
                'MID': '#3498db',
                'DEF': '#2ecc71',
                'GK': '#f39c12'
            }
        )
        fig1.update_layout(height=500)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Points per 90 vs xGI per 90 (recent form)
        fig2 = px.scatter(
            df,
            x='xGI_per90_last_5',
            y='points_per90_last_5',
            color='position',
            size='minutes_last_5',
            hover_name='full_name',
            hover_data={
                'xGI_per90_last_5': ':.2f',
                'points_per90_last_5': ':.2f',
                'points_last_5': ':.0f',
                'minutes_last_5': ':.0f'
            },
            title='Recent Form: Points/90 vs xGI/90 (Last 5 Games)',
            labels={
                'xGI_per90_last_5': 'xGI per 90 (Last 5)',
                'points_per90_last_5': 'Points per 90 (Last 5)',
                'position': 'Position'
            },
            color_discrete_map={
                'FWD': '#e74c3c',
                'MID': '#3498db',
                'DEF': '#2ecc71',
                'GK': '#f39c12'
            }
        )
        fig2.update_layout(height=500)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Top performers table
    st.subheader("🏆 Top Performers (Season)")
    
    top_performers = df.nlargest(15, 'total_points')[
        ['full_name', 'position', 'total_points', 'fixtures_played', 
         'points_per90_season', 'total_xGI', 'xGI_per90_season']
    ].copy()
    
    top_performers.columns = ['Player', 'Pos', 'Points', 'Games', 'Pts/90', 'xGI', 'xGI/90']
    
    # Style the dataframe
    st.dataframe(
        top_performers.style.format({
            'Points': '{:.0f}',
            'Games': '{:.0f}',
            'Pts/90': '{:.2f}',
            'xGI': '{:.2f}',
            'xGI/90': '{:.2f}'
        }).background_gradient(subset=['Points'], cmap='YlGn'),
        use_container_width=True,
        hide_index=True
    )

def show_form_trends(df, match_data):
    """Show form trends and hot/cold players"""
    
    st.subheader("🔥 Form Analysis")
    
    # Hot form players
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Players in Hot Form")
        hot_players = df[df['hot_form'] == True].nlargest(10, 'form_trend_points')[
            ['full_name', 'position', 'points_per90_season', 'points_per90_last_5', 
             'form_trend_points', 'minutes_last_5']
        ].copy()
        
        if len(hot_players) > 0:
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
            st.info("No players currently in hot form (min 5 games, +1.0 pts/90 improvement)")
    
    with col2:
        st.markdown("#### 📉 Cold Form Players")
        cold_players = df[df['form_trend_points'] < -1.0].nsmallest(10, 'form_trend_points')[
            ['full_name', 'position', 'points_per90_season', 'points_per90_last_5', 
             'form_trend_points', 'minutes_last_5']
        ].copy()
        
        if len(cold_players) > 0:
            cold_players.columns = ['Player', 'Pos', 'Season Pts/90', 'Recent Pts/90', 'Trend', 'Mins L5']
            st.dataframe(
                cold_players.style.format({
                    'Season Pts/90': '{:.2f}',
                    'Recent Pts/90': '{:.2f}',
                    'Trend': '{:+.2f}',
                    'Mins L5': '{:.0f}'
                }).background_gradient(subset=['Trend'], cmap='RdYlGn_r'),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No players in cold form")
    
    # Form trend visualization
    st.markdown("#### 📊 Form Trend Distribution")
    
    fig = go.Figure()
    
    for pos in df['position'].unique():
        pos_data = df[df['position'] == pos]
        fig.add_trace(go.Box(
            y=pos_data['form_trend_points'],
            name=pos,
            boxmean='sd'
        ))
    
    fig.update_layout(
        title='Form Trend Distribution by Position',
        yaxis_title='Form Trend (Recent - Season Pts/90)',
        showlegend=True,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Top xGI performers (recent)
    st.markdown("#### ⚡ Top xGI/90 (Last 5 Games)")
    
    top_xgi = df[df['minutes_last_5'] >= 200].nlargest(15, 'xGI_per90_last_5')[
        ['full_name', 'position', 'xGI_per90_last_5', 'goals_last_5', 
         'assists_last_5', 'points_last_5', 'minutes_last_5']
    ].copy()
    
    top_xgi.columns = ['Player', 'Pos', 'xGI/90', 'Goals', 'Assists', 'Points', 'Minutes']
    
    st.dataframe(
        top_xgi.style.format({
            'xGI/90': '{:.2f}',
            'Goals': '{:.0f}',
            'Assists': '{:.0f}',
            'Points': '{:.0f}',
            'Minutes': '{:.0f}'
        }).background_gradient(subset=['xGI/90'], cmap='Blues'),
        use_container_width=True,
        hide_index=True
    )

def show_value_analysis(df):
    """Show value analysis and efficiency metrics"""
    
    st.subheader("💎 Value Analysis")
    
    # Points per price (if price data available)
    st.markdown("#### 🎯 xG Overperformance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Over-performers
        over_performers = df[df['total_xG'] > 1].nlargest(15, 'xG_overperformance')[
            ['full_name', 'position', 'goals_scored', 'total_xG', 'xG_overperformance']
        ].copy()
        
        over_performers.columns = ['Player', 'Pos', 'Goals', 'xG', 'Diff']
        
        st.markdown("**Top xG Over-performers**")
        st.dataframe(
            over_performers.style.format({
                'Goals': '{:.0f}',
                'xG': '{:.2f}',
                'Diff': '{:+.2f}'
            }).background_gradient(subset=['Diff'], cmap='Greens'),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        # Under-performers
        under_performers = df[df['total_xG'] > 1].nsmallest(15, 'xG_overperformance')[
            ['full_name', 'position', 'goals_scored', 'total_xG', 'xG_overperformance']
        ].copy()
        
        under_performers.columns = ['Player', 'Pos', 'Goals', 'xG', 'Diff']
        
        st.markdown("**Top xG Under-performers**")
        st.dataframe(
            under_performers.style.format({
                'Goals': '{:.0f}',
                'xG': '{:.2f}',
                'Diff': '{:+.2f}'
            }).background_gradient(subset=['Diff'], cmap='Reds_r'),
            use_container_width=True,
            hide_index=True
        )
    
    # Scatter: Goals vs xG
    st.markdown("#### 📊 Goals vs Expected Goals (xG)")
    
    fig = px.scatter(
        df[df['total_xG'] > 0],
        x='total_xG',
        y='goals_scored',
        color='position',
        size='total_minutes',
        hover_name='full_name',
        hover_data={
            'total_xG': ':.2f',
            'goals_scored': True,
            'xG_overperformance': ':.2f',
            'fixtures_played': True
        },
        title='Actual Goals vs Expected Goals (xG)',
        labels={
            'total_xG': 'Expected Goals (xG)',
            'goals_scored': 'Actual Goals',
            'position': 'Position'
        },
        color_discrete_map={
            'FWD': '#e74c3c',
            'MID': '#3498db',
            'DEF': '#2ecc71',
            'GK': '#f39c12'
        }
    )
    
    # Add diagonal line (perfect xG match)
    max_val = max(df['total_xG'].max(), df['goals_scored'].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode='lines',
        line=dict(color='gray', dash='dash'),
        name='Expected (xG = Goals)',
        showlegend=True
    ))
    
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Efficiency metrics
    st.markdown("#### 🎖️ Efficiency Leaders")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Best Points/90 (Season)**")
        best_pts_90 = df[df['total_minutes'] >= 450].nlargest(10, 'points_per90_season')[
            ['full_name', 'position', 'total_points', 'total_minutes', 'points_per90_season']
        ].copy()
        best_pts_90.columns = ['Player', 'Pos', 'Points', 'Minutes', 'Pts/90']
        st.dataframe(
            best_pts_90.style.format({
                'Points': '{:.0f}',
                'Minutes': '{:.0f}',
                'Pts/90': '{:.2f}'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        st.markdown("**Best Bonus/90**")
        best_bonus = df[df['total_minutes'] >= 450].assign(
            bonus_per90=lambda x: x['bonus'] * 90 / x['total_minutes']
        ).nlargest(10, 'bonus_per90')[
            ['full_name', 'position', 'bonus', 'total_minutes', 'bonus_per90']
        ].copy()
        best_bonus.columns = ['Player', 'Pos', 'Bonus', 'Minutes', 'Bonus/90']
        st.dataframe(
            best_bonus.style.format({
                'Bonus': '{:.0f}',
                'Minutes': '{:.0f}',
                'Bonus/90': '{:.2f}'
            }),
            use_container_width=True,
            hide_index=True
        )

# Call the main show function
show(player_data, match_data)
