# 🚀 QUICK START GUIDE

Get your FPL Dashboard running in 3 simple steps!

## Step 1: Install Python Dependencies

### For Linux/Mac:
```bash
chmod +x run.sh
./run.sh
```

### For Windows:
```cmd
run.bat
```

### Manual Installation:
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Step 2: Open Dashboard

The dashboard will automatically open in your browser at:
```
http://localhost:8501
```

## Step 3: Download Data

1. Look for the sidebar on the left
2. Click the **"📥 Download Data"** button
3. Wait 2-3 minutes for data to download
4. Start analyzing!

## 📊 What You Can Do

### Overview Tab
- See top performers with scatter plots
- Find players in hot/cold form
- Identify value picks

### Player Comparison Tab
- Compare 2-5 players at once
- Use radar charts for visual comparison
- Track form over recent gameweeks

### Team Analysis Tab
- See which teams have best attack/defense
- Find vulnerable defenses to target
- Compare teams head-to-head

## 🎯 Pro Tips

1. **Filter by Position**: Use the sidebar to focus on specific positions
2. **Minimum Minutes**: Increase to show only regular starters
3. **Hot Form**: Look for players with "Hot Form" flag for transfers
4. **xG Metrics**: Use expected stats to find players likely to score soon
5. **Refresh Data**: Click refresh before each gameweek for latest stats

## 🆘 Need Help?

- **No data showing?** Click "Download Data" in sidebar
- **Slow loading?** Increase minimum minutes filter
- **Installation issues?** Check README.md for troubleshooting

## 🌐 Share With League

Want to share with your mini-league?

### Easy Option - Streamlit Cloud (Free):
1. Create a GitHub account
2. Push this folder to a new repository
3. Go to share.streamlit.io
4. Deploy your repository
5. Share the URL with friends!

### Local Network:
```bash
streamlit run app.py --server.address 0.0.0.0
```
Access from other devices: `http://YOUR_IP:8501`

---

**Ready to dominate your FPL league? Let's go! ⚽🏆**
