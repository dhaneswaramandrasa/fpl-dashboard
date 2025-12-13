"""
FPL Dashboard - Fantasy Premier League Analysis Tool
Main application file with navigation and data loading
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add utils to path
sys.path.append(str(Path(__file__).parent))

from utils.data_loader import load_fpl_data, check_data_exists
from utils.scraper import scrape_all_data

# Page configuration
st.set_page_config(
    page_title="FPL Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'player_data' not in st.session_state:
    st.session_state.player_data = None
if 'match_data' not in st.session_state:
    st.session_state.match_data = None
if 'team_defensive' not in st.session_state:
    st.session_state.team_defensive = None
if 'team_attacking' not in st.session_state:
    st.session_state.team_attacking = None

# Sidebar
with st.sidebar:
    st.title("⚽ FPL Dashboard")
    st.markdown("---")
    
    # Data status
    st.subheader("📊 Data Status")
    
    if check_data_exists():
        st.success("✅ Data files found")
        if st.button("🔄 Refresh Data", use_container_width=True):
            with st.spinner("Scraping latest FPL data..."):
                scrape_all_data()
                st.session_state.data_loaded = False
                st.rerun()
    else:
        st.warning("⚠️ No data files found")
        if st.button("📥 Download Data", use_container_width=True, type="primary"):
            with st.spinner("Scraping FPL data... This may take a few minutes..."):
                scrape_all_data()
                st.session_state.data_loaded = False
                st.rerun()
    
    st.markdown("---")
    
    # Navigation
    st.subheader("📍 Navigation")
    st.page_link("app.py", label="🏠 Home", icon="🏠")
    st.page_link("pages/1_📈_Overview.py", label="Overview", icon="📈")
    st.page_link("pages/2_👥_Player_Comparison.py", label="Player Comparison", icon="👥")
    st.page_link("pages/3_🏆_Team_Analysis.py", label="Team Analysis", icon="🏆")
    st.page_link("pages/4_📅_Fixture_Analysis.py", label="Fixture Analysis", icon="📅")
    
    st.markdown("---")
    
    # Info
    st.subheader("ℹ️ About")
    st.markdown("""
    This dashboard provides comprehensive FPL analysis including:
    - **Overview**: Top performers and trends
    - **Player Comparison**: Compare players head-to-head
    - **Team Analysis**: Attacking/defensive team stats
    - **Fixture Analysis**: Upcoming fixture difficulty rankings
    
    **Data Source**: Official FPL API
    """)
    
    st.markdown("---")
    st.caption("Built with Streamlit | Data updates on refresh")

# Load data if not already loaded
if not st.session_state.data_loaded and check_data_exists():
    with st.spinner("Loading FPL data..."):
        data = load_fpl_data()
        if data:
            st.session_state.player_data = data['player_data']
            st.session_state.match_data = data['match_data']
            st.session_state.team_defensive = data['team_defensive']
            st.session_state.team_attacking = data['team_attacking']
            st.session_state.data_loaded = True

# Main content - Home page
st.title("⚽ Welcome to FPL Dashboard")
st.markdown("### Your Fantasy Premier League Analysis Tool")

if st.session_state.data_loaded:
    # Show quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_players = len(st.session_state.player_data)
        st.metric("📊 Total Players", total_players)
    
    with col2:
        top_scorer = st.session_state.player_data.nlargest(1, 'total_points').iloc[0]
        st.metric("🏆 Top Scorer", top_scorer['full_name'][:15] + "...")
    
    with col3:
        hot_form = len(st.session_state.player_data[st.session_state.player_data['hot_form'] == True])
        st.metric("🔥 Hot Form Players", hot_form)
    
    with col4:
        fixtures = st.session_state.player_data['fixtures_played'].max()
        st.metric("⚽ Gameweeks", int(fixtures))
    
    st.markdown("---")
    
    # Navigation cards
    st.markdown("### 📍 Choose Your Analysis")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info("📈 **Overview**\n\nTrack top performers, form trends, and key metrics")
        if st.button("Go to Overview →", use_container_width=True):
            st.switch_page("pages/1_📈_Overview.py")
    
    with col2:
        st.info("👥 **Player Comparison**\n\nCompare players side-by-side with radar charts")
        if st.button("Go to Player Comparison →", use_container_width=True):
            st.switch_page("pages/2_👥_Player_Comparison.py")
    
    with col3:
        st.info("🏆 **Team Analysis**\n\nAnalyze team attacking and defensive stats")
        if st.button("Go to Team Analysis →", use_container_width=True):
            st.switch_page("pages/3_🏆_Team_Analysis.py")
    
    with col4:
        st.info("📅 **Fixture Analysis**\n\nFind teams with the best upcoming fixtures")
        if st.button("Go to Fixture Analysis →", use_container_width=True):
            st.switch_page("pages/4_📅_Fixture_Analysis.py")
    
    st.markdown("---")
    
    # Quick insights
    st.markdown("### 💡 Quick Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔥 Top 5 Players in Form")
        hot_players = st.session_state.player_data.nlargest(5, 'points_per90_last_5')[
            ['full_name', 'position', 'points_per90_last_5', 'form_trend_points']
        ]
        hot_players.columns = ['Player', 'Pos', 'Pts/90 (L5)', 'Form Trend']
        st.dataframe(hot_players, hide_index=True, use_container_width=True)
    
    with col2:
        st.markdown("#### ⚡ Top 5 xGI per 90 (L5)")
        top_xgi = st.session_state.player_data[
            st.session_state.player_data['minutes_last_5'] >= 200
        ].nlargest(5, 'xGI_per90_last_5')[
            ['full_name', 'position', 'xGI_per90_last_5', 'points_last_5']
        ]
        top_xgi.columns = ['Player', 'Pos', 'xGI/90', 'Points (L5)']
        st.dataframe(top_xgi, hide_index=True, use_container_width=True)

else:
    # Welcome screen when no data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info("📈 **Overview**\n\nTrack top performers, form trends, and key metrics")
    
    with col2:
        st.info("👥 **Player Comparison**\n\nCompare players side-by-side with radar charts")
    
    with col3:
        st.info("🏆 **Team Analysis**\n\nAnalyze team attacking and defensive stats")
    
    with col4:
        st.info("📅 **Fixture Analysis**\n\nFind teams with best upcoming fixtures")
    
    st.markdown("---")
    st.warning("👈 **Get Started**: Click 'Download Data' in the sidebar to fetch the latest FPL data")
    
    st.markdown("### Features")
    st.markdown("""
    - 🎯 **Real-time FPL Data**: Directly from the official FPL API
    - 📊 **Interactive Visualizations**: Scatter plots, radar charts, and more
    - 🔥 **Form Analysis**: Rolling metrics for recent performance
    - ⚡ **xG Metrics**: Expected goals and assists
    - 🏠 **Home/Away Splits**: Detailed venue-based statistics
    - 💰 **Value Analysis**: Points per price insights
    - 📅 **Fixture Difficulty**: Upcoming fixture rankings and analysis
    """)

if __name__ == "__main__":
    pass
