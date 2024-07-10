import re
import asyncio

from .. import utils



async def create_text_chunks(transcript, overlap_character_count=500):
    chunk_size=1000
    overlap=overlap_character_count
    text_chunks=[transcript[i:i+chunk_size] for i in range(0, len(transcript), (chunk_size-overlap))]
    print("Number of chunks: ",len(text_chunks))

    return text_chunks


async def generate_text_chunk_batches(text_chunks):

    # target chunk batch size
    target_batch_size=10

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

    for response in responses:
        annotated_results+=process_annotation_response(response)

    return responses, annotated_results

async def annotate_batch(text_chunk_batch, recap):


    system_prompt="""The user will give you text segments and you must annotate what the segment is about for each number. 

The user will give a recap with major and minor topics which you will use to categorize the text segments and will provide the segments. You will also need to say what the segment is about.

The recap will have a major topics section, each of these high level topics is a category, when listing the category of a segment you must use the exact text of the major topic. If the segment doesn't fit into a major topic then you categorize it as 'non categorized'. The minor topics are a list, if a segment contains the content of the minor topic then the category label should be the exact text of that minor topic in the recap.If the segment doesn't fit into a minor topic then you categorize it as 'non categorized'. 

DO NOT FORGET THE MINOR TOPICS

Make your response using the delmiter 'Segment x (recap topic category):' about the text segment. For example: 'Segment 1 (Weather Discussion): The weather in the bay area, 74 degrees and sunny but going to rain tomorrow.' Where 'Weather Discussion' is a major topic in the recap."""

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



def process_annotation_response(response_str):
    pattern = r"Segment (\d+) \(([^)]+)\): (.+)"
    matches = re.findall(pattern, response_str, re.MULTILINE)
    
    results = []
    for match in matches:
        segment_number = int(match[0])
        category = match[1]
        annotation = match[2].strip()
        results.append({
            "segment": segment_number,
            "category": category,
            "annotation": annotation
        })
    
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
    


