# cftc-cot-tracker
An automated tracker that visualizes the "crowding premium" in the Bitcoin cash-and-carry trade. By overlaying the weekly annualized basis with public CFTC hedge fund positioning data, this tool provides a clear, data-driven look at exactly how crowded the trade is becoming.

This repository uses a serverless Python script to pull public data from the CFTC API and Yahoo Finance. It calculates the net short positioning of Leveraged Funds, overlays it with the annualized BTC futures basis, and generates a static chart (cftc_btc_crowding.png).

How to Run the Tracker (3 Options)
1. Fully Automated (GitHub Actions)
The primary engine for this repository is a GitHub Action that runs completely hands-off.

Scheduled Run: The bot automatically wakes up every Friday at 4:30 PM ET, pulls the fresh CFTC data, updates the chart, and commits the new image directly to this repository.

Manual Trigger: If you want to force an update immediately:

Click the Actions tab at the top of this repository.

Click Weekly CFTC Chart Update on the left sidebar.

Click the Run workflow dropdown on the right, and hit the green Run workflow button.

Wait ~60 seconds for the bot to generate and save the new chart.

2. The Backup Environment (Google Colab)
If GitHub Actions is ever rate-limited by Yahoo Finance, or if you want to experiment with the code and see the chart render interactively, you can use the included Jupyter Notebook backup.

Navigate to the WeeklyCFTCChartUpdate.ipynb file in this repository.

You can open this directly in Google Colab by navigating to colab.research.google.com, clicking File > Open Notebook, selecting the GitHub tab, and pasting your repository URL.

Run the cells sequentially to install dependencies and view the chart directly in your browser.

3. Local Execution
If you prefer to run the script on your own machine:

Clone the repository.

Install the lightweight dependencies:

Bash
pip install -r requirements.txt
Execute the script:

Bash
python tracker.py
The updated cftc_btc_crowding.png file will be saved directly to your local folder.
