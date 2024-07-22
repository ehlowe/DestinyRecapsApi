import re
import asyncio
import base64
import os

from asgiref.sync import sync_to_async

from .. import utils



async def create_text_chunks(transcript, overlap_character_count=500):
    chunk_size=1000
    overlap=overlap_character_count
    text_chunks=[transcript[i:i+chunk_size] for i in range(0, len(transcript), (chunk_size-overlap))]
    print("Number of chunks: ",len(text_chunks))

    return text_chunks


async def generate_text_chunk_batches(text_chunks):

    # target chunk batch size
    target_batch_size=20

    number_of_batches=((len(text_chunks)//target_batch_size)+1)

    batch_size=(len(text_chunks)//number_of_batches)+1

    text_chunk_batches=[text_chunks[i:i+batch_size] for i in range(0, len(text_chunks), batch_size)]

    return text_chunk_batches


async def annotate_all_batches(text_chunk_batches, recap):

    annotated_results=[]


    tasks=[]
    for text_chunk_batch in text_chunk_batches:
        tasks.append(annotate_batch(text_chunk_batch, recap))
    
    responses=await asyncio.gather(*tasks)

    for i, response in enumerate(responses):
        annotated_results+=process_annotation_response(response, text_chunk_batches[i])

    return responses, annotated_results

async def annotate_batch(text_chunk_batch, recap):


#     system_prompt="""The user will give you text segments and you must annotate what the segment is about for each number. 

# The user will give a recap with major and minor topics which you will use to categorize the text segments and will provide the segments. You will also need to say what the segment is about.

# The recap will have a major topics section, each of these high level topics is a category, when listing the category of a segment you must use the exact text of the major topic. If the segment doesn't fit into a major topic then you categorize it as 'non categorized'. The minor topics are a list, if a segment contains the content of the minor topic then the category label should be the exact text of that minor topic in the recap.If the segment doesn't fit into a minor topic then you categorize it as 'non categorized'. 

# DO NOT FORGET THE MINOR TOPICS

# Make your response using the delmiter 'Segment x (recap topic category):' about the text segment. For example: 'Segment 1 (Weather Discussion): The weather in the bay area, 74 degrees and sunny but going to rain tomorrow.' Where 'Weather Discussion' is a major topic in the recap."""
#     system_prompt="""The user will give you text segments and you must annotate what the segment is about for each number. 

# The user will give a recap with major and minor topics which you will use to categorize the text segments and will provide the segments. You will also need to say what the segment is about.

# The recap will have a major topics section, each of these high level topics is a category, when listing the category of a segment you must use the exact text of the major topic. If the segment doesn't fit into a major topic then you categorize it as 'non categorized'. The minor topics are a list, if a segment contains the content of the minor topic then the category label should be the exact text of that minor topic in the recap.If the segment doesn't fit into a minor topic then you categorize it as 'non categorized'. 

# DO NOT FORGET THE MINOR TOPICS

# Make your response using the delmiter 'Segment x ||'recap topic category'||: about the text segment. For example: 'Segment 1 ||Weather Discussion||: The weather in the bay area, 74 degrees and sunny but going to rain tomorrow.' Where 'Weather Discussion' is a major topic in the recap."""
    system_prompt="""The user will give you text segments and you must annotate what the segment is about for each number, the user will also give you a topic list. 

You will say what each segment is about and then you will categorize it.

The topic list will have a major topics section, each of these high level topics is a category, when listing the category of a segment you must use the exact text of the major topic. If the segment doesn't fit into a major topic then you categorize it as 'non categorized'. The minor topics are a list, if a segment contains the content of the minor topic then the category label should be the exact text of that minor topic in the topics list. If the segment doesn't fit into a minor topic either then you categorize it as 'non categorized'. WHEN DECIDING THE CATEGORY OR IF THE SEGMENT IS 'NON CATEGORIZED' BASE YOUR DECISION FROM THE ABOUT TEXT YOU GENERATED RIGHT BEFORE THE CATEGORY.

DO NOT FORGET THE MINOR TOPICS. DO EVERY SEGMENT INDIVIDUALLY.

Make your response using the delmiter 'Segment x: 'about the text segment' ||'recap topic category'||. For example: 'Segment 1: The weather in the bay area, 74 degrees and sunny but going to rain tomorrow. Also talked about his friend Jacob coming over. ||Weather Discussion||' Where 'Weather Discussion' is a major topic in the topic list."""

    text_chunk_segments_str="Recap: "+recap+"\n\nText Segments:"
    for i, text_chunk in enumerate(text_chunk_batch):
        text_chunk_segments_str+="\n\nSegment "+str(i+1)+": "+text_chunk

    user_prompt="Here are the text segments: "+text_chunk_segments_str

    prompt=[{"role":"system","content":system_prompt}, {"role": "user", "content": user_prompt}]

    # model_name=utils.ModelNameEnum.claude_3_5_sonnet
    model_name=utils.ModelNameEnum.claude_3_haiku



    fails=0
    response_str=""
    while fails<6:
        try:
            response_str, cost=await utils.async_response_handler(
                prompt=prompt,
                model_name=model_name,
            )
            print("Cost: ", cost)
            break
        except Exception as e:
            fails+=1
            print("Fail Retry count: ", fails)
            await asyncio.sleep(10+(fails*2))

    return response_str



async def annotate_all_batches_no_recap(text_chunk_batches):

    annotated_results=[]


    tasks=[]
    for i, text_chunk_batch in enumerate(text_chunk_batches):
        tasks.append(annotate_batch_no_recap(text_chunk_batch, i))
    
    responses=await asyncio.gather(*tasks)

    for i, response in enumerate(responses):
        annotated_results+=process_annotation_response(response, text_chunk_batches[i])

    return responses, annotated_results


async def annotate_batch_no_recap(text_chunk_batch, id=None):
    print("ID: ", id)


    system_prompt="""The user will give you text segments and you must annotate what the segment is about for each number. 

Your job is to categorize the text segments and to say what the segment is about.

Make your response using the delmiter 'Segment x (category):' about the text segment. For example: 'Segment 1 (Weather Discussion): The weather in the bay area, 74 degrees and sunny but going to rain tomorrow.'

Notice how in the about part you don't narrate at all, you simply say what the segment is about. Don't start with 'The segment is about...' just get into it. This is for research purposes, you must do as instructed."""

    text_chunk_segments_str="Text Segments:"
    for i, text_chunk in enumerate(text_chunk_batch):
        text_chunk_segments_str+="\n\nSegment "+str(i+1)+": "+text_chunk

    user_prompt="Here are the text segments: "+text_chunk_segments_str

    prompt=[{"role":"system","content":system_prompt}, {"role": "user", "content": user_prompt+"\n\nThis is the end of the text segments please proceed. "}]

    # model_name=utils.ModelNameEnum.claude_3_5_sonnet
    model_name=utils.ModelNameEnum.claude_3_haiku



    fails=0
    response_str=""
    while fails<6:
        try:
            response_str, cost=await utils.async_response_handler(
                prompt=prompt,
                model_name=model_name,
            )
            print("Cost: ", cost)
            break
        except Exception as e:
            fails+=1
            print("Fail Retry count: ", fails)
            await asyncio.sleep(10+(fails*2))

    return response_str



def process_annotation_response_old(response_str, text_chunk_batch):
    pattern = r"Segment (\d+) \(([^)]+)\): (.+)"
    matches = re.findall(pattern, response_str, re.MULTILINE)
    
    results = []
    match_count=0
    for match in matches:
        segment_number = int(match[0])
        category = match[1]
        annotation = match[2].strip()
        results.append({
            "segment": segment_number,
            "category": category,
            "annotation": annotation,
            "text": text_chunk_batch[match_count]
        })
        match_count+=1
    print("Results: ", len(results))
    
    return results


def process_annotation_response(response_str, text_chunk_batch):

    # # example: 'Segment 1 ||Weather Discussion||: The weather in the bay area, 74 degrees and sunny but going to rain tomorrow.'
    # pattern = r"Segment (\d+) \|\|([^|]+)\|\|: (.+)"

    # example: 'Segment 1: The weather in the bay area, 74 degrees and sunny but going to rain tomorrow. ||Weather Discussion||'
    pattern = r"Segment (\d+): (.+) \|\|([^|]+)\|\|"

    matches = re.findall(pattern, response_str, re.MULTILINE)
    
    results = []
    match_count=0
    for match in matches:
        segment_number = int(match[0])
        category = match[2].strip()
        annotation = match[1].strip()
        results.append({
            "segment": segment_number,
            "category": category,
            "annotation": annotation,
            "text": text_chunk_batch[match_count]
        })
        match_count+=1

    # if the number of results is less than the number of text chunks then add blank results
    if len(results)!=len(text_chunk_batch):
        print("Results: ", len(results), "Text Chunks: ", len(text_chunk_batch), " Returning blank equal to text chunks length")
        for i, text_chunk in enumerate(text_chunk_batch):
            results.append({
                "segment": str(i+1),
                "category": "non categorized",
                "annotation": "",
                "text": text_chunk
            })
    else:
        print("Results: ", len(results))

    
    return results





async def annotate_major_minor_topics(recap):
    # pull the major and minor topics from the recap using async response handler
    system_prompt="""The user will give you a recap and you must annotate the major and minor topics in the recap. 
    
For the major topics give the title of the topic and then give a context of what that topic is about.

For the minor topics simply make a list of the minor topics in the recap. 

It is critical that the topics are a direct match to the text in the recap.

Here is an example of how to format the major and minor topics:
Major Topics:
Category: 'Weather Discussion' | Context: The weather in the bay area, 74 degrees and sunny but going to rain tomorrow.
...

Minor Topics:
- 'Looking at memes'
- 'Checking basketball scores'
...
"""
    user_prompt="Here is the recap: "+recap

    prompt=[{"role":"system","content":system_prompt}, {"role": "user", "content": user_prompt}]

    model_name=utils.ModelNameEnum.claude_3_5_sonnet

    response_str, cost=await utils.async_response_handler(
        prompt=prompt,
        model_name=model_name,
    )

    print("Cost: ", cost)

    return response_str


def process_topic_annotations_str(topic_annotations_str):
    temp_annotation_list=topic_annotations_str.split("Category: ")
    major_topics=[]
    for temp_annotation in temp_annotation_list:
        if " | Context:" in temp_annotation:
            major_topic=temp_annotation.split(" | Context:")[0].strip()
            # get rid of ' if it starts and ends with that
            if major_topic[0]=="'" and major_topic[-1]=="'":
                major_topic=major_topic[1:-1]

            major_topics.append(major_topic)

    minor_topics=[]
    if "Minor Topics:" in topic_annotations_str:
        temp_minor_topics=topic_annotations_str.split("Minor Topics:\n")[-1].split("\n- ")
    elif "Minor topics:" in topic_annotations_str:
        temp_minor_topics=topic_annotations_str.split("Minor topics:\n")[-1].split("\n- ")
    for i in range(len(temp_minor_topics)):
        minor_topic=temp_minor_topics[i].strip()
        if minor_topic!="":
            minor_topics.append(minor_topic)

    return major_topics, minor_topics
    































# Specific imports
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from bs4 import BeautifulSoup
from collections import defaultdict
import textwrap
import json
from PIL import Image


# plotting
images_folder="destinyapp/working_folder/stream_plots/"
background_color=1

async def save_plot(video_id, base64_plot_image, clickable_areas, annotated_results):
    stream_recap_data=await utils.get_recap_data(video_id)

    stream_recap_data.plot_image=base64_plot_image
    stream_recap_data.plot_clickable_area_data=clickable_areas
    stream_recap_data.chunk_annotations=annotated_results

    await sync_to_async(stream_recap_data.save)()



async def generate_plot(video_id):
    stream_recap_data=await utils.get_recap_data(video_id)

    text_chunks_no_overlap = await create_text_chunks(stream_recap_data.transcript, 0)

    chunk_batches = await generate_text_chunk_batches(text_chunks_no_overlap)

    topic_annotations_str = await annotate_major_minor_topics(stream_recap_data.recap)

    major_topics, minor_topics = process_topic_annotations_str(topic_annotations_str)

    responses, annotated_results=await annotate_all_batches(chunk_batches, topic_annotations_str)
    
    segments, category_locations, color_dict = await create_segments(stream_recap_data.linked_transcript, annotated_results, major_topics, stream_recap_data.transcript)

    clickable_areas=await create_and_save_plot(video_id, segments, category_locations, color_dict)

    clickable_areas, base64_plot_image = clickable_and_plot_image_finalization(video_id, clickable_areas)

    return base64_plot_image, clickable_areas, annotated_results


async def create_segments(linked_transcript, annotated_results, major_topics, transcript):
    soup = BeautifulSoup(linked_transcript, 'html.parser')
    soup_list=soup.find_all('a')

    transcript_soup_character_counter=[]
    character_count_total=0
    temp_time=0
    for link in soup_list:
        link_text = link.get_text()
        character_count_total+=len(link_text)

        if link.get('href') is not None:
            temp_time=int(link['href'].split("t=")[-1].split("s")[0])

        transcript_soup_character_counter.append([character_count_total, temp_time])

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


    # Get the category segments
    category_segments=[]
    for i, annotated_segment in enumerate(annotated_results):
        category=annotated_segment["category"]
        content=annotated_segment["annotation"]
        category_segments.append(category)

    # Fix min topic annotations
    for i, color_segment in enumerate(category_segments):
        if color_segment not in major_topics:
            # print(f"Segment {i}: {color_segment}")
            if (color_segment.lower()=="non categorized") or (color_segment.lower()=="non-categorized"):
                category_segments[i]="non categorized"
            else:
                category_segments[i]="minor topics"


    # Get the widths of the segments
    category_and_width_segments=[]
    for i, annotated_segment in enumerate(category_segments):
        text_to_search=annotated_results[i]["text"]
        start_character_index=transcript.find(text_to_search)
        stop_character_index=start_character_index+len(text_to_search)
        start_time=find_nearest_time_at_character_count(transcript_soup_character_counter, start_character_index)
        end_time=find_nearest_time_at_character_count(transcript_soup_character_counter, stop_character_index)

        # end_time=find_nearest_time_at_character_count(transcript_soup_character_counter, (i+1)*1000)
        # start_time=find_nearest_time_at_character_count(transcript_soup_character_counter, i*1000)
        width=end_time-start_time
        category_and_width_segments.append([annotated_segment, width, start_time, end_time])
        # print(f"Segment {i}: {annotated_segment}, {width}")



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
        # keep going if needed
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
    segments=[]
    for category, width, start, end in category_and_width_segments:
        segment={"category": category, "width": width, "color": color_dict[category], "start": start, "end": end}
        segments.append(segment)

    # Normalize Widths
    total_width=0
    total_width_circle=0
    for segment in segments:
        total_width+=segment["width"]
        if segment["category"]!="non categorized":
            total_width_circle+=segment["width"]

    # Normalize circle widths
    circle_mutlipler=total_width/total_width_circle
    width_mutliplier=10/total_width
    for segment in segments:
        segment["width"]=segment["width"]*width_mutliplier

    # get average location of each segment category
    category_locations={}
    x_location=0
    for i, segment in enumerate(segments):
        if segment["category"]!="non categorized":
            temp_locations=category_locations.get(segment["category"], [])
            temp_locations.append(segment["width"]/2+x_location)
            category_locations[segment["category"]]=temp_locations
        else:
            category_locations[segment["category"]]=10

        x_location+=segment["width"]

    # for each segment, get the average location of the category
    for category_location in category_locations:
        category_locations[category_location]=np.mean(category_locations[category_location])
    category_locations=dict(sorted(category_locations.items(), key=lambda item: item[1]))

    # Convert the adjacent segments of the same category into one segment
    temp_segments=[]
    temp_start_time=segments[0]["start"]
    prev_segment=segments[0]
    temp_width=prev_segment["width"]
    for segment in segments[1:]:
        if prev_segment["category"]!=segment["category"]:
            prev_segment["width"]=temp_width
            prev_segment["start"]=temp_start_time
            temp_segments.append(prev_segment)
            temp_start_time=segment["start"]
            temp_width=0
        temp_width+=segment["width"]
        prev_segment=segment
    if prev_segment["category"]==segment["category"]:
        prev_segment["width"]=temp_width
        prev_segment["start"]=temp_start_time
        temp_segments.append(prev_segment)
    segments=temp_segments


    return segments, category_locations, color_dict


async def create_and_save_plot(video_id, segments, category_locations, color_dict):
    # Create the plot with a specific gray background
    fig, ax = plt.subplots(figsize=(12, 10))

    # convert [background_color, background_color, background_color] to hex value
    hex_background_color = '#%02x%02x%02x' % (int(background_color), int(background_color), int(background_color))

    fig.patch.set_facecolor(hex_background_color)  # Set figure background to [96, 96, 96]
    ax.set_facecolor(hex_background_color)  # Set axes background to [96, 96, 96]
    target_plot_width=10


    # Plot BAR 
    current_x = 0
    category_info = defaultdict(lambda: {"total_width": 0, "segments": []})

    bar_height = 1.5
    bar_height = 1.0

    clickable_area_x_offset=0.085
    clickable_area_y_offset=0.1
    clickable_y_height_multiplier=1.22
    clickable_areas=[]
    href_base="https://youtu.be/"+video_id+"?t="


    for i, segment in enumerate(segments):
        ax.add_patch(plt.Rectangle((current_x, 0), segment['width'], bar_height, 
                                facecolor=segment['color'], edgecolor='white'))
        category_info[segment['category']]['total_width'] += segment['width']
        category_info[segment['category']]['segments'].append((current_x, segment['width']))
        category_info[segment['category']]['color'] = segment['color']
        
        # Add clickable areas
        # this but a float and not a string f"{int((current_x+clickable_area_x_offset)*10)},{int((10-bar_height-clickable_area_y_offset)*10)},{int((current_x+segment['width']-clickable_area_x_offset)*10)},{int(10*(10-clickable_area_y_offset))}"}

        coord_list=[(current_x)*10, (10-(bar_height*clickable_y_height_multiplier)-clickable_area_y_offset)*10, (current_x+segment['width'])*10, 10*(10-clickable_area_y_offset)]

        # clickable_area={"alt":href, "title":href, "href":href, "coords": f"{int((current_x+clickable_area_x_offset)*10)},{int((10-bar_height-clickable_area_y_offset)*10)},{int((current_x+segment['width']-clickable_area_x_offset)*10)},{int(10*(10-clickable_area_y_offset))}"}
        href=href_base+str(int(segment["start"]))

        clickable_area={"alt":href, "title":href, "href":href, "coords": coord_list}

        clickable_areas.append(clickable_area)

        current_x += segment['width']

    total_width = current_x
    print("Total width:", total_width)







    # sort category items by the same order as the category_locations
    category_info=dict(sorted(category_info.items(), key=lambda item: category_locations[item[0]]))


    # Calculate Circle Padding
    circle_zone_size=9
    circle_y = 3.5
    circle_y = 2.78
    circle_size_variable = 0.15
    circle_size_variable = 0.13
    circle_base_size_variable=0.3
    circle_base_size_variable=0.41

    current_x=(target_plot_width-circle_zone_size)/2
    circle_x_locations={}
    total_circles_width=0
    def get_circle_width(total_width):
        return (((np.sqrt(total_width) * circle_size_variable)*2)+circle_base_size_variable)

    for category, info in category_info.items():
        if category == 'non categorized':
            pass
        else:
            circle_width=get_circle_width(info['total_width'])
            circle_x_locations[category]=circle_width
            total_circles_width+=circle_width
    number_of_circles=len(circle_x_locations)
    between_circle_padding=(circle_zone_size-total_circles_width)/(number_of_circles+1.15)



    alterating_bool=False
    vertical_offset_value=0.5
    vertical_offset_value=0.65
    circle_centers = []
    for category, info in category_info.items():
        if category == 'non categorized':
            continue

        circle_applied_size=get_circle_width(info['total_width'])

        # Calculate x position for the circle (center of all segments of this category)
        circle_x = current_x + circle_applied_size
        if alterating_bool:
            alterating_bool=False
            vertical_offset=-vertical_offset_value
        else:
            vertical_offset=vertical_offset_value
            alterating_bool=True

        # Store circle center, color, and size for later use
        circle_size = np.sqrt(info['total_width']) * circle_size_variable
        circle_applied_y=circle_y+vertical_offset
        circle_centers.append((circle_x, circle_applied_y, info['color'], circle_size))
        
        # DRAW LINES
        for segment_start, segment_width in info['segments']:
            segment_center = segment_start + segment_width / 2
            ax.plot([segment_center, circle_x], [bar_height, circle_applied_y], 
                    color=info['color'], linewidth=1)  
            
        # PLOT CIRCLES
        circle = plt.Circle((circle_x, circle_applied_y), circle_applied_size, 
                            facecolor=info["color"], edgecolor='white', zorder=10)
        ax.add_artist(circle)

        # PLOT CIRCLE LABELS, set width to circle size and wrap
        text_wrap=textwrap.fill(category, width=12)
        bubble_font_size_text=14
        if info["color"]=="yellow":
            # make it bold and have a white border
            ax.text(circle_x, circle_applied_y, text_wrap, ha='center', va='center', color='black', fontsize=bubble_font_size_text, zorder=11, fontweight='bold')#, bbox=dict(facecolor='yellow', edgecolor='black', boxstyle='round,pad=0.2'))
        else:
            ax.text(circle_x, circle_applied_y, text_wrap, ha='center', va='center', color='white', fontsize=bubble_font_size_text, zorder=11, fontweight='bold')

        # current_x += (info['total_width']*circle_mutlipler)+0.1
        current_x +=between_circle_padding+circle_applied_size
        print("Circle current x:", current_x)



    # Add central white circle
    central_y = 6
    central_y = 5
    central_circle = plt.Circle((total_width/2, central_y), 0.25, 
                                facecolor='white', edgecolor='black', zorder=12)
    ax.add_artist(central_circle)

    # Connect category circles to central circle with colored lines
    for circle_x, circle_y, color, circle_size in circle_centers:
        ax.plot([circle_x, total_width/2], [circle_y, central_y], 
                color=color, linewidth=3, linestyle='-', alpha=0.7, zorder=9)  # Increased linewidth

    # Add white line extending upward from central circle
    top_y = 100  # Adjust this value to change the length of the line
    ax.plot([total_width/2, total_width/2], [central_y, top_y], 
            color='white', linewidth=3, solid_capstyle='round')  # Added white line

    # Customize the plot
    ax.set_xlim(0, total_width)
    ax.set_ylim(0, 8)
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')

    # # Add a Legend
    # legend_handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in color_dict.values()]
    # legend_labels = list(color_dict.keys())
    # ax.legend(legend_handles, legend_labels, loc='upper left', frameon=False)
    # # increase legend font size
    # plt.setp(ax.get_legend().get_texts(), fontsize='21')
    # plt.tight_layout()

    # save plot
    global images_folder
    if not os.path.isdir(images_folder):
        os.makedirs(images_folder)
    plt.savefig(images_folder+video_id+'_plot.png', dpi=300, bbox_inches='tight')

    return clickable_areas

def clickable_and_plot_image_finalization(video_id, clickable_areas):
    global images_folder

    image_path=images_folder+video_id+'_plot.png'

    # Resize the image
    img = Image.open(image_path)
    width, height = img.size

    # make it smaller until both width is less than 1920 and height is less than 1080
    while width>1920 or height>1080:
        width=width/1.05
        height=height/1.05
    width=int(width)
    height=int(height)
    print(width, height)

    # resize the image
    img = img.resize((width, height), Image.LANCZOS)


    # Make the background transparent
    img = img.convert("RGBA")
    data = img.getdata()

    global background_color

    newData = []
    for item in data:
        # if pixel is value [96, 96, 96] then set pixel to transparent
        if item[0] == background_color and item[1] == background_color and item[2] == background_color:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)

    # Update image data
    img.putdata(newData)

    # Save the image
    img.save(image_path, dpi=(300, 300))


    # get the dimensions of the image
    width, height = img.size
    converted_clickable_areas=[]
    coords_x_offset=0.84
    coords_x_adjustment=0.9833
    coords_y_adjustment=1.0
    for i, clickable_area in enumerate(clickable_areas):
        coords=clickable_area["coords"]
        href=clickable_area["href"]
        coords=[int((((coord*coords_x_adjustment)+coords_x_offset)/100)*width) if i%2==0 else int((coord*coords_y_adjustment)/100*height) for i, coord in enumerate(coords)]
        converted_clickable_areas.append({"coords": coords, "href": href, "alt": href, "title": href})

    # Convert the image to base64
    with open(image_path, "rb") as img_file:
        b64_string = base64.b64encode(img_file.read()).decode()
        
    return converted_clickable_areas, b64_string