"""
Diagnostic Script - Check xG Data Availability
Run this to see why the xG/xGC tab isn't showing up
"""

import streamlit as st
import pandas as pd
from pathlib import Path

st.title("🔍 xG Data Diagnostic")

# Check 1: Session State Keys
st.subheader("1️⃣ Session State Check")

keys_to_check = ['team_defensive', 'team_attacking', 'match_data', 'data_loaded']

for key in keys_to_check:
    if key in st.session_state:
        value = st.session_state[key]
        if value is None:
            st.warning(f"❌ `{key}` exists but is None")
        elif isinstance(value, pd.DataFrame):
            if value.empty:
                st.warning(f"⚠️ `{key}` is an empty DataFrame")
            else:
                st.success(f"✅ `{key}` has {len(value)} rows")
        else:
            st.info(f"ℹ️ `{key}` = {value}")
    else:
        st.error(f"❌ `{key}` NOT in session_state")

# Check 2: Match Data Columns
st.markdown("---")
st.subheader("2️⃣ Match Data Columns Check")

if 'match_data' in st.session_state and st.session_state.match_data is not None:
    match_data = st.session_state.match_data
    
    if not match_data.empty:
        st.success(f"✅ Match data has {len(match_data)} rows")
        
        required_columns = [
            'expected_goals',
            'expected_assists', 
            'expected_goal_involvements',
            'player_team',
            'opponent_team',
            'fixture',
            'was_home',
            'round'
        ]
        
        st.markdown("**Required columns for xG calculation:**")
        missing_cols = []
        for col in required_columns:
            if col in match_data.columns:
                # Check if column has data
                non_null = match_data[col].notna().sum()
                total = len(match_data)
                st.success(f"✅ `{col}` - {non_null}/{total} non-null values")
            else:
                st.error(f"❌ `{col}` - MISSING")
                missing_cols.append(col)
        
        if missing_cols:
            st.error(f"🚨 Missing columns: {', '.join(missing_cols)}")
            st.info("These columns are required for xG calculations")
        
        # Show sample data
        st.markdown("**Sample match data (first 3 rows):**")
        sample_cols = [c for c in required_columns if c in match_data.columns]
        if sample_cols:
            st.dataframe(match_data[sample_cols].head(3))
    else:
        st.warning("⚠️ Match data DataFrame is empty")
else:
    st.error("❌ No match_data in session state")

# Check 3: Data Files
st.markdown("---")
st.subheader("3️⃣ Data Files Check")

data_dir = Path("data")
files_to_check = [
    'fpl_match_data.csv',
    'team_defensive_analysis.csv',
    'team_attacking_analysis.csv',
    'enhanced_player_aggregation.csv'
]

for file in files_to_check:
    file_path = data_dir / file
    if file_path.exists():
        size_kb = file_path.stat().st_size / 1024
        st.success(f"✅ `{file}` exists ({size_kb:.1f} KB)")
        
        # Load and check
        try:
            df = pd.read_csv(file_path)
            st.info(f"   📊 {len(df)} rows, {len(df.columns)} columns")
            
            if file == 'fpl_match_data.csv':
                # Check for xG columns
                xg_cols = ['expected_goals', 'expected_assists', 'expected_goal_involvements']
                for col in xg_cols:
                    if col in df.columns:
                        non_zero = (df[col] > 0).sum()
                        st.success(f"   ✅ `{col}` has {non_zero} non-zero values")
                    else:
                        st.error(f"   ❌ `{col}` missing")
        except Exception as e:
            st.error(f"   ❌ Error reading file: {str(e)}")
    else:
        st.error(f"❌ `{file}` NOT FOUND")

# Check 4: Import Test
st.markdown("---")
st.subheader("4️⃣ Import Test")

try:
    from utils.team_xg_aggregator import calculate_team_xg_stats, create_team_xg_leaderboard
    st.success("✅ Successfully imported team_xg_aggregator functions")
    
    # Try to calculate if we have match data
    if 'match_data' in st.session_state and st.session_state.match_data is not None:
        match_data = st.session_state.match_data
        if not match_data.empty:
            st.info("Attempting to calculate team xG stats...")
            try:
                team_xg_stats = calculate_team_xg_stats(match_data)
                if team_xg_stats is not None and not team_xg_stats.empty:
                    st.success(f"✅ Successfully calculated xG for {len(team_xg_stats)} teams!")
                    st.dataframe(team_xg_stats.head())
                else:
                    st.error("❌ Calculation returned empty DataFrame")
            except Exception as e:
                st.error(f"❌ Error during calculation: {str(e)}")
                st.exception(e)
        else:
            st.warning("⚠️ Match data is empty, cannot test calculation")
    else:
        st.warning("⚠️ No match_data available to test calculation")
        
except ImportError as e:
    st.error(f"❌ Cannot import team_xg_aggregator: {str(e)}")
    st.info("Make sure utils/team_xg_aggregator.py exists")

# Check 5: Recommendation
st.markdown("---")
st.subheader("5️⃣ Diagnosis & Next Steps")

# Determine the issue
if 'match_data' not in st.session_state or st.session_state.match_data is None:
    st.error("**Issue:** match_data is not in session state")
    st.markdown("""
    **Solution:**
    1. Make sure data scraping completed successfully
    2. Check that app.py loads match_data: `st.session_state.match_data = data['match_data']`
    3. Re-download data from the sidebar
    """)
elif st.session_state.match_data.empty:
    st.error("**Issue:** match_data is empty")
    st.markdown("""
    **Solution:**
    1. Re-download data from the sidebar
    2. Check if season has started (no match data before first gameweek)
    """)
elif 'expected_goals' not in st.session_state.match_data.columns:
    st.error("**Issue:** match_data missing xG columns")
    st.markdown("""
    **Solution:**
    1. Your scraper might not be collecting xG data
    2. Update utils/scraper.py to include xG fields
    3. Re-download data
    """)
else:
    st.success("**All checks passed!** The xG/xGC tab should work.")
    st.info("If you still don't see the tab, try refreshing the page or restarting Streamlit")

# Quick fix button
st.markdown("---")
if st.button("🔄 Reload Data from Files", type="primary"):
    from utils.data_loader import load_fpl_data
    
    with st.spinner("Loading data..."):
        data = load_fpl_data()
        if data:
            st.session_state.player_data = data['player_data']
            st.session_state.match_data = data['match_data']
            st.session_state.team_defensive = data['team_defensive']
            st.session_state.team_attacking = data['team_attacking']
            st.session_state.data_loaded = True
            st.success("✅ Data reloaded! Refresh this page to see updated results.")
            st.rerun()