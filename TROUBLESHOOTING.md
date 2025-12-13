# Troubleshooting Guide

## Common Issues and Solutions

### 🔴 Pages Not Loading / Tabs Empty

**Symptoms:**
- Click on Overview/Player Comparison/Team Analysis tabs
- Page is blank or shows loading forever
- Error messages in console

**Solutions:**

1. **Check if data is downloaded**
   - Look at the sidebar
   - Should show "✅ Data files found"
   - If not, click "📥 Download Data"

2. **Restart the dashboard**
   ```bash
   # Stop: Press Ctrl+C
   # Start again:
   streamlit run app.py
   ```

3. **Clear Streamlit cache**
   - Click the hamburger menu (☰) in top right
   - Click "Clear cache"
   - Click "Rerun"

4. **Check for error details**
   - Look at the terminal/console where you ran the app
   - Error messages will appear there
   - Share these if asking for help

---

### 🔴 Data Download Fails

**Symptoms:**
- "Download Data" button clicked but nothing happens
- Error during data scraping
- "No data available" message

**Solutions:**

1. **Check internet connection**
   - FPL API requires internet
   - Test: Visit https://fantasy.premierleague.com

2. **Wait and retry**
   - FPL API may be temporarily down
   - Usually happens during gameweek deadlines
   - Try again in 5-10 minutes

3. **Check API availability**
   - Go to: https://fantasy.premierleague.com/api/bootstrap-static/
   - Should show JSON data
   - If blank/error, FPL API is down

4. **Manual data download** (if API is down)
   ```bash
   # In terminal, in the fpl_dashboard folder:
   python -c "from utils.scraper import scrape_all_data; scrape_all_data()"
   ```

---

### 🔴 TypeError: unsupported operand type(s) for /: 'str' and 'int'

**This should be fixed in v1.1!**

If you still see this:

1. **Make sure you have the latest version**
   - Re-download `fpl_dashboard.zip`
   - Extract and replace old folder

2. **Check the file version**
   - Open `utils/scraper.py`
   - Look for line ~65: should have `pd.to_numeric(df[col], errors='coerce')`
   - If not present, you have an old version

3. **Force reinstall**
   ```bash
   rm -rf fpl_dashboard
   unzip fpl_dashboard.zip
   cd fpl_dashboard
   pip install -r requirements.txt --force-reinstall
   streamlit run app.py
   ```

---

### 🔴 Empty Visualizations / No Data Showing

**Symptoms:**
- Scatter plots are empty
- Tables show "No data"
- Charts don't render

**Solutions:**

1. **Adjust filters**
   - Minimum minutes might be too high
   - Try setting to 0 or 90
   - Select "All" for position filter

2. **Check data files**
   ```bash
   ls data/
   # Should show:
   # - enhanced_player_aggregation.csv
   # - fpl_match_data.csv
   # - team_defensive_analysis.csv
   # - team_attacking_analysis.csv
   ```

3. **Verify data content**
   ```bash
   wc -l data/enhanced_player_aggregation.csv
   # Should show 400+ lines
   ```

4. **Re-download data**
   - Click "🔄 Refresh Data" in sidebar
   - Wait for completion

---

### 🔴 Import Errors

**Symptoms:**
- `ModuleNotFoundError: No module named 'streamlit'`
- `ModuleNotFoundError: No module named 'plotly'`

**Solutions:**

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Check Python version**
   ```bash
   python --version
   # Should be 3.8 or higher
   ```

3. **Use virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Mac/Linux
   # or
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

---

### 🔴 Port Already in Use

**Symptoms:**
- `Address already in use`
- Can't start Streamlit

**Solutions:**

1. **Use different port**
   ```bash
   streamlit run app.py --server.port 8502
   ```

2. **Kill existing process**
   ```bash
   # Mac/Linux
   lsof -ti:8501 | xargs kill -9
   
   # Windows
   netstat -ano | findstr :8501
   # Note the PID, then:
   taskkill /PID [PID] /F
   ```

---

### 🔴 Slow Performance

**Symptoms:**
- Dashboard is slow
- Plots take long to render
- Filtering is laggy

**Solutions:**

1. **Increase minimum minutes filter**
   - Set to 450+ for starters only
   - Reduces data points significantly

2. **Filter by position**
   - Select specific position instead of "All"
   - Much faster rendering

3. **Close other tabs/apps**
   - Browser memory usage affects performance
   - Close unnecessary tabs

4. **Refresh browser**
   - Sometimes Streamlit cache gets full
   - Refresh page (F5)

---

### 🔴 Deployment Issues

#### Streamlit Cloud

**Problem**: App won't deploy

**Solutions:**
1. Check `requirements.txt` is in root folder
2. Verify `app.py` is in root folder
3. Check GitHub repository structure matches local

**Problem**: App crashes on Streamlit Cloud

**Solutions:**
1. Check logs in Streamlit Cloud dashboard
2. Verify all dependencies in `requirements.txt`
3. Ensure no local file paths in code

#### Local Network

**Problem**: Others can't access

**Solutions:**
1. Check firewall settings
2. Verify IP address:
   ```bash
   # Mac/Linux
   ifconfig | grep inet
   
   # Windows
   ipconfig
   ```
3. Make sure running with `--server.address 0.0.0.0`

---

### 🔴 Data Quality Issues

**Symptoms:**
- Strange player names
- Missing statistics
- Incorrect values

**Solutions:**

1. **Re-download data**
   - FPL API may have had issues
   - Click "Refresh Data"

2. **Check during non-peak times**
   - API is most reliable mid-week
   - Avoid gameweek deadline hours

3. **Verify on FPL website**
   - Go to official FPL site
   - Check if data matches
   - If FPL site has issues, our data will too

---

## 🆘 Still Having Issues?

### Debug Mode

Run with verbose logging:
```bash
streamlit run app.py --logger.level debug
```

### Check Logs

Look in terminal for detailed error messages:
```bash
streamlit run app.py 2>&1 | tee debug.log
```

### Get Help

1. **Check CHANGELOG.md** - Issue might be fixed in latest version
2. **Read OVERVIEW.md** - Comprehensive feature guide
3. **Check GitHub Issues** - See if others had same problem
4. **Create GitHub Issue** - Include:
   - Python version: `python --version`
   - OS: Windows/Mac/Linux
   - Error message (full traceback)
   - Steps to reproduce

---

## 💡 Tips for Best Experience

✅ **Refresh data weekly** - Keep stats current
✅ **Use filters wisely** - Improve performance
✅ **Check during mid-week** - API most reliable
✅ **Close unused tabs** - Reduce browser memory
✅ **Use Chrome/Firefox** - Best Streamlit support
✅ **Restart occasionally** - Clears cache issues

---

**Most issues are solved by:**
1. Re-downloading the latest version
2. Refreshing data
3. Restarting the app
4. Clearing browser cache

Good luck! ⚽🎯
