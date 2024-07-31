import asyncio

from . import data_processing
from destinyapp.customlibrary import utils



async def recap_segment(category, texts):
    if texts==[]:
        return ""
    
    system_prompt="You are a recaper. The user will tell you the supposed category of the content and the text of the content. Your job is to make a 250-100 word recap of what was said in precise detail. "
    user_prompt="Category: "+category+"\n\nText:"
    for text in texts:
        user_prompt+=text+"\n"
    full_prompt=[{"role":"system", "content":system_prompt}, {"role":"user", "content":user_prompt}]
    response, cost = await utils.async_response_handler(full_prompt, utils.ModelNameEnum.gpt_4o_mini)
    return response
    

async def recap_segments(plot_object: data_processing.PlotObject):
    # Produce the segment recaps
    tasks=[]
    for i in range(len(plot_object.segments)):
        tasks.append(recap_segment(plot_object.segments[i].category, plot_object.segments[i].texts))
    responses=await asyncio.gather(*tasks)

    # load the responses into the plot object
    for i in range(len(plot_object.segments)):
        plot_object.segments[i].recap=responses[i]

    return plot_object



async def recap_abstraction(category, segment_recaps):
    if segment_recaps==[]:
        return ""

    system_prompt="You are a recaper. The user will tell you the supposed category of the content and the text of the content. Your job is to make a 250-100 word recap of what was said in precise detail. "
    user_prompt="Category: "+category+"\n\nText:"
    for recap in segment_recaps:
        user_prompt+=recap+"\n"
    full_prompt=[{"role":"system", "content":system_prompt}, {"role":"user", "content":user_prompt}]
    response, cost = await utils.async_response_handler(full_prompt, utils.ModelNameEnum.gpt_4o_mini)
    return response

async def recap_abstractions(plot_object: data_processing.PlotObject):
    # Produce the abstraction recaps
    tasks=[]
    for key in list(plot_object.abstractions.keys()):
        # get all the segments with category == key
        temp_segment_recaps=[]
        for segment in plot_object.segments:
            if segment.category==key:
                temp_segment_recaps.append(segment.recap)

        tasks.append(recap_abstraction(key, temp_segment_recaps))
    responses=await asyncio.gather(*tasks)

    # load the responses into the plot object
    for i, key in enumerate(list(plot_object.abstractions.keys())):
        plot_object.abstractions[key].recap=responses[i]

    return plot_object

