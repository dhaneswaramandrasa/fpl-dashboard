# FPL Dashboard - Complete Overview

## 🎯 What You've Received

A fully functional, production-ready Fantasy Premier League analytics dashboard built with **Streamlit**. This is a complete web application that can run locally or be deployed to the cloud **for free**.

## 📦 Package Contents

```
fpl_dashboard/
├── app.py                          # Main application entry point
├── requirements.txt                # All dependencies
├── README.md                       # Full documentation
├── QUICKSTART.md                   # Quick start guide
├── run.sh                          # Linux/Mac run script
├── run.bat                         # Windows run script
├── .gitignore                      # Git ignore file
├── pages/                          # Dashboard pages
│   ├── overview.py                 # Overview/analytics page
│   ├── player_comparison.py        # Player comparison page
│   └── team_analysis.py            # Team analysis page
└── utils/                          # Utility modules
    ├── data_loader.py              # Data loading functions
    └── scraper.py                  # FPL API data scraper
```

## 🚀 Getting Started (3 Steps)

### Step 1: Extract & Navigate
```bash
unzip fpl_dashboard.zip
cd fpl_dashboard
```

### Step 2: Run the Dashboard

**Option A - Automatic (Recommended):**
```bash
# Mac/Linux
./run.sh

# Windows
run.bat
```

**Option B - Manual:**
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Step 3: Download Data
1. Dashboard opens at http://localhost:8501
2. Click "📥 Download Data" in sidebar
3. Wait 2-3 minutes for scraping to complete
4. Start exploring!

## 📊 Dashboard Features

### 1️⃣ OVERVIEW PAGE - High-Level Analytics

**What it shows:**
- Top scorers across all positions
- Players in hot/cold form
- Performance scatter plots (Points vs xGI)
- Value analysis (xG over/under-performers)
- Efficiency metrics (Points/90, Bonus/90)

**Key Visualizations:**
- **Performance Scatter Plot**: Shows total points vs expected goal involvements, with bubble size representing minutes played
- **Recent Form Scatter**: Points/90 vs xGI/90 for last 5 games
- **Form Distribution**: Box plots showing form trends by position
- **Value Charts**: Goals vs xG scatter to find over-performers

**Filters Available:**
- Position (FWD, MID, DEF, GK, or All)
- Minimum minutes played

**Use Cases:**
- Find in-form players for transfers
- Identify value picks (high points, low cost)
- Spot players about to haul (high xG, low actual goals)
- Compare season performance vs recent form

### 2️⃣ PLAYER COMPARISON PAGE - Head-to-Head Analysis

**What it shows:**
- Compare 2-5 players simultaneously
- Radar charts (percentile comparisons)
- Bar charts for key metrics
- Form trends over gameweeks
- Detailed statistics table

**Key Visualizations:**
- **Overall Performance Radar**: Percentile rankings across 5 key metrics
- **Attacking Output Radar**: Goals, assists, xG, xA, xGI comparison
- **Recent Form Radar**: Last 5 games performance
- **Performance Bars**: Total points, goals, assists comparisons
- **Form Trend Line**: Points over last 10 gameweeks

**Filters Available:**
- Position filter (focus comparison on same position)
- Minimum minutes (show only regular starters)

**Use Cases:**
- Transfer decisions (Player A vs Player B)
- Differential picks (find undervalued players)
- Captain selection (who's in best form?)
- Template vs differential comparison

### 3️⃣ TEAM ANALYSIS PAGE - Team Performance

**What it shows:**
- Attack vs Defense positioning map
- Team categories (Strong, Vulnerable, etc.)
- Attacking statistics and rankings
- Defensive statistics and clean sheets
- Head-to-head team comparisons

**Key Visualizations:**
- **Attack vs Defense Scatter**: All teams positioned by offensive/defensive performance
- **Goals per Game Bar Chart**: Attacking form rankings
- **Goals Conceded Chart**: Defensive vulnerability
- **Clean Sheets Chart**: Best defensive teams
- **Team Comparison**: Side-by-side metrics for any 2 teams

**Use Cases:**
- Find vulnerable defenses to target with attackers
- Identify best defenses for defensive assets
- Double gameweek planning
- Fixture swing analysis

## 🎯 Key Metrics Explained

### Player Metrics

| Metric | Description |
|--------|-------------|
| **Total Points** | Season FPL points |
| **Points/90** | Points per 90 minutes (season or recent) |
| **xGI** | Expected Goal Involvements (xG + xA) |
| **xGI/90** | Expected goal involvements per 90 minutes |
| **Form Trend** | Recent form vs season average (positive = improving) |
| **Hot Form** | Flag for players performing >1.0 pts/90 better recently |
| **xG Overperformance** | Actual goals minus expected goals (positive = clinical) |
| **Bonus/90** | Bonus points per 90 minutes |

### Team Metrics

| Metric | Description |
|--------|-------------|
| **Goals/Game** | Average goals scored per match |
| **Conceded/Game** | Average goals conceded per match |
| **Clean Sheet %** | Percentage of matches with no goals conceded |
| **xG** | Expected goals (when available) |

## 💡 Pro Tips & Strategies

### Finding Transfers

1. **Hot Form Players**
   - Go to Overview → Form Trends
   - Look for "Hot Form" flag
   - Check they have good upcoming fixtures

2. **Value Picks**
   - Overview → Value Analysis
   - Find xG under-performers (due a haul)
   - Check if minutes are consistent

3. **Differential Picks**
   - Player Comparison → Compare template vs differential
   - Look for similar xGI but lower ownership

### Captain Selection

1. **Compare Top Options**
   - Player Comparison → Select 3-5 premium players
   - Check Recent Form radar chart
   - Review form trend over last 10 games

2. **Check Opponent**
   - Team Analysis → Find their opponent
   - Look at defensive stats (conceded/game)
   - Higher conceding = better captain option

### Planning Ahead

1. **Fixture Swings**
   - Team Analysis → Compare teams
   - Identify teams with good upcoming fixtures
   - Target players from those teams

2. **Double Gameweeks**
   - Team Analysis → Check attacking/defensive stats
   - Pick players from strongest teams

## 🌐 Deployment Options

### Option 1: Streamlit Cloud (Free & Easy)

**Perfect for sharing with mini-league!**

1. Create GitHub account
2. Create new repository
3. Upload fpl_dashboard folder
4. Go to [share.streamlit.io](https://share.streamlit.io)
5. Connect GitHub and select repository
6. Deploy!

**Result**: Live URL like `https://your-fpl-dashboard.streamlit.app`

### Option 2: Local Network Sharing

Share on your home/office network:

```bash
streamlit run app.py --server.address 0.0.0.0
```

Others can access at: `http://YOUR_IP_ADDRESS:8501`

### Option 3: Cloud Hosting

Deploy to any cloud platform:
- Heroku (free tier available)
- Google Cloud Run
- AWS Elastic Beanstalk
- DigitalOcean App Platform

## 🔧 Customization Guide

### Adding New Metrics

Edit `utils/scraper.py` to add new calculated metrics:

```python
# In aggregate_player_stats function
season_agg['your_new_metric'] = season_agg['some_column'] / season_agg['other_column']
```

### Changing Colors

Edit visualization colors in page files:

```python
# In any page .py file
colors = ['#YOUR_HEX_COLOR_1', '#YOUR_HEX_COLOR_2', ...]
```

### Adding New Visualizations

Add new charts in the page files:

```python
# In pages/overview.py or other page files
fig = px.scatter(df, x='metric1', y='metric2')
st.plotly_chart(fig)
```

## 📱 Mobile Responsive

The dashboard is fully responsive and works on:
- 📱 Phones
- 📱 Tablets  
- 💻 Laptops
- 🖥️ Desktops

## ⚡ Performance Tips

1. **Faster Loading**
   - Use position filters
   - Increase minimum minutes
   - This reduces data points

2. **Data Refresh**
   - Refresh data once per gameweek
   - Not needed more frequently
   - Each refresh takes 2-3 minutes

3. **Browser Cache**
   - Streamlit caches data automatically
   - Much faster after first load

## 🆘 Troubleshooting

### Dashboard won't start
```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --no-cache-dir
```

### Data not loading
- Check internet connection
- FPL API may be down during gameweek deadline
- Try "Refresh Data" button

### Slow performance
- Increase minimum minutes filter
- Select specific position
- Close other browser tabs

### Port already in use
```bash
# Use different port
streamlit run app.py --server.port 8502
```

## 📚 Technical Details

### Built With
- **Streamlit**: Web application framework
- **Plotly**: Interactive visualizations
- **Pandas**: Data manipulation
- **Requests**: API data fetching

### Data Source
- Official FPL API
- Updated in real-time
- No API key required
- Rate-limited (handled automatically)

### Data Storage
- CSV files in `data/` directory
- Created automatically on first run
- Can be deleted and re-downloaded

## 🎓 Learning Resources

Want to understand the code better?

- [Streamlit Documentation](https://docs.streamlit.io)
- [Plotly Python Documentation](https://plotly.com/python/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [FPL API Guide](https://medium.com/@frenzelts/fantasy-premier-league-api-endpoints-a-detailed-guide-acbd5598eb19)

## 🤝 Support & Community

- Star the repository on GitHub
- Share with your FPL mini-league
- Report bugs via GitHub issues
- Suggest features via discussions

## 📄 License

MIT License - Use freely for personal or commercial projects

---

## 🎉 You're Ready!

You now have a professional-grade FPL analytics tool. Use it to:
- ✅ Make better transfer decisions
- ✅ Pick the right captain
- ✅ Find differentials
- ✅ Plan ahead for fixture swings
- ✅ Dominate your mini-league!

**Good luck with your FPL season! ⚽🏆**
