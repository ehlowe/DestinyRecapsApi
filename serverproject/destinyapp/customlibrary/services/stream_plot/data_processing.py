
import numpy as np
from bs4 import BeautifulSoup



def find_nearest_time_at_character_count(transcript_soup_character_counter, character_count):
    # middle sort the list to get to the closest character count quickly
    l=0
    r=len(transcript_soup_character_counter)-1

    while l<r:
        m=(l+r)//2
        if transcript_soup_character_counter[m][0]<character_count:
            l=m+1
        else:
            r=m

    if l==0:
        return transcript_soup_character_counter[l][1]
    else:
        if abs(transcript_soup_character_counter[l][0]-character_count)<abs(transcript_soup_character_counter[l-1][0]-character_count):
            return transcript_soup_character_counter[l][1]
        else:
            return transcript_soup_character_counter[l-1][1]
        


def create_topic_color_dict(major_topics):
    # Create the segments
    color_dict={
        "minor topics": "yellow",
        "non categorized": "black"
    }
    major_topic_color_list=[
        "green",
        "blue",
        "purple",
        "orange",
        "red",
        "pink",
        "brown",
        "cyan",
        "gold",
        "gray",
        "lime",
        "magenta",
        "olive",
    ]
    for i, mt in enumerate(major_topics):
        color_dict[mt]=major_topic_color_list[i]

    return color_dict


async def create_segments(linked_transcript, annotated_results, major_topics, transcript):
    soup = BeautifulSoup(linked_transcript, 'html.parser')
    soup_list=soup.find_all('a')

    # Setup list for getting the time at each character count
    transcript_soup_character_counter=[]
    character_count_total=0
    temp_time=0
    for link in soup_list:
        link_text = link.get_text()
        character_count_total+=len(link_text)

        if link.get('href') is not None:
            temp_time=int(link['href'].split("t=")[-1].split("s")[0])

        transcript_soup_character_counter.append([character_count_total, temp_time])

    # Setup color dictionary to annotate color
    color_dict=create_topic_color_dict(major_topics)

    # Get the category segments
    total_bar_width=0
    total_categorized_width=0
    for i in range(len(annotated_results)):
        # Fix the category Labels
        if annotated_results[i]["category"] not in major_topics:
            if (annotated_results[i]["category"].lower()=="non categorized") or (annotated_results[i]["category"].lower()=="non-categorized"):
                annotated_results[i]["category"]="non categorized"
            else:
                annotated_results[i]["category"]="minor topics"

        # Compute the positional components
        text_to_search=annotated_results[i]["text"]
        start_character_index=transcript.find(text_to_search)
        stop_character_index=start_character_index+len(text_to_search)
        start_time=find_nearest_time_at_character_count(transcript_soup_character_counter, start_character_index)
        end_time=find_nearest_time_at_character_count(transcript_soup_character_counter, stop_character_index)
        width=end_time-start_time

        # Add the positional components to the annotated results
        annotated_results[i]["start_time"]=start_time
        annotated_results[i]["end_time"]=end_time
        annotated_results[i]["width"]=width

        # Add the color to the annotated results
        annotated_results[i]["color"]=color_dict[annotated_results[i]["category"]]

        # Add the width to the total bar width
        total_bar_width+=width
        if annotated_results[i]["category"]!="non categorized":
            total_categorized_width+=width

    # get average location of each segment category
    category_locations={}
    x_location=0
    for i in range(len(annotated_results)):
        if annotated_results[i]["category"]!="non categorized":
            temp_locations=category_locations.get(annotated_results[i]["category"], [])
            temp_locations.append((annotated_results[i]["width"]/2+x_location)*annotated_results[i]["width"])
            category_locations[annotated_results[i]["category"]]=temp_locations
        else:
            category_locations[annotated_results[i]["category"]]=1
        x_location+=annotated_results[i]["width"]

    # for each segment, get the average location of the category
    for category_location in category_locations:
        category_locations[category_location]=np.mean(category_locations[category_location])

    # sort the category locations
    category_locations=dict(sorted(category_locations.items(), key=lambda item: item[1]))

    return annotated_results, category_locations


async def annotated_to_plot_segments(annotated_results):

    def unpack_annotated_result(annotated_result, text_list=None, annotation_list=None):
        temp_dict={
            "category": annotated_result["category"],
            "color": annotated_result["color"],

            "start_time": annotated_result["start_time"],
            "end_time": annotated_result["end_time"],
            "width": annotated_result["width"],
        }

        if text_list and annotation_list:
            temp_dict["texts"]=text_list
            temp_dict["annotations"]=annotation_list

        return temp_dict


    # Setup the plot segments
    plot_segments=[]
    temp_text_list=[annotated_results[0]["text"]]
    temp_annotation_list=[annotated_results[0]["annotation"]]
    temp_width=annotated_results[0]["width"]
    temp_start=annotated_results[0]["start_time"]

    for i in range(1, len(annotated_results)):
        # if last is the same as current, append to temp data
        if annotated_results[i]["category"]==annotated_results[i-1]["category"]:
            temp_text_list.append(annotated_results[i]["text"])
            temp_annotation_list.append(annotated_results[i]["annotation"])
            temp_width+=annotated_results[i]["width"]

        # if the category is different, append the last result with temp data
        else:
            temp_segment=unpack_annotated_result(annotated_results[i-1], temp_text_list, temp_annotation_list)
            temp_segment["width"]=temp_width
            temp_segment["start_time"]=temp_start
            plot_segments.append(temp_segment)


            # reset for next segment
            temp_start=annotated_results[i]["start_time"]
            temp_width=annotated_results[i]["width"]
            temp_text_list=[annotated_results[i]["text"]]
            temp_annotation_list=[annotated_results[i]["annotation"]]
    
    # append the last segment
    if annotated_results[-1]["category"]==annotated_results[-2]["category"]:
        temp_segment=unpack_annotated_result(annotated_results[-1], temp_text_list, temp_annotation_list)
        temp_segment["width"]=temp_width
        temp_segment["start_time"]=temp_start
        plot_segments.append(temp_segment)

    return plot_segments

















# Pack into a class
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Segment:
    category: str
    color: str

    start_time: float
    end_time: float
    width: float

    x: float

    texts: List[str]
    annotations: List[str]

    href: str

    recap: str=""

@dataclass
class Abstraction:
    width: float
    color: str
    
    x: float
    y: float
    size: float

    recap: str=""

@dataclass
class TimeNormalization:
    start_offset: float
    net_duration: float

@dataclass
class PlotParameters:
    background_color: int
    plotting_width: int
    plotting_height: int

    bar_height_setting: float

    upper_y: float
    lower_y: float
    circle_size_multiplier: float
    circle_size_offset: float
    abstraction_width_cutoff: float

    central_y: float

    bar_height_setting: float

    video_id: str


@dataclass
class PlotObject:
    segments: List[Segment] = field(default_factory=list)
    abstractions: Dict[str, Abstraction] = field(default_factory=dict)
    time_normalization: Optional[TimeNormalization] = field(default=None)
    plot_parameters: Optional[PlotParameters] = field(default=None)



async def create_plot_object(plot_segments, category_locations, video_id):
    # # Set up the plot object parameters
    # Overall plot
    background_color=96
    plotting_width=10
    plotting_height=10

    # Bar 
    bar_height_setting=0.15

    # Abstraction Position
    # upper_y=0.45
    # lower_y=0.3
    upper_y=.55
    lower_y=0.70
    circle_size_multiplier=0.1
    circle_size_offset=0.08
    abstraction_width_cutoff=0.05

    # Meta 
    central_y = 0.7

    # Load data into plot object
    plot_object=PlotObject()

    # push the plot parameters
    plot_object.plot_parameters=PlotParameters(
        background_color=background_color,
        plotting_width=plotting_width,
        plotting_height=plotting_height,
        bar_height_setting=bar_height_setting,
        upper_y=upper_y,
        lower_y=lower_y,
        circle_size_multiplier=circle_size_multiplier,
        circle_size_offset=circle_size_offset,
        abstraction_width_cutoff=abstraction_width_cutoff,
        central_y=central_y,
        video_id=video_id
    )

    # Define Segments
    total_bar_width=0
    total_abstraction_width=0
    plot_object.segments=[]
    for segment in plot_segments:
        segment["x"]=None
        segment["href"]="https://youtu.be/"+video_id+"?t="+str(int(segment["start_time"])//1000)
        seg_obj=Segment(**segment)
        plot_object.segments.append(seg_obj)
        total_bar_width+=segment["width"]
        if segment["category"]!="non categorized":
            total_abstraction_width+=segment["width"]

    # Define time_normalization
    plot_object.time_normalization=TimeNormalization(net_duration=plot_object.segments[-1].end_time-plot_object.segments[0].start_time, start_offset=plot_object.segments[0].start_time)

    # Define Abstractions
    for i in range(len(plot_object.segments)):
        abstraction=plot_object.abstractions.get(plot_object.segments[i].category, None)
        if abstraction:
            plot_object.abstractions[plot_object.segments[i].category].width+=(plot_object.segments[i].width/plot_object.time_normalization.net_duration)
        else:
            plot_object.abstractions[plot_object.segments[i].category]=Abstraction(width=plot_object.segments[i].width/plot_object.time_normalization.net_duration, color=plot_object.segments[i].color, x=None, y=None, size=None)
        plot_object.segments[i].width=plot_object.segments[i].width/plot_object.time_normalization.net_duration
        plot_object.segments[i].x=(((plot_object.segments[i].start_time+plot_object.segments[i].end_time)/2)-plot_object.time_normalization.start_offset)/plot_object.time_normalization.net_duration
        # plot_object.segments[i].x=(plot_object.segments[i].x-plot_object.time_normalization.start_offset)/plot_object.time_normalization.net_duration




    # Define circle size
    def get_circle_size(total_width):
        return (((np.sqrt(total_width) * circle_size_multiplier)*2)+circle_size_offset)

    # # Get the width of all circles
    # total_abstraction_width=0
    # for category in range(len(list(plot_object.abstractions.keys()))):
    #     total_abstraction_width+=plot_object.abstractions[category].width
    total_abstraction_size=0
    for category, abstraction in plot_object.abstractions.items():
        if category=="non categorized":
            continue
        plot_object.abstractions[category].size=get_circle_size(abstraction.width)
        total_abstraction_size+=plot_object.abstractions[category].size

    # define abstraction x
    number_of_abstractions=len(plot_object.abstractions.values())
    circle_zone_size=1-(abstraction_width_cutoff*2)
    between_circle_padding=(circle_zone_size-total_abstraction_size)/(number_of_abstractions-2)

    last_x=abstraction_width_cutoff-between_circle_padding

    for i, category in enumerate(list(category_locations.keys())):
        if category=="non categorized":
            continue
        plot_object.abstractions[category].x=last_x+(plot_object.abstractions[category].size/2)+between_circle_padding

        last_x=plot_object.abstractions[category].x+(plot_object.abstractions[category].size/2)
        if i%2==0:
            plot_object.abstractions[category].y=upper_y
        else:
            plot_object.abstractions[category].y=lower_y
        
    return plot_object
