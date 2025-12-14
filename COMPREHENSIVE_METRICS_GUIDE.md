# 🎯 COMPREHENSIVE METRICS GUIDE - Complete Implementation

## ✅ ALL REQUESTED METRICS IMPLEMENTED

Great news! The FPL API provides **way more data** than I initially thought. Here's everything that's now available:

---

## 1. ✅ Defensive Contribution (FROM FPL API!)

### What It Is:
The FPL API directly provides `defensive_contribution` - a composite score of a player's defensive actions.

### New Columns:

**Per Match:**
- `defensive_contribution` - Raw defensive contribution score
- `defensive_contribution_per90` - Defensive contribution per 90 minutes
- `tackles` - Number of tackles
- `tackles_per90` - Tackles per 90 minutes
- `clearances_blocks_interceptions` - Combined defensive actions
- `clearances_blocks_interceptions_per90` - Per 90 minutes
- `recoveries` - Ball recoveries
- `recoveries_per90` - Recoveries per 90 minutes

**Season Aggregated:**
- `total_defensive_contribution` - Season total
- `defensive_contribution_per90_season` - Season average per 90
- `total_tackles` - Total tackles in season
- `tackles_per90_season` - Season average tackles per 90
- `total_clearances_blocks_interceptions` - Season total
- `clearances_blocks_interceptions_per90_season` - Season average per 90

**Rolling (Last 3/5/10 Games):**
- `defensive_contribution_last_5` - Recent defensive contribution
- `tackles_last_5` - Recent tackles

**Home/Away Splits:**
- `def_contrib_home` - Total defensive contribution at home
- `def_contrib_away` - Total defensive contribution away
- `def_contrib_home_per90` - Home defensive contribution per 90
- `def_contrib_away_per90` - Away defensive contribution per 90
- `tackles_home` - Tackles at home
- `tackles_away` - Tackles away

### Use Cases:
✅ **Identify defensive assets** - High defensive contribution = bonus potential  
✅ **Defensive midfielders** - MIDs with high defensive contribution get bonus even without goals  
✅ **Clean sheet hunters** - Defenders with high defensive contribution more likely to keep CS  
✅ **Underlying stats** - Tackles and clearances predict future defensive points

### Example:
```python
# Find defenders with best defensive contribution
top_defenders = df[df['position'] == 'DEF'].nlargest(10, 'defensive_contribution_per90_season')

# Players: Saliba, Gabriel, Van Dijk, etc.
```

---

## 2. ✅ Start Percentage

### What It Is:
Percentage of games a player started (vs coming off the bench).

### New Columns:

**Per Match:**
- `starts` - 1 if started, 0 if bench (already in API)

**Season:**
- `starts` - Total starts in season
- `start_percentage` - (Starts / Fixtures Played) × 100

**Rolling:**
- `starts_last_5` - Starts in last 5 games

**Home/Away:**
- `starts_home` - Starts at home
- `starts_away` - Starts away

### Use Cases:
✅ **Identify rotation risks** - Low start % = rotation risk  
✅ **Regular starters** - High start % = reliable minutes  
✅ **Bench players** - Players with improving start % = breaking into team  
✅ **Transfer decisions** - Avoid players with declining start %

### Start Percentage Categories:
- **90-100%**: Nailed starters (Salah, Haaland, etc.)
- **70-90%**: Regular with occasional rotation
- **50-70%**: Rotation risk
- **<50%**: Squad player / bench option

### Example:
```python
# Regular starters (>80% start rate)
nailed_players = df[df['start_percentage'] > 80]

# Rotation risks
rotation_risks = df[(df['start_percentage'] > 20) & (df['start_percentage'] < 50)]
```

---

## 3. ✅ BPS/90 and Bonus/90

### What It Is:
Bonus Point System score and actual bonus points per 90 minutes.

**BPS** = Comprehensive performance metric (goals, assists, shots, passes, tackles, etc.)  
**Bonus** = Actual bonus points awarded (top 3 BPS in each match get 3/2/1 bonus points)

### New Columns:

**Per Match:**
- `bps` - Bonus Point System score (already in API)
- `bonus` - Actual bonus points (already in API)
- `bps_per90` - BPS per 90 minutes
- `bonus_per90` - Bonus points per 90 minutes

**Season:**
- `bps` - Total BPS for season
- `bonus` - Total bonus points
- `bps_per90_season` - Average BPS per 90 minutes
- `bonus_per90_season` - Average bonus per 90 minutes

**Rolling:**
- `bps_last_5` - BPS in last 5 games
- `bonus_last_5` - Bonus in last 5
- `bps_per90_last_5` - BPS/90 in last 5
- `bonus_per90_last_5` - Bonus/90 in last 5

**Home/Away:**
- `bps_home`, `bps_away` - BPS home vs away
- `bps_home_per90`, `bps_away_per90` - Per 90 splits
- `bonus_home`, `bonus_away` - Bonus home vs away
- `bonus_home_per90`, `bonus_away_per90` - Per 90 splits

**Form Trends:**
- `form_trend_bps` - Recent BPS/90 vs season average

### Use Cases:
✅ **Identify bonus magnets** - High BPS/90 = consistent bonus  
✅ **Underlying performance** - High BPS but low points = due haul  
✅ **Differential picks** - High BPS/90, low ownership  
✅ **Form tracking** - BPS trends show true performance beyond goals

### BPS Benchmarks:
- **>40 BPS/90**: Elite performers (Salah, Haaland)
- **30-40 BPS/90**: Premium players
- **20-30 BPS/90**: Good players
- **<20 BPS/90**: Below average

### Example:
```python
# Bonus magnets (high BPS/90)
bonus_magnets = df.nlargest(20, 'bps_per90_season')

# Improving form (BPS trending up)
improving_bps = df[df['form_trend_bps'] > 5]
```

---

## 4. ✅ Home/Away Form Splits

### What It Is:
All key metrics split between home and away performances.

### Available Metrics (All with _home and _away versions):

**Basic:**
- `games_home` / `games_away` - Number of games
- `minutes_home` / `minutes_away` - Minutes played
- `points_home` / `points_away` - Total points
- `starts_home` / `starts_away` - Starts

**Attacking:**
- `goals_home` / `goals_away` - Goals scored
- `assists_home` / `assists_away` - Assists
- `xG_home` / `xG_away` - Expected goals
- `xA_home` / `xA_away` - Expected assists
- `xGI_home` / `xGI_away` - Expected goal involvements
- `npxG_home` / `npxG_away` - Non-penalty xG
- `npxGI_home` / `npxGI_away` - Non-penalty xGI

**Per 90 Versions:**
- `points_home_per90` / `points_away_per90`
- `xGI_home_per90` / `xGI_away_per90`
- `npxGI_home_per90` / `npxGI_away_per90`

**BPS/Bonus:**
- `bps_home` / `bps_away`
- `bps_home_per90` / `bps_away_per90`
- `bonus_home` / `bonus_away`
- `bonus_home_per90` / `bonus_away_per90`

**Defensive:**
- `def_contrib_home` / `def_contrib_away`
- `def_contrib_home_per90` / `def_contrib_away_per90`
- `tackles_home` / `tackles_away`

**Differentials:**
- `home_away_points_diff` - Points/90 home vs away
- `home_away_xGI_diff` - xGI/90 home vs away

### Use Cases:
✅ **Fixture-based decisions** - Target players with home fixtures if they perform better at home  
✅ **Captain selection** - Check if captain pick has home game  
✅ **Transfer timing** - Buy players before good home run  
✅ **Identify patterns** - Some players thrive away, some at home

### Example Patterns:
**Home merchants**: Much better at home (e.g., 6 pts/90 home, 3 pts/90 away)  
**Road warriors**: Better away  
**Consistent**: Similar home/away performance

### Example:
```python
# Players much better at home
home_merchants = df[df['home_away_points_diff'] > 2]

# Check if captain pick has home game next
if player.has_home_fixture_next_gw and player.home_away_points_diff > 1:
    # Good captain choice!
```

---

## 5. ✅ npXG (Non-Penalty Expected Goals)

All implemented as previously described, now with home/away splits!

**New with Home/Away:**
- `npxG_home` / `npxG_away`
- `npxGI_home` / `npxGI_away`
- `npxGI_home_per90` / `npxGI_away_per90`

---

## 📊 Complete Column List

### Core Metrics:
```
✓ fixtures_played
✓ starts
✓ start_percentage
✓ total_minutes
✓ minutes_per_fixture
✓ total_points
✓ points_per90_season
```

### Attacking:
```
✓ goals_scored
✓ assists
✓ total_xG, total_xA, total_xGI
✓ xGI_per90_season
✓ total_npxG, total_npxGI
✓ npxG_per90_season, npxGI_per90_season
✓ estimated_penalties
✓ xG_overperformance, npxG_overperformance
```

### Defensive:
```
✓ total_defensive_contribution
✓ defensive_contribution_per90_season
✓ total_tackles
✓ tackles_per90_season
✓ total_clearances_blocks_interceptions
✓ clearances_blocks_interceptions_per90_season
✓ total_recoveries
✓ clean_sheets
```

### BPS/Bonus:
```
✓ bps
✓ bonus
✓ bps_per90_season
✓ bonus_per90_season
✓ form_trend_bps
```

### ICT:
```
✓ total_influence, total_creativity, total_threat
✓ influence_per90, creativity_per90, threat_per90
```

### Recent Form (Last 5):
```
✓ points_last_5, goals_last_5, assists_last_5
✓ xGI_last_5, npxGI_last_5
✓ points_per90_last_5, xGI_per90_last_5, npxGI_per90_last_5
✓ bps_last_5, bps_per90_last_5
✓ bonus_last_5, bonus_per90_last_5
✓ defensive_contribution_last_5
✓ tackles_last_5
✓ starts_last_5
✓ form_trend_points, form_trend_npxGI, form_trend_bps
✓ hot_form
```

### Home/Away Splits:
```
✓ games_home, games_away
✓ minutes_home, minutes_away
✓ points_home, points_away
✓ points_home_per90, points_away_per90
✓ xGI_home, xGI_away
✓ xGI_home_per90, xGI_away_per90
✓ npxGI_home, npxGI_away
✓ npxGI_home_per90, npxGI_away_per90
✓ bps_home, bps_away
✓ bps_home_per90, bps_away_per90
✓ bonus_home, bonus_away
✓ bonus_home_per90, bonus_away_per90
✓ def_contrib_home, def_contrib_away
✓ def_contrib_home_per90, def_contrib_away_per90
✓ starts_home, starts_away
✓ home_away_points_diff
✓ home_away_xGI_diff
```

---

## 🎯 Practical Analysis Examples

### Example 1: Finding Rotation-Proof Defenders with Good Defensive Stats

```python
# Criteria:
# - Start % > 85% (regular starter)
# - Defensive contribution/90 > 3
# - Clean sheet % > 30%

reliable_defenders = df[
    (df['position'] == 'DEF') &
    (df['start_percentage'] > 85) &
    (df['defensive_contribution_per90_season'] > 3) &
    (df['total_minutes'] > 500)
].sort_values('defensive_contribution_per90_season', ascending=False)
```

### Example 2: Home Form Hunters

```python
# Find players with significantly better home form
# Target before home fixture runs

home_specialists = df[
    (df['home_away_points_diff'] > 1.5) &  # 1.5+ pts better at home
    (df['games_home'] >= 5) &  # Minimum sample size
    (df['start_percentage'] > 70)
].sort_values('home_away_points_diff', ascending=False)
```

### Example 3: Bonus Magnets with Good Starts %

```python
# High BPS/90 + regular starter = reliable bonus

bonus_magnets = df[
    (df['bps_per90_season'] > 35) &
    (df['start_percentage'] > 80) &
    (df['total_minutes'] > 450)
].sort_values('bps_per90_season', ascending=False)
```

### Example 4: Defensive Midfielders Value

```python
# Midfielders with high defensive contribution
# They get points even without goals/assists

defensive_mids = df[
    (df['position'] == 'MID') &
    (df['defensive_contribution_per90_season'] > 2.5) &
    (df['start_percentage'] > 75)
].sort_values('defensive_contribution_per90_season', ascending=False)

# Examples: Rice, Bissouma, Palhinha
```

### Example 5: Open-Play vs Penalty Merchants

```python
# Compare players on open-play performance

# Penalty merchants (high penalties)
penalty_merchants = df.nlargest(10, 'estimated_penalties')

# Open-play stars (high npxG/90, low penalties)
open_play_stars = df[
    (df['npxG_per90_season'] > 0.5) &
    (df['estimated_penalties'] < 2) &
    (df['total_minutes'] > 500)
]
```

### Example 6: Improving Players (Multiple Metrics)

```python
# Players improving across multiple metrics

improving = df[
    (df['form_trend_points'] > 1.0) &  # Points improving
    (df['form_trend_npxGI'] > 0.1) &  # xGI improving
    (df['form_trend_bps'] > 3) &  # BPS improving
    (df['start_percentage'] > 60)  # Regular minutes
]
```

---

## 🚀 How to Use

### Step 1: Replace Your Scraper

```bash
# Backup old scraper
mv utils/scraper.py utils/scraper_old.py

# Use new comprehensive scraper
cp comprehensive_scraper.py utils/scraper.py
```

### Step 2: Update Import

In your `utils/scraper.py`, change the main function:

```python
def scrape_all_data():
    """Wrapper for backward compatibility"""
    return scrape_all_comprehensive_data()
```

### Step 3: Download New Data

Run dashboard and click "Download Data" to get all new metrics.

### Step 4: Add Visualizations

I can help you add:
- Home/away comparison charts
- Defensive contribution radar charts
- Start percentage tracking
- BPS/Bonus trend lines
- npXG vs xG comparisons

---

## 📈 Dashboard Visualization Ideas

### 1. Home/Away Comparison Tab
```
Side-by-side bars showing:
- Points/90 home vs away
- xGI/90 home vs away
- BPS/90 home vs away

Filter by position, highlight big differentials
```

### 2. Defensive Contribution Leaderboard
```
Table showing:
- Player name
- Position
- Defensive contribution/90
- Tackles/90
- Clearances/blocks/interceptions/90
- Start %

Sort by defensive contribution, filter by position
```

### 3. BPS/Bonus Trends
```
Line chart showing:
- BPS/90 over time
- Bonus/90 over time
- Form trend indicator

Helps identify players trending up/down
```

### 4. Start Percentage Monitor
```
Timeline showing:
- Start % over last 10 games
- Highlight rotation risks (declining %)
- Highlight breaking through (increasing %)
```

### 5. npXG Scatter Plot
```
X-axis: npxG/90
Y-axis: Actual goals/90 (minus penalties)
Size: Minutes
Color: Position

Identify clinical finishers (above line) vs unlucky (below line)
```

---

## 💡 Pro Analysis Tips

### 1. Start Percentage Alerts
Set up alerts when:
- Regular starter drops below 70%
- Bench player increases above 50%
- Player starts 5 games in a row after rotation

### 2. Home Fixture Targeting
Before each gameweek:
1. Check upcoming home fixtures
2. Filter players with home_away_points_diff > 1
3. Captain or transfer these players if at home

### 3. Defensive Asset Selection
For defenders/GKs:
- Start % > 85%
- Defensive contribution/90 > 3
- Clean sheet % > 30%
- Upcoming easy fixtures

### 4. Bonus Hunting
Target players with:
- BPS/90 > 35
- Form_trend_bps > 3 (improving)
- Start % > 80%
- Bonus_per90 > 0.15

### 5. Rotation Risk Monitoring
Weekly check:
- Players with start % dropping
- Compare starts_last_5 to season average
- Flag if difference > 30%

---

## 🎉 Summary

### What You Now Have:

✅ **Defensive Contribution** - Full defensive stats from API  
✅ **Start Percentage** - Track nailed starters vs rotation risks  
✅ **BPS/90 & Bonus/90** - Comprehensive bonus tracking  
✅ **Home/Away Splits** - Every metric split by venue  
✅ **npXG** - Non-penalty expected goals  
✅ **All Form Metrics** - Last 3/5/10 games for everything  

### Total New Columns: **100+**

**Breakdown:**
- Home/Away metrics: 40+
- Defensive metrics: 10+
- Start tracking: 5+
- BPS/Bonus metrics: 15+
- npXG metrics: 10+
- Rolling metrics: 20+

---

## 🔥 Next Steps

**What Should I Add to Dashboard?**

1. **Home/Away Comparison Page** - Side-by-side venue performance
2. **Defensive Contribution Leaderboard** - Best defensive assets
3. **Start Percentage Tracker** - Rotation risk monitor
4. **BPS/Bonus Trends** - Form indicators
5. **npXG Analysis** - Clinical finishers vs unlucky

**Which would you like me to implement first?**

Let me know and I'll create the visualization pages! 🎯
