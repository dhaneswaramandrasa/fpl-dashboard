"""
Quick Test Script - Run this to verify understatapi works
"""

print("="*70)
print("UNDERSTAT API PACKAGE - QUICK TEST")
print("="*70)
print()

# Step 1: Check if package is installed
print("Step 1: Checking if understatapi is installed...")
print("-"*70)

try:
    from understatapi import UnderstatClient
    print("✅ understatapi is installed")
except ImportError:
    print("❌ understatapi is NOT installed")
    print()
    print("Install it with:")
    print("  pip install understatapi")
    print()
    exit(1)

print()

# Step 2: Try to fetch data
print("Step 2: Testing connection to Understat...")
print("-"*70)

try:
    with UnderstatClient() as understat:
        # Get just a small sample of data
        print("Fetching Premier League 2024/25 data...")
        data = understat.league(league="EPL").get_player_data(season="2024")
        
        if data:
            print(f"✅ Successfully fetched {len(data)} players!")
            print()
            
            # Show sample data
            print("Sample data (first 5 players):")
            print("-"*70)
            import pandas as pd
            df = pd.DataFrame(data)
            
            # Convert numeric columns
            df['shots'] = pd.to_numeric(df['shots'], errors='coerce')
            df['goals'] = pd.to_numeric(df['goals'], errors='coerce')
            df['xG'] = pd.to_numeric(df['xG'], errors='coerce')
            
            # Show top shooters
            print("\nTop 5 by shots:")
            top_5 = df.nlargest(5, 'shots')[['player_name', 'team_title', 'shots', 'goals', 'xG']]
            print(top_5.to_string(index=False))
            
            print()
            print("="*70)
            print("✅ SUCCESS! Everything is working")
            print("="*70)
            print()
            print("You can now integrate this into your FPL dashboard!")
            print()
            print("Next step: Use understat_package_integration.py")
            
        else:
            print("❌ No data returned")
            
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Possible issues:")
    print("1. Understat website might be down")
    print("2. Network connection problems")
    print("3. Try again in a few minutes")