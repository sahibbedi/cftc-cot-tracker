import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def build_cot_chart():
    # 1. Fetch CFTC Data 
    url = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
    params = {
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 156
    }

    print("Fetching CFTC CoT Data...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    cot_df = pd.DataFrame(response.json())

    # Filter for Bitcoin data
    bitcoin_cot_df = cot_df[
        (cot_df['contract_market_name'].str.contains('BITCOIN', case=False, na=False)) |
        (cot_df['commodity_name'].str.contains('BITCOIN', case=False, na=False))
    ].copy()

    if bitcoin_cot_df.empty:
        print("No Bitcoin data found.")
        return 

    # Process Leveraged Funds Net Short
    cot_df = bitcoin_cot_df.copy() 
    # Ensure CFTC date is explicitly timezone-naive
    cot_df['Date'] = pd.to_datetime(cot_df['report_date_as_yyyy_mm_dd']).dt.tz_localize(None)
    cot_df['Lev_Short'] = pd.to_numeric(cot_df['lev_money_positions_short'])
    cot_df['Lev_Long'] = pd.to_numeric(cot_df['lev_money_positions_long'])
    cot_df['Net_Short'] = cot_df['Lev_Short'] - cot_df['Lev_Long']
    cot_df = cot_df[['Date', 'Net_Short']].sort_values('Date').set_index('Date')

   # 2. Fetch Pricing Data for Basis
    print("Fetching pricing data for basis overlay...")
    start_date = cot_df.index.min().strftime('%Y-%m-%d')
    
    # Switch back to yf.download() as it is more stable in GitHub Actions
    price_data = yf.download(["BTC-USD", "BTC=F"], start=start_date, progress=False)
    
    # SAFETY CHECK: If Yahoo blocked the request, exit cleanly
    if price_data.empty or 'Close' not in price_data:
        print("Error: Yahoo Finance returned no data (likely rate-limited). Try again later.")
        return
        
    spot = price_data['Close']['BTC-USD'].dropna()
    fut = price_data['Close']['BTC=F'].dropna()
    
    # THE FIX: Explicitly force the index to be a Datetime object, then strip timezones
    spot.index = pd.to_datetime(spot.index).tz_localize(None)
    fut.index = pd.to_datetime(fut.index).tz_localize(None)
    
    # Calculate basis
    ann_basis = ((fut / spot) - 1) * (365 / 30) * 100
    ann_basis.name = 'Ann_Basis_Pct'

    # 3. Merge Datasets 
    merged = cot_df.join(ann_basis, how='left')
    merged['Ann_Basis_Pct'] = merged['Ann_Basis_Pct'].ffill().bfill()

    # 4. Generate the Chart
    print("Generating chart...")
    fig, ax1 = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#ffffff')

    # Net Short Bar Chart
    color1 = '#E63946'
    ax1.bar(merged.index, merged['Net_Short'], width=5, color=color1, alpha=0.8, label='Lev Funds Net Short')
    ax1.set_ylabel('Leveraged Funds Net Short (Contracts)', color=color1, fontweight='bold', fontsize=11)
    ax1.tick_params(axis='y', labelcolor=color1)

    # THE TITLE FIX: Use suptitle for main, set_title for sub, and adjust margins
    latest_date = merged.index.max().strftime('%b %d, %Y')
    fig.suptitle('BTC CME Basis vs. Leveraged Fund Positioning', fontsize=16, fontweight='bold', y=0.98)
    ax1.set_title(f"The Crowding Premium (CFTC Data as of {latest_date})", fontsize=11, color='gray', pad=15)

    # Ann Basis Line Chart
    ax2 = ax1.twinx()
    color2 = '#1D3557'
    ax2.plot(merged.index, merged['Ann_Basis_Pct'], color=color2, linewidth=2.5, label='Ann. Basis (%)')
    ax2.set_ylabel('Annualised Basis (%)', color=color2, fontweight='bold', fontsize=11)
    ax2.tick_params(axis='y', labelcolor=color2)

    # Clean up X-Axis formatting
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45) 
    ax1.grid(True, linestyle='--', alpha=0.4)

    # Merge Legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', frameon=True)

    # Apply layout constraints
    fig.tight_layout()
    fig.subplots_adjust(top=0.85) # Explicitly push chart down to give titles space

    # Save as static image
    filename = 'cftc_btc_crowding.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Successfully generated '{filename}'")

if __name__ == "__main__":
    build_cot_chart()
