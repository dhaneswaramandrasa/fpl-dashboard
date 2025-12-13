# ⚽ FPL Dashboard

A comprehensive Fantasy Premier League analysis dashboard built with Streamlit.

## Features

### 📈 Overview Page
- **Top Performers**: View the highest-scoring players across all positions
- **Performance Analysis**: Interactive scatter plots showing Points vs xGI relationships
- **Form Trends**: Identify players in hot/cold form
- **Value Analysis**: Find players over/under-performing their xG/xA
- **Efficiency Metrics**: Best points per 90, bonus points leaders

### 👥 Player Comparison
- **Side-by-Side Comparison**: Compare 2-5 players simultaneously
- **Radar Charts**: Visual comparison across multiple metrics (percentile-based)
- **Performance Metrics**: Detailed bar charts and statistics
- **Form Trends**: Track points over recent gameweeks
- **Detailed Stats Table**: Complete statistical breakdown

### 🏆 Team Analysis
- **Attack vs Defense Map**: Interactive scatter plot positioning all teams
- **Team Categories**: Identify strong, vulnerable, attack/defense-focused teams
- **Attacking Stats**: Goals per game, total goals, best/worst attacks
- **Defensive Stats**: Goals conceded, clean sheets, defensive rankings
- **Head-to-Head Comparison**: Compare any two teams directly

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Steps

1. **Clone or download this repository**

2. **Navigate to the project directory**
```bash
cd fpl_dashboard
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## Usage

### Running the Dashboard

1. **Start the Streamlit app**
```bash
streamlit run app.py
```

2. **Open your browser**
The dashboard will automatically open at `http://localhost:8501`

3. **Download FPL Data**
- Click the "📥 Download Data" button in the sidebar
- Wait for the data scraping to complete (2-3 minutes for full dataset)
- The dashboard will automatically load once data is ready

### Using the Dashboard

#### Overview Tab
1. Use the sidebar filters to select position and minimum minutes
2. View scatter plots to identify top performers
3. Check the "Form Trends" tab to see hot/cold form players
4. Explore "Value Analysis" for xG over/under-performers

#### Player Comparison Tab
1. Filter players by position and minimum minutes
2. Select 2-5 players from the dropdown
3. Compare using:
   - Radar charts (percentile-based comparisons)
   - Performance bars (points, goals, assists)
   - Form trends over recent gameweeks
   - Detailed statistics table

#### Team Analysis Tab
1. View the overview scatter plot to see all teams positioned by attack/defense
2. Explore "Attacking Stats" for offensive metrics
3. Check "Defensive Stats" for clean sheets and goals conceded
4. Use "Team Comparison" to compare any two teams head-to-head

## Data Sources

- **Official FPL API**: Player and team statistics
- **Live Updates**: Data can be refreshed at any time via the sidebar

## Key Metrics Explained

### Player Metrics
- **xGI**: Expected Goal Involvements (xG + xA)
- **Points/90**: FPL points per 90 minutes
- **Form Trend**: Recent points/90 minus season average
- **xG Overperformance**: Actual goals minus expected goals
- **Hot Form**: Players performing significantly better recently (>1.0 pts/90 improvement)

### Team Metrics
- **Goals/Game**: Average goals scored per game
- **Conceded/Game**: Average goals conceded per game
- **Clean Sheet %**: Percentage of games with no goals conceded
- **xG**: Expected goals based on shot quality (when available)

## Deployment

### Streamlit Cloud (Free)

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR_REPO_URL
git push -u origin main
```

2. **Deploy on Streamlit Cloud**
- Go to [share.streamlit.io](https://share.streamlit.io)
- Connect your GitHub account
- Select your repository
- Click "Deploy"

Your dashboard will be live at `https://[your-app-name].streamlit.app`

### Local Network Access

To share on your local network:
```bash
streamlit run app.py --server.address 0.0.0.0
```

Access from other devices using: `http://YOUR_IP_ADDRESS:8501`

## File Structure

```
fpl_dashboard/
├── app.py                          # Main application
├── requirements.txt                # Dependencies
├── README.md                       # This file
├── data/                          # Data storage (created automatically)
│   ├── enhanced_player_aggregation.csv
│   ├── fpl_match_data.csv
│   ├── team_defensive_analysis.csv
│   └── team_attacking_analysis.csv
├── pages/                         # Page modules
│   ├── __init__.py
│   ├── overview.py                # Overview page
│   ├── player_comparison.py       # Player comparison page
│   └── team_analysis.py           # Team analysis page
└── utils/                         # Utility modules
    ├── __init__.py
    ├── data_loader.py             # Data loading functions
    └── scraper.py                 # FPL API scraper
```

## Troubleshooting

### Data not loading?
- Click "🔄 Refresh Data" in the sidebar
- Check your internet connection
- The FPL API may be temporarily unavailable during gameweeks

### Slow performance?
- Reduce minimum minutes filter to show fewer players
- Filter by specific position
- The initial data download takes 2-3 minutes

### Package installation errors?
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

## Contributing

Feel free to fork this repository and submit pull requests for any improvements!

## License

MIT License - feel free to use for personal or commercial projects.

## Acknowledgments

- Data from [Fantasy Premier League Official API](https://fantasy.premierleague.com/api/)
- Built with [Streamlit](https://streamlit.io/)
- Visualizations powered by [Plotly](https://plotly.com/)

## Support

For issues or questions, please open an issue on the GitHub repository.

---

**Enjoy analyzing your FPL team! ⚽📊**
