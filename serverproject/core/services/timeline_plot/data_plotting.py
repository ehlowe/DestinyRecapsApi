
from matplotlib import pyplot as plt
import numpy as np
import textwrap
from collections import defaultdict
import pandas as pd
from datetime import datetime
import seaborn as sns

# import display from IPython
from IPython.display import display



def generate_plot(data):
    # Convert dates to datetime objects and create a set of all unique dates
    all_dates = set()
    for dates in data.values():
        all_dates.update([datetime.strptime(date.strip(), '%m/%d/%Y') for date in dates])

    # Sort the dates
    all_dates = sorted(all_dates)

    # Create a DataFrame with dates as index and topics as columns
    df = pd.DataFrame(index=all_dates, columns=data.keys(), data=0)

    # Fill the DataFrame
    for topic, dates in data.items():
        for date in dates:
            df.loc[datetime.strptime(date.strip(), '%m/%d/%Y'), topic] = 1

    # Sort the DataFrame by date
    df = df.sort_index()

    # Create a color palette
    n_colors = len(df.columns)
    color_palette = sns.color_palette("husl", n_colors)

    # Create a dictionary mapping topics to colors
    color_dict = dict(zip(df.columns, color_palette))

    # Plotting
    fig, ax = plt.subplots(figsize=(15, 10))

    # Create the stacked bar chart with consistent colors
    df.plot(kind='bar', stacked=True, ax=ax, color=[color_dict[col] for col in df.columns])

    # Customize the plot
    plt.title('Topics Over Time', fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Topics', fontsize=12)
    plt.legend(title='Topics', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')

    # Adjust the layout to prevent cut-off
    plt.tight_layout()

    # Show the plot
    plt.show()