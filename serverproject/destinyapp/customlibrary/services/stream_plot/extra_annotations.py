import asyncio

from . import data_processing
from destinyapp.customlibrary import utils



async def recap_segment(category, texts):
    if texts==[]:
        return ""
    
    system_prompt="""You are a stream segment recapper with an active voice. The user will tell you the supposed category of the content and the text of the content. Your job is to make a 50 word recap of what was said in precise detail. 
    
Do not use any fluff, your response does not need to be gramatically correct. Start with what generally happened and then go into specifics. """
    user_prompt="Category: "+category+"\n\nText:"
    for text in texts:
        user_prompt+=text+"\n"
    full_prompt=[{"role":"system", "content":system_prompt}, {"role":"user", "content":user_prompt}]
    response, cost = await utils.async_response_handler(full_prompt, utils.ModelNameEnum.gpt_4o_mini)
    return response, cost
    

async def recap_segments(plot_object: data_processing.PlotObject):
    # Produce the segment recaps
    tasks=[]
    for i in range(len(plot_object.segments)):
        tasks.append(recap_segment(plot_object.segments[i].category, plot_object.segments[i].texts))
    responses_and_costs=await asyncio.gather(*tasks)

    # load the responses into the plot object
    cost=0
    for i in range(len(plot_object.segments)):
        plot_object.segments[i].recap=responses_and_costs[i][0]
        cost+=responses_and_costs[i][1]

    return plot_object, cost



async def recap_abstraction(category, segment_recaps):
    if segment_recaps==[]:
        return ""

    system_prompt="""You are a stream segment recapper with an active voice. The user will tell you the supposed category of the content and the recaps of the contents. Your job is to make a 50 word recap of what was said, specifically in relation to the category, in precise detail. 
    
Do not use any fluff, your response does not need to be gramatically correct. Start with what generally happened and then go into specifics. """
    user_prompt="Category: "+category+"\n\nText:"
    for recap in segment_recaps:
        user_prompt+=recap+"\n"
    full_prompt=[{"role":"system", "content":system_prompt}, {"role":"user", "content":user_prompt}]
    response, cost = await utils.async_response_handler(full_prompt, utils.ModelNameEnum.gpt_4o_mini)
    return response, cost

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
    responses_and_costs=await asyncio.gather(*tasks)

    # load the responses into the plot object
    cost=0
    for i, key in enumerate(list(plot_object.abstractions.keys())):
        plot_object.abstractions[key].recap=responses_and_costs[i][0]
        cost+=responses_and_costs[i][1]


    return plot_object, cost

