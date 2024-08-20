from matplotlib import pyplot as plt
import numpy as np
import textwrap
from collections import defaultdict

from .data_processing import PlotObject

# import display from IPython
from IPython.display import display

async def generate_plot(plot_object: PlotObject):
    
    # Create the plot with a specific gray background
    fig, ax = plt.subplots(figsize=(plot_object.plot_parameters.plotting_width, plot_object.plot_parameters.plotting_height))
    hex_background_color = '#%02x%02x%02x' % (int(plot_object.plot_parameters.background_color), int(plot_object.plot_parameters.background_color), int(plot_object.plot_parameters.background_color))
    fig.patch.set_facecolor(hex_background_color)  # Set figure background to [96, 96, 96]
    ax.set_facecolor(hex_background_color)  # Set axes background to [96, 96, 96]
    target_plot_width=10
    plt.close(fig)

    # Plot BAR 
    current_x = 0
    category_info = defaultdict(lambda: {"total_width": 0, "segments": []})

    bar_height = plot_object.plot_parameters.bar_height_setting*plot_object.plot_parameters.plotting_height

    clickable_area_x_offset=0.085
    clickable_area_y_offset=0.1
    clickable_y_height_multiplier=1.22
    clickable_areas=[]
    # href_base="https://youtu.be/"+video_id+"?t="

    for i, segment in enumerate(plot_object.segments):
        ax.add_patch(plt.Rectangle((((segment.x-(segment.width/2))*plot_object.plot_parameters.plotting_width), 0), segment.width*plot_object.plot_parameters.plotting_width, bar_height, 
                                facecolor=segment.color, edgecolor='white'))
        current_x += segment.width
    total_width = current_x


    # Calculate Circle Padding
    circle_zone_size=9
    circle_y = 3.5
    circle_y = 2.78
    circle_size_variable = 0.15
    circle_size_variable = 0.13
    circle_base_size_variable=0.3
    circle_base_size_variable=0.41

    # current_x=
    circle_x_locations={}
    total_circles_width=0
    def get_circle_width(total_width):
        return (((np.sqrt(total_width) * circle_size_variable)*2)+circle_base_size_variable)

    alterating_bool=False
    vertical_offset_value=0.5
    vertical_offset_value=0.65

    # Add central white circle
    central_circle = plt.Circle((plot_object.plot_parameters.plotting_width/2, plot_object.plot_parameters.central_y*plot_object.plot_parameters.plotting_height), 0.25, facecolor='white', edgecolor='black', zorder=12)
    ax.add_artist(central_circle)


    for category, abstraction in plot_object.abstractions.items():
        print(category, abstraction.width)

        if category == 'non categorized':
            continue

        # Calculate x position for the circle (center of all segments of this category)
        if alterating_bool:
            alterating_bool=False
            vertical_offset=-vertical_offset_value
        else:
            vertical_offset=vertical_offset_value
            alterating_bool=True

        # PLOT CIRCLES
        circle = plt.Circle((abstraction.x*plot_object.plot_parameters.plotting_width, abstraction.y*plot_object.plot_parameters.plotting_width), (abstraction.size/2)*plot_object.plot_parameters.plotting_width, facecolor=abstraction.color, edgecolor='white', zorder=10)
        ax.add_artist(circle)

        # PLOT CIRCLE LABELS, set width to circle size and wrap
        text_wrap=textwrap.fill(category, width=12)
        bubble_font_size_text=14
        if abstraction.color=="yellow":
            ax.text(abstraction.x*plot_object.plot_parameters.plotting_width, abstraction.y*plot_object.plot_parameters.plotting_height, text_wrap, ha='center', va='center', color='black', fontsize=bubble_font_size_text, zorder=11, fontweight='bold')
        else:
            ax.text(abstraction.x*plot_object.plot_parameters.plotting_width, abstraction.y*plot_object.plot_parameters.plotting_height, text_wrap, ha='center', va='center', color='white', fontsize=bubble_font_size_text, zorder=11, fontweight='bold')

        # Make lines to center circle
        ax.plot([abstraction.x*plot_object.plot_parameters.plotting_width, plot_object.plot_parameters.plotting_width/2], [abstraction.y*plot_object.plot_parameters.plotting_height, plot_object.plot_parameters.central_y*plot_object.plot_parameters.plotting_height], color=abstraction.color, linewidth=3, linestyle='-', alpha=0.7, zorder=9) 

    # make lines to the circles
    for segment in plot_object.segments:
        abstraction=plot_object.abstractions[segment.category]
        if segment.x and abstraction.y:
            ax.plot([segment.x*plot_object.plot_parameters.plotting_width, abstraction.x*plot_object.plot_parameters.plotting_width], [bar_height, abstraction.y*10], color=segment.color, linewidth=1)  


    # Add white line extending upward from central circle
    top_y = 100  # Adjust this value to change the length of the line
    ax.plot([plot_object.plot_parameters.plotting_width/2, plot_object.plot_parameters.plotting_width/2], [plot_object.plot_parameters.central_y*plot_object.plot_parameters.plotting_height, plot_object.plot_parameters.plotting_height], color='white', linewidth=3, solid_capstyle='round')  # Added white line

    # Customize the plot
    ax.set_xlim(0, total_width*plot_object.plot_parameters.plotting_width)
    ax.set_ylim(0, 8)
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')
    display(fig)
