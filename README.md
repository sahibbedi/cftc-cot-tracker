# cftc-cot-tracker
An automated tracker that visualizes the "crowding premium" in the Bitcoin cash-and-carry trade. By overlaying the weekly annualized basis with public CFTC hedge fund positioning data, this tool provides a clear, data-driven look at exactly how crowded the trade is becoming.

This repository uses a serverless Python script to pull public data from the CFTC API and Yahoo Finance. It calculates the net short positioning of Leveraged Funds, overlays it with the annualized BTC futures basis, and generates a static chart (cftc_btc_crowding.png).

<img width="1226" height="594" alt="Screenshot 2026-05-27 at 5 53 45 PM" src="https://github.com/user-attachments/assets/d471d4f0-daa0-4613-bbdc-9f0160e8557e" />


# How to Read the Chart #
This dual-axis chart visualizes the relationship between the basis yield and institutional positioning over the past twelve months. The red bars correspond to the left axis, tracking the net short contract positioning of leveraged funds, where deeper negative values indicate heavier institutional short exposure. The dark blue line maps to the right axis, tracking the rolling annualized basis yield percentage to show the reward currently available for executing the cash-and-carry trade.

# What Value This Creates
Institutional clients could constantly ask about the health of the basis yield and whether the trade is becoming "too crowded." This tracker can simply provide an instant, data-backed answer:
* **Quantifies Institutional Sentiment:** By mapping the net short positioning of leveraged funds against the basis yield, it visually demonstrates how heavily institutions are leaning into the trade.
* **Contextualizes Risk vs. Reward:** It tells the team whether the current market is highly crowded (deep negative positioning) or normalizing over a 12-month window.
* **Drives the Conversation:** It serves as an authoritative, objective reference point for talking with institutional clients about yield health.

# How to Run the Tracker (3 Options) #
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

Feel free to email sahibsbedi26@gmail.com if you run into issues.
