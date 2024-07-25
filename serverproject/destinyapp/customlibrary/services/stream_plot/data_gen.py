import asyncio
import re

from destinyapp.customlibrary import utils
from destinyapp.models import StreamRecapData


# Process the transcript into batches of text chunks
async def create_text_chunks(transcript, overlap_character_count=500):
    chunk_size=1000
    overlap=overlap_character_count
    text_chunks=[transcript[i:i+chunk_size] for i in range(0, len(transcript), (chunk_size-overlap))]

    return text_chunks

async def generate_text_chunk_batches(text_chunks):
    target_batch_size=20
    number_of_batches=((len(text_chunks)//target_batch_size)+1)
    batch_size=(len(text_chunks)//number_of_batches)+1
    text_chunk_batches=[text_chunks[i:i+batch_size] for i in range(0, len(text_chunks), batch_size)]

    return text_chunk_batches


















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





















# Annotate the text chunks
async def annotate_batch(text_chunk_batch, recap):
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

def process_annotation_response(response_str, text_chunk_batch):
    pattern = r"Segment (\d+): (.+) \|\|([^|]+)\|\|"
    matches = re.findall(pattern, response_str, re.MULTILINE)
    results = []

    # Get the matches and add them to the results
    try:
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
    except Exception as e:
        print("Error in process_annotation_response, continuing with blank results: ", e)

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



# Run annotation on all batches
async def annotate_all_batches(text_chunk_batches, recap):

    annotated_results=[]

    tasks=[]
    for text_chunk_batch in text_chunk_batches:
        tasks.append(annotate_batch(text_chunk_batch, recap))
    
    responses=await asyncio.gather(*tasks)

    for i, response in enumerate(responses):
        annotated_results+=process_annotation_response(response, text_chunk_batches[i])

    return responses, annotated_results
