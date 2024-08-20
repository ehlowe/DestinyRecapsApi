import asyncio
import re
from datetime import datetime

from core import utils
from destinyapp.models import StreamRecapData


# load all recaps and get the time topics from each
async def generate_data(all_recaps):
    ordered_recaps=[]

    for recap in all_recaps:
        title=recap["video_characteristics"]["title"]
        if ("ate:" in title):
            stream_date=title.split("ate:")[-1].strip()
        elif ("ate~" in title):
            stream_date=title.split("ate~")[-1].strip()
        ordered_recaps.append([stream_date, recap])

    # sort by date mm/dd/yyyy in descending order
    ordered_recaps.sort(key=lambda x: datetime.strptime(x[0], "%m/%d/%Y"), reverse=True)
    return ordered_recaps

    

async def make_timeline_data(topic_date_string):
    example="""
Input:
07/01/2024: Presidential immunity debate, Biden's 2024 prospects, Constitutional power struggles, Trump's legal battles

06/30/2024: Russia-Ukraine conflict, US foreign policy debates, NATO's role in modern geopolitics, analysis of international conflicts Destiny unpacks Israel-Palestine, slams Trump's GOP, defends Biden, and navigates audience skepticism while battling tech gremlins

06/28/2024: U.S. election dynamics, streaming industry drama, Israel-Palestine insights, content moderation ethics, and wealth taxation debates

06/27/2024: Israel-Palestine conflict, European immigration debates, streaming techniques, Trump analysis, cultural clashes, archaeological revelations

06/25/2024: Streaming tech wizardry, Rust strategies, debate prep, and pop culture musings - a peek into Destiny's multifaceted world



Response:
07/01/2024: 2024 electrion and Trump

06/30/2024: Israel-Palestine, 2024 election and Trump, Ukraine-Russia conflict

06/28/2024: 2024 election and Trump, Israel-Palestine, streaming industry

06/27/2024: Israel-Palesine, Immigration

06/25/2024: Goofing off

"""
    system_prompt=f"""
You are a timeline generator for a streamer named Destiny. You will be provided a brief overview of what was said or done on a stream for a day and then you will have to make a timeline of the various erras of the streams. 

Your response should attempt to unity topics into a coherent timeline. 

It should be structured like this:
date: timeline category/s

Here is an example:
{example}

IT IS CRITICAL THAT THE CATEGORIES ARE CONSISTENT SO THAT THE TIMELINE WILL BE CONSISTENT. YOU ARE EFFECTIVELY CLUMPING UP THE TOPICS INTO CATEGORIES.
"""

#     example="""
# Input:    
# 06/22/2024: Destiny's Twitch ban, Israel-Palestine conflict deep dive, COVID-19 misinformation, streaming platform comparisons

# 06/22/2024: Upcoming debates, Twitch drama, Russian bot analysis, and work-life balance insights

# 06/19/2024: Israel-Hamas conflict: Just war debate, historical roots, AI in warfare, and challenging simplistic narratives


# Response:
# 06/22/2024:

# 06/22/2024:

# 06/19/2024: Israel-Palastine, challenging misinformation, streaming platform discussions
# """



    full_prompt=[{"role":"system","content":system_prompt},{"role":"user","content":topic_date_string}]

    response, cost= await utils.async_response_handler(full_prompt, utils.ModelNameEnum.gpt_4o_mini)

    print(cost)

    return response




async def normalize_data_gen(data_generated):
    example="""Input:
07/01/2024: Presidential immunity debate, Biden's 2024 prospects, Constitutional power struggles, Trump's legal battles

06/30/2024: Russia-Ukraine conflict, US foreign policy debates, NATO's role in modern geopolitics, analysis of international conflicts Destiny unpacks Israel-Palestine, slams Trump's GOP, defends Biden, and navigates audience skepticism while battling tech gremlins

06/28/2024: U.S. election dynamics, streaming industry drama, Israel-Palestine insights, content moderation ethics, and wealth taxation debates

06/27/2024: Israel-Palestine conflict, European immigration debates, streaming techniques, Trump analysis, cultural clashes, archaeological revelations

06/25/2024: Streaming tech wizardry, Rust strategies, debate prep, and pop culture musings - a peek into Destiny's multifaceted world



Response:
07/01/2024: 2024 electrion and Trump

06/30/2024: Israel-Palestine, 2024 election and Trump, Ukraine-Russia conflict

06/28/2024: 2024 election and Trump, Israel-Palestine, streaming industry

06/27/2024: Israel-Palesine, Immigration

06/25/2024: Goofing off"""


    example="""
Input:
07/01/2024: Presidential immunity debate, Biden's 2024 prospects, Constitutional power struggles, Trump's legal battles

06/30/2024: Russia-Ukraine conflict, US foreign policy debates, NATO's role in modern geopolitics, analysis of international conflicts Destiny unpacks Israel-Palestine, slams Trump's GOP, defends Biden, and navigates audience skepticism while battling tech gremlins

06/28/2024: U.S. election dynamics, streaming industry drama, Israel-Palestine insights, content moderation ethics, and wealth taxation debates

06/27/2024: Israel-Palestine conflict, European immigration debates, streaming techniques, Trump analysis, cultural clashes, archaeological revelations

06/25/2024: Streaming tech wizardry, Rust strategies, debate prep, and pop culture musings - a peek into Destiny's multifaceted world



Response:
2024 election and Trump:
07/01/2024, 06/30/2024, 06/28/2024, 06/27/2024

Israel-Palestine conflict:
06/30/2024, 06/28/2024, 06/27/2024

Supreme Court and legal battles:
07/01/2024

Ukraine-Russia conflict:
06/30/2024

Streaming industry:
06/28/2024

Immigration:
06/27/2024

Goofing off:
06/25/2024
"""

    system_prompt=f"""
You are a timeline generator for a streamer named Destiny. You will be provided a brief overview of what was said or done on a stream for a day and you have to remake that list of overviews so that similar topics are grouped together under terms with the same exact name.

Here is an example notice how the same exact topics are reused and are quite broad allowing them to be grouped together:
{example}"""
    #THE GOAL IS NOT TO ANNOTATE ALL THE TOPICS IT IS TO GET THE GIST OVER THE COURSE OF WEEKS OR MONTHS.
    #
    full_prompt=[{"role":"system","content":system_prompt},{"role":"user","content":data_generated}]

    response, cost= await utils.async_response_handler(full_prompt, utils.ModelNameEnum.claude_3_5_sonnet)#utils.ModelNameEnum.gpt_4o_mini)

    print(cost)

    return response





async def parse_normalized_data(normalized_data):
    # Parse this:
    test="""
Here's the reorganized timeline with similar topics grouped together:

2024 Election and Trump:
07/23/2024, 07/22/2024, 07/20/2024, 07/18/2024, 07/17/2024, 07/15/2024, 07/06/2024, 06/28/2024

January 6th and Election Challenges:
07/22/2024, 07/20/2024, 07/18/2024, 07/15/2024

Supreme Court and Legal Battles:
07/23/2024, 07/20/2024, 07/10/2024, 07/09/2024, 07/08/2024, 07/05/2024, 07/04/2024, 07/03/2024, 07/01/2024
"""
    split_datas=normalized_data.split("\n")
    data_prev=""

    timeline_data={}


    def is_date(str_input):
        try:
            # with datetime
            datetime.strptime(str_input, "%m/%d/%Y")
            return True
        except:
            return False
        

    for split_data in split_datas:

        split_data=split_data.strip()
        items=split_data.split(",")

        # print(items[0])
        # test=datetime.strptime(items[0], "%m/%d/%Y")

        if is_date(items[0]):
            timeline_data[data_prev]=items

        data_prev=split_data

    return timeline_data



    
    


"""07/23/2024, 07/22/2024, 07/20/2024, 07/18/2024, 07/17/2024, 07/15/2024, 07/06/2024, 07/05/2024, 07/04/2024, 07/03/2024, 07/01/2024, 06/28/2024: 2024 election and Trump

07/23/2024, 07/10/2024, 07/09/2024, 07/08/2024, 07/05/2024, 07/04/2024, 07/03/2024, 07/01/2024: Supreme Court and legal battles

07/21/2024, 07/17/2024, 07/15/2024, 07/09/2024: Media and technology

07/22/2024, 07/20/2024, 07/18/2024, 07/15/2024: January 6th analysis

06/30/2024, 06/27/2024, 06/22/2024, 06/19/2024: Israel-Palestine conflict

07/21/2024, 06/27/2024: Immigration

07/10/2024, 07/08/2024, 07/03/2024: Economic debates

07/23/2024, 06/28/2024: Streaming industry

07/16/2024, 06/25/2024: Goofing off

07/07/2024: Police reform

07/02/2024: Trump-Epstein connection

06/30/2024: Ukraine-Russia conflict"""