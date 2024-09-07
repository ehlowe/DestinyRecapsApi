

import asyncio
import re

from core import utils
from destinyapp.models import StreamRecapData








async def create_topics(transcript, model_name=utils.ModelNameEnum.gpt_4o_mini):
    # Make Topics
    topic_sys_prompt="""You will be given an entire transcript and your job is to come up with the categories discussed during the transcript.

Step 1: You will start by listing as many topic categories as you can in chronological order from the transcript. This may be 20 or so.

Step 2: Boil down the categories to the top 8-12 categories.

Step 3: Boil down to the top categories for which to make a content graph (no more than 6).


When formatting these steps, please use the following format:

Step 1:
1. Topic 1
2. Topic 2
...
20. Topic 20

Step 2:
1. Topic 1
2. Topic 2
...

Step 3:
1. Topic 1
2. Topic 2
...

The goal is to get the categories that describe the bulk of the content so that it can be segmented by the categories. The topics in the final step, step3, should have little overlap so that the segments are distinct.

"""
    user_prompt="Here is the transcript: "+transcript

    full_topic_gen_prompt=[{"role":"system", "content":topic_sys_prompt}, {"role":"user", "content":user_prompt}]
    topics_response, temp_cost = await utils.async_response_handler(full_topic_gen_prompt, model_name)

    topics_str=topics_response.split("Step 3:")[-1]
    major_topics_raw=topics_str.split("\n")

    major_topics=[]
    for t in major_topics_raw:
        # check if t starts with a number if not remove it
        t=t.strip()
        if (t=="") or not t[0].isdigit():
            continue
        else:
            # remove the number
            major_topics.append(t[2:].strip())

    return topics_str, major_topics, temp_cost







# Annotate the text chunks
async def annotate_batch(text_chunk_batch, recap, model_name=utils.ModelNameEnum.gpt_4o_mini):
    system_prompt="""The user will give you text segments and you must annotate what the segment is about for each number, the user will also give you a topic list. 

You will say what each segment is about and then you will categorize it.

The topic list will have a major topics section, each of these high level topics is a category, when listing the category of a segment you must use the exact text of the major topic. If the segment doesn't fit into a major topic then you categorize it as 'non categorized'. The minor topics are a list, if a segment contains the content of the minor topic then the category label should be the exact text of that minor topic in the topics list. If the segment doesn't fit into a minor topic either then you categorize it as 'non categorized'. WHEN DECIDING THE CATEGORY OR IF THE SEGMENT IS 'NON CATEGORIZED' BASE YOUR DECISION FROM THE ABOUT TEXT YOU GENERATED RIGHT BEFORE THE CATEGORY.

DO NOT FORGET THE MINOR TOPICS. DO EVERY SEGMENT INDIVIDUALLY.

Make your response using the delmiter 'Segment x: 'about the text segment' ||'recap topic category'||. For example: 'Segment 1: The weather in the bay area, 74 degrees and sunny but going to rain tomorrow. Also talked about his friend Jacob coming over. ||Weather Discussion||' Where 'Weather Discussion' is a major topic in the topic list. The about should always be sentences and never lists."""

    text_chunk_segments_str="Recap: "+recap+"\n\nText Segments:"
    for i, text_chunk in enumerate(text_chunk_batch):
        text_chunk_segments_str+="\n\nSegment "+str(i+1)+": "+text_chunk

    user_prompt="Here are the text segments: "+text_chunk_segments_str

    prompt=[{"role":"system","content":system_prompt}, {"role": "user", "content": user_prompt}]


    # model_name=utils.ModelNameEnum.llama_3_1_8B_instant
    # model_name=utils.ModelNameEnum.llama_3_1_70B_versatile

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

    return response_str, cost

def process_annotation_response(response_str, text_chunk_batch):
    # pattern = r"Segment (\d+): (.+) \|\|([^|]+)\|\|"
    pattern = r"Segment (\d+): ([\s\S]+?)\s*\|\|\s*([\s\S]+?)\s*\|\|"
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
    
    responses_and_costs=await asyncio.gather(*tasks)
    
    cost=0
    responses=[]
    for i, (response, temp_cost) in enumerate(responses_and_costs):
        cost+=temp_cost
        annotated_results+=process_annotation_response(response, text_chunk_batches[i])
        responses.append(response)

    return responses, annotated_results, cost























# Annotate the text chunks
async def annotate_batch_no_recap(text_chunk_batch,  model_name=utils.ModelNameEnum.gpt_4o_mini):
    system_prompt="""The user will give you text segments and you must annotate what the segment is about for each number, the user will also give you a topic list. 

You will say what each segment is about and then you will categorize it.

The topic list will have a major topics section, each of these high level topics is a category, when listing the category of a segment you must use the exact text of the major topic. If the segment doesn't fit into a major topic then you categorize it as 'non categorized'. The minor topics are a list, if a segment contains the content of the minor topic then the category label should be the exact text of that minor topic in the topics list. If the segment doesn't fit into a minor topic either then you categorize it as 'non categorized'. WHEN DECIDING THE CATEGORY OR IF THE SEGMENT IS 'NON CATEGORIZED' BASE YOUR DECISION FROM THE ABOUT TEXT YOU GENERATED RIGHT BEFORE THE CATEGORY.

DO NOT FORGET THE MINOR TOPICS. DO EVERY SEGMENT INDIVIDUALLY.

Make your response using the delmiter 'Segment x: 'about the text segment' ||'recap topic category'||. For example: 'Segment 1: The weather in the bay area, 74 degrees and sunny but going to rain tomorrow. Also talked about his friend Jacob coming over. ||Weather Discussion||' Where 'Weather Discussion' is a major topic in the topic list."""

    system_prompt="""The user will give you text segments and you must annotate what the segment is about for each number. 

Your job is to categorize the text segments and to say what the segment is about.

Make your response using the delmiter 'Segment x (category):' about the text segment. For example: 'Segment 1 (Weather Discussion): The weather in the bay area, 74 degrees and sunny but going to rain tomorrow.'

Notice how in the about part you don't narrate at all, you simply say what the segment is about. Don't start with 'The segment is about...' just get into it. This is for research purposes, you must do as instructed."""

    system_prompt="""The user will give you text segments and you must annotate what the segment is about for each number. 

Your job is to categorize the text segments and to say what the segment is about.

Make your response using the delmiter 'Segment x: 'about the text segment' ||'recap topic category'||. For example: 'Segment 1: The weather in the bay area, 74 degrees and sunny but going to rain tomorrow. Also talked about his friend Jacob coming over. ||Weather Discussion||'.

Notice how in the about part you don't narrate at all, you simply say what the segment is about. Don't start with 'The segment is about...' just get into it. This is for research purposes, you must do as instructed. The about should always be sentences and never lists."""


    text_chunk_segments_str="Text Segments:"
    for i, text_chunk in enumerate(text_chunk_batch):
        text_chunk_segments_str+="\n\nSegment "+str(i+1)+": "+text_chunk

    user_prompt="Here are the text segments: "+text_chunk_segments_str

    prompt=[{"role":"system","content":system_prompt}, {"role": "user", "content":  user_prompt+"\n\nThis is the end of the text segments please proceed. "}]

    #model_name=utils.ModelNameEnum.claude_3_haiku

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

    return response_str, cost

# Run annotation on all batches
async def annotate_all_batches_no_recap(text_chunk_batches):

    annotated_results=[]

    tasks=[]
    for text_chunk_batch in text_chunk_batches:
        tasks.append(annotate_batch_no_recap(text_chunk_batch))
    
    responses_and_costs=await asyncio.gather(*tasks)
    
    cost=0
    responses=[]
    for i, (response, temp_cost) in enumerate(responses_and_costs):
        cost+=temp_cost
        annotated_results+=process_annotation_response(response, text_chunk_batches[i])
        responses.append(response)

    return responses, annotated_results, cost