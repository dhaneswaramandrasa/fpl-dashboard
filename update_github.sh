#!/bin/bash

# FPL Dashboard - GitHub Update Script (v2.0)
# Automatically updates repository with comprehensive metrics

echo "=================================================="
echo "FPL Dashboard - Update to v2.0"
echo "Comprehensive Metrics Implementation"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}Error: Not in a git repository!${NC}"
    echo "Please run this script from your fpl_dashboard root directory"
    exit 1
fi

echo -e "${YELLOW}Step 1: Creating backup branch${NC}"
git checkout -b backup-v1.2 2>/dev/null || echo "Branch already exists, continuing..."
git push origin backup-v1.2 2>/dev/null || echo "Backup branch already pushed"
git checkout main

echo ""
echo -e "${YELLOW}Step 2: Backing up current scraper${NC}"
cp utils/scraper.py utils/scraper_backup_v1.2.py
echo "✓ Backup created: utils/scraper_backup_v1.2.py"

echo ""
echo -e "${YELLOW}Step 3: Checking for new files${NC}"

# Check if comprehensive_scraper.py exists
if [ ! -f "comprehensive_scraper.py" ]; then
    echo -e "${RED}Error: comprehensive_scraper.py not found!${NC}"
    echo "Please make sure you have the comprehensive_scraper.py file in the current directory"
    exit 1
fi

# Check if guide exists
if [ ! -f "COMPREHENSIVE_METRICS_GUIDE.md" ]; then
    echo -e "${RED}Error: COMPREHENSIVE_METRICS_GUIDE.md not found!${NC}"
    echo "Please make sure you have the guide file in the current directory"
    exit 1
fi

echo "✓ All required files found"

echo ""
echo -e "${YELLOW}Step 4: Updating utils/scraper.py${NC}"

# Create a modified version of comprehensive_scraper.py with correct function names
cat comprehensive_scraper.py | sed 's/scrape_all_comprehensive_data/scrape_all_data/g' > utils/scraper.py

echo "✓ Scraper updated with comprehensive version"

echo ""
echo -e "${YELLOW}Step 5: Adding documentation${NC}"
cp COMPREHENSIVE_METRICS_GUIDE.md ./
echo "✓ Added COMPREHENSIVE_METRICS_GUIDE.md"

echo ""
echo -e "${YELLOW}Step 6: Updating CHANGELOG.md${NC}"

# Backup existing CHANGELOG
if [ -f "CHANGELOG.md" ]; then
    cp CHANGELOG.md CHANGELOG.md.bak
fi

# Create new CHANGELOG entry
cat > CHANGELOG_v2.md << 'EOF'
## Version 2.0 - 2024-12-15

### 🎉 MAJOR UPDATE: Comprehensive Metrics

#### ✨ New Features

**1. Defensive Contribution Metrics**
- Full defensive stats from FPL API
- `defensive_contribution`, `tackles`, `clearances_blocks_interceptions`
- All with per 90 and home/away splits
- Helps identify defensive assets and bonus potential

**2. Start Percentage Tracking**
- Track how often players start vs come off bench
- `start_percentage` - identify nailed starters vs rotation risks
- `starts_last_5` - recent starting frequency
- Home/away start splits

**3. BPS/90 and Bonus/90**
- Comprehensive bonus point tracking
- `bps_per90_season`, `bonus_per90_season`
- `form_trend_bps` - trending up or down
- Home/away splits for BPS and bonus

**4. Home/Away Form Splits (40+ metrics)**
- Every major metric now has home and away versions
- `points_home_per90`, `points_away_per90`
- `xGI_home_per90`, `xGI_away_per90`
- `bps_home_per90`, `bps_away_per90`
- `def_contrib_home_per90`, `def_contrib_away_per90`
- `home_away_points_diff`, `home_away_xGI_diff`

**5. npXG (Non-Penalty Expected Goals)**
- `npxG`, `npxGI` - open-play performance
- `npxG_per90_season`, `npxGI_per90_season`
- `estimated_penalties` - penalty taker identification
- `npxG_overperformance` - clinical finishing metric
- Home/away splits

#### 📊 New Columns Available

**Total: 100+ new columns**

**Defensive (10+):**
- defensive_contribution_per90_season
- tackles_per90_season
- clearances_blocks_interceptions_per90_season
- recoveries_per90_season
- Plus all home/away splits

**Start Tracking (5+):**
- start_percentage
- starts_home, starts_away
- starts_last_5

**BPS/Bonus (15+):**
- bps_per90_season, bonus_per90_season
- form_trend_bps
- bps/bonus home/away splits
- Rolling averages (last 3/5/10)

**Home/Away (40+):**
- All major metrics split by venue
- Performance differentials

**npXG (10+):**
- npxG/npxGI season and rolling
- Penalty estimates
- Overperformance metrics

#### 🎯 Use Cases

- ✅ Find rotation-proof defenders with high defensive contribution
- ✅ Target players with better home form before home fixtures
- ✅ Identify bonus magnets with high BPS/90
- ✅ Compare open-play performance (npxG) vs penalties
- ✅ Monitor start percentage for rotation risks

#### 🔧 Technical Changes

**Enhanced Scraper:**
- Comprehensive data extraction from FPL API
- New `defensive_contribution` field support
- Home/away aggregation system
- Start percentage calculation
- npXG estimation algorithm

**Data Pipeline:**
- All numeric fields properly typed
- Home/away split calculations
- Per 90 metrics for all stats
- Rolling windows with venue splits

#### 📚 Documentation

- New `COMPREHENSIVE_METRICS_GUIDE.md` with full metric explanations
- Use case examples and analysis patterns
- Dashboard visualization ideas

---

EOF

# Prepend to existing CHANGELOG
if [ -f "CHANGELOG.md" ]; then
    cat CHANGELOG_v2.md CHANGELOG.md > CHANGELOG_new.md
    mv CHANGELOG_new.md CHANGELOG.md
    rm CHANGELOG_v2.md
else
    mv CHANGELOG_v2.md CHANGELOG.md
fi

echo "✓ CHANGELOG.md updated"

echo ""
echo -e "${YELLOW}Step 7: Staging changes${NC}"
git add utils/scraper.py
git add COMPREHENSIVE_METRICS_GUIDE.md
git add CHANGELOG.md
git add utils/scraper_backup_v1.2.py

echo "✓ Changes staged"

echo ""
echo -e "${YELLOW}Step 8: Creating commit${NC}"
git commit -m "v2.0: Add comprehensive metrics

- Defensive contribution tracking
- Start percentage for rotation monitoring  
- BPS/90 and Bonus/90 metrics
- Home/Away form splits (40+ metrics)
- npXG (non-penalty expected goals)
- 100+ new columns total

See COMPREHENSIVE_METRICS_GUIDE.md for details"

echo "✓ Commit created"

echo ""
echo -e "${GREEN}=================================================="
echo "Update Complete!"
echo "==================================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Review changes: git log -1"
echo "  2. Push to GitHub: git push origin main"
echo "  3. (Optional) Create release tag: git tag v2.0.0 && git push origin v2.0.0"
echo ""
echo "To test locally before pushing:"
echo "  streamlit run app.py"
echo ""
echo -e "${YELLOW}Ready to push to GitHub? [y/N]${NC}"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo -e "${YELLOW}Pushing to GitHub...${NC}"
    git push origin main
    
    echo ""
    echo -e "${GREEN}✓ Successfully pushed to GitHub!${NC}"
    echo ""
    echo "Create a release? [y/N]"
    read -r release_response
    
    if [[ "$release_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo ""
        echo -e "${YELLOW}Creating release tag v2.0.0${NC}"
        git tag -a v2.0.0 -m "v2.0: Comprehensive Metrics - Defensive contribution, start %, home/away splits, BPS/90, npXG"
        git push origin v2.0.0
        echo ""
        echo -e "${GREEN}✓ Release tag created!${NC}"
        echo ""
        echo "Go to GitHub to create the release notes:"
        echo "https://github.com/YOUR_USERNAME/fpl_dashboard/releases/new?tag=v2.0.0"
    fi
else
    echo ""
    echo "Skipped push. You can push manually later with:"
    echo "  git push origin main"
fi

echo ""
echo -e "${GREEN}🎉 All done!${NC}"
echo ""
echo "What's next?"
echo "  • Test the dashboard locally"
echo "  • Download data to verify new metrics"
echo "  • Create visualizations for new metrics"
echo "  • Share with your users!"
echo ""
