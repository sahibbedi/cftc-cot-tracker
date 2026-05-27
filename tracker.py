import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def build_cot_chart():
    # 1. Fetch CFTC Data (Updated Endpoint)
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
        print("No Bitcoin data found with current filters.")
        return # Exit if no Bitcoin data

    # Process Leveraged Funds Net Short
    cot_df = bitcoin_cot_df.copy() 
    cot_df['Date'] = pd.to_datetime(cot_df['report_date_as_yyyy_mm_dd'])
    cot_df['Lev_Short'] = pd.to_numeric(cot_df['lev_money_positions_short'])
    cot_df['Lev_Long'] = pd.to_numeric(cot_df['lev_money_positions_long'])
    cot_df['Net_Short'] = cot_df['Lev_Short'] - cot_df['Lev_Long']
    cot_df = cot_df[['Date', 'Net_Short']].sort_values('Date').set_index('Date')

    # 2. Fetch Pricing Data for Basis
    print("Fetching pricing data for basis overlay...")
    start_date = cot_df.index.min().strftime('%Y-%m-%d')
    
    # Download as a list to ensure consistent column parsing in yfinance
    price_data = yf.download(["BTC-USD", "BTC=F"], start=start_date, progress=False)['Close']
    
    # Calculate basis and name the series so it merges cleanly
    ann_basis = ((price_data['BTC=F'] / price_data['BTC-USD']) - 1) * (365 / 30) * 100
    ann_basis.name = 'Ann_Basis_Pct'

    # 3. Merge Datasets 
    # Forward-fill (ffill) and backward-fill (bfill) to fix the missing line caused by weekend/holiday NaN gaps
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

    # Title & Subtitle (Adjusted padding and Y coordinates to prevent overlap)
    latest_date = merged.index.max().strftime('%b %d, %Y')
    plt.title('BTC CME Basis vs. Leveraged Fund Positioning', fontsize=16, fontweight='bold', pad=25)
    plt.suptitle(f"The Crowding Premium (CFTC Data as of {latest_date})", fontsize=11, color='gray', y=0.88)

    # Ann Basis Line Chart
    ax2 = ax1.twinx()
    color2 = '#1D3557'
    ax2.plot(merged.index, merged['Ann_Basis_Pct'], color=color2, linewidth=2.5, label='Ann. Basis (%)')
    ax2.set_ylabel('Annualised Basis (%)', color=color2, fontweight='bold', fontsize=11)
    ax2.tick_params(axis='y', labelcolor=color2)

    # Clean up X-Axis formatting
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45) # Angle dates slightly so they don't overlap on long timeframes
    ax1.grid(True, linestyle='--', alpha=0.4)

    # Merge Legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', frameon=True)

    # Tell tight_layout to leave room at the top for the suptitle
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    # Save as static image
    filename = 'cftc_btc_crowding.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Successfully generated '{filename}'")

# Execute the function
if __name__ == "__main__":
    build_cot_chart()
