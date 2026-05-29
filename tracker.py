import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def build_cot_chart():
    # ------------------------------------------------------------------
    # 1. Fetch CFTC Data
    # ------------------------------------------------------------------
    url = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"

    params = {
        "$where": "contract_market_name like '%BITCOIN%'",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 156
    }

    print("Fetching CFTC CoT Data...")

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch CFTC data: {e}")
        return

    data = response.json()

    if not data:
        print("No data returned from CFTC API.")
        return

    cot_df = pd.DataFrame(data)

    print(f"Rows returned: {len(cot_df)}")
    print(f"Columns returned: {list(cot_df.columns)}")

    # Validate required columns
    required_columns = [
        "contract_market_name",
        "report_date_as_yyyy_mm_dd",
        "lev_money_positions_short",
        "lev_money_positions_long"
    ]

    missing = [c for c in required_columns if c not in cot_df.columns]

    if missing:
        print(f"Missing expected columns: {missing}")
        return

    bitcoin_cot_df = cot_df[
        cot_df["contract_market_name"].str.contains(
            "BITCOIN",
            case=False,
            na=False
        )
    ].copy()

    if bitcoin_cot_df.empty:
        print("No Bitcoin data found.")
        return

    # ------------------------------------------------------------------
    # 2. Process CoT Data
    # ------------------------------------------------------------------
    cot_df = bitcoin_cot_df.copy()

    cot_df["Date"] = pd.to_datetime(
        cot_df["report_date_as_yyyy_mm_dd"]
    ).dt.tz_localize(None)

    cot_df["Lev_Short"] = pd.to_numeric(
        cot_df["lev_money_positions_short"],
        errors="coerce"
    )

    cot_df["Lev_Long"] = pd.to_numeric(
        cot_df["lev_money_positions_long"],
        errors="coerce"
    )

    cot_df["Net_Short"] = cot_df["Lev_Short"] - cot_df["Lev_Long"]

    cot_df = (
        cot_df[["Date", "Net_Short"]]
        .dropna()
        .sort_values("Date")
        .set_index("Date")
    )

    if cot_df.empty:
        print("No usable CoT records after processing.")
        return

    # ------------------------------------------------------------------
    # 3. Fetch BTC Spot + Futures
    # ------------------------------------------------------------------
    print("Fetching pricing data...")

    start_date = cot_df.index.min().strftime("%Y-%m-%d")

    try:
        price_data = yf.download(
            ["BTC-USD", "BTC=F"],
            start=start_date,
            progress=False,
            auto_adjust=False
        )
    except Exception as e:
        print(f"Yahoo Finance download failed: {e}")
        return

    if price_data.empty:
        print("Yahoo Finance returned no data.")
        return

    if isinstance(price_data.columns, pd.MultiIndex):
        if "Close" in price_data.columns.get_level_values(0):
            close_df = price_data["Close"].dropna(how="all")
        elif "Close" in price_data.columns.get_level_values(1):
            close_df = price_data.xs(
                "Close",
                level=1,
                axis=1
            ).dropna(how="all")
        else:
            print("Close column not found.")
            return
    else:
        close_df = price_data.copy()

    if (
        "BTC-USD" not in close_df.columns
        or "BTC=F" not in close_df.columns
    ):
        print("Required Yahoo Finance symbols missing.")
        print(close_df.columns.tolist())
        return

    spot = close_df["BTC-USD"].copy()
    fut = close_df["BTC=F"].copy()

    spot.index = pd.to_datetime(spot.index).tz_localize(None)
    fut.index = pd.to_datetime(fut.index).tz_localize(None)

    ann_basis = ((fut / spot) - 1) * (365 / 30) * 100
    ann_basis.name = "Ann_Basis_Pct"

    # ------------------------------------------------------------------
    # 4. Merge
    # ------------------------------------------------------------------
    merged = cot_df.join(ann_basis, how="left")

    merged["Ann_Basis_Pct"] = (
        merged["Ann_Basis_Pct"]
        .ffill()
        .bfill()
    )

    # ------------------------------------------------------------------
    # 5. Plot
    # ------------------------------------------------------------------
    print("Generating chart...")

    fig, ax1 = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("white")

    color1 = "#E63946"

    ax1.bar(
        merged.index,
        merged["Net_Short"],
        width=5,
        color=color1,
        alpha=0.8,
        label="Lev Funds Net Short"
    )

    ax1.set_ylabel(
        "Leveraged Funds Net Short (Contracts)",
        color=color1,
        fontweight="bold"
    )

    ax1.tick_params(axis="y", labelcolor=color1)

    latest_date = merged.index.max().strftime("%b %d, %Y")

    fig.suptitle(
        "BTC CME Basis vs. Leveraged Fund Positioning",
        fontsize=16,
        fontweight="bold"
    )

    ax1.set_title(
        f"CFTC Data as of {latest_date}",
        fontsize=11,
        color="gray"
    )

    ax2 = ax1.twinx()

    color2 = "#1D3557"

    ax2.plot(
        merged.index,
        merged["Ann_Basis_Pct"],
        color=color2,
        linewidth=2.5,
        label="Ann. Basis (%)"
    )

    ax2.set_ylabel(
        "Annualised Basis (%)",
        color=color2,
        fontweight="bold"
    )

    ax2.tick_params(axis="y", labelcolor=color2)

    ax1.xaxis.set_major_formatter(
        mdates.DateFormatter("%b %Y")
    )

    plt.xticks(rotation=45)

    ax1.grid(True, linestyle="--", alpha=0.4)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc="upper left"
    )

    fig.tight_layout()
    fig.subplots_adjust(top=0.88)

    filename = "cftc_btc_crowding.png"

    plt.savefig(
        filename,
        dpi=300,
        bbox_inches="tight"
    )

    print(f"Successfully generated {filename}")


if __name__ == "__main__":
    build_cot_chart()
