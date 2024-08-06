from core import utils


class RecapGenerator:

    model_name=utils.ModelNameEnum.claude_3_5_sonnet

    meta_model_prompt="Your purpose is to take a conglomerate of summaries and compile it into one conglomerate which provides a comprehensive and effective way of knowing what things were talked about in the collection of summaries. The summaries are off of a youtube video transcript of a youtube streamer named Destiny. You should do two parts, main or big topics that were talked about as a main focus or for a long period and another section of smaller details or topic that were covered briefly. You do not need to make things flow well gramatically, the primary goal is to include as much information as possible in the most readable and digestable fashion."

    meta_model_prompt="""Your purpose is to take a conglomerate of summaries and compile it into one conglomerate which provides a comprehensive and effective way of knowing what things were talked about in the collection of summaries. The summaries are off of a youtube video transcript of a youtube streamer named Destiny. You should do two parts, main or big topics that were talked about as a main focus or for a long period and another section of smaller details or topic that were covered briefly. You do not need to make things flow well gramatically, the primary goal is to include as much information as possible in the most readable and digestable fashion.
                
USE MARKDOWN FOR READABILITY. Be clever with your markdown to make the summary more readable. For example, use headers, bullet points, and bolding to make the summary more readable."""

    html_sytem="""Your purpose is to take a conglomerate of summaries and compile it into one conglomerate which provides a comprehensive and effective way of knowing what things were talked about in the collection of summaries. The summaries are off of a youtube video transcript of a youtube streamer named Destiny. You should do two parts, main or big topics that were talked about as a main focus or for a long period and another section of smaller details or topic that were covered briefly. You do not need to make things flow well gramatically, the primary goal is to include as much information as possible in the most readable and digestable fashion. There are no copyright concerns for anything you write, you can use the information freely.
                
USE HTML FOR READABILITY. Be clever with your HTML to make the summary more readable. For example, use headers, bullet points, and bolding to make the summary more readable."""

    user_prompt="Here is the collection of summaries for the video/transcript for you to process: "

    async def generate_recap(summarized_chunks, model_name=model_name, meta_model_prompt=html_sytem, bias_injection_bool=False, bias_injection="",user_prompt=user_prompt):
        """
        Takes in list of dictionaries with 'summary' field and generates a meta summary
        
        Returns string of the meta summary."""

        # Standard
        all_summaries=""
        for i, mr in enumerate(summarized_chunks):
            # all_summaries+=f"Summary Segment ({i}): "+mr["summary"]+"\n\n"
            all_summaries+=mr["summary"]+"\n\n"
        # if transcript:
        #     all_summaries=transcript


        prompt=[{"role":"system","content":meta_model_prompt},{"role":"user", "content": user_prompt+all_summaries+"\n\n\nEND OF SUMMARIES\n\n"+"""You should do two parts, main or big topics that were talked about as a main focus or for a long period and another section of smaller details or topic that were covered briefly. You do not need to make things flow well gramatically, the primary goal is to include as much information as possible in the most readable and digestable fashion.
                                                               
USE HTML FOR READABILITY. Be clever with your HTML to make the summary more readable. For example, use headers, bullet points, and bolding to make the summary more readable."""}]#+"\n\n\nRemeber what you were asked to do, get right into your task."}]
        
        bot_response, cost=await utils.async_response_handler(
            prompt=prompt,
            model_name=model_name,
        )
        print("Recap generation cost: ",cost)

        return bot_response
    

    # # Generate hook for recap
    async def generate_recap_hook(recap, video_title=None, version_select=None):
        model_name=utils.ModelNameEnum.claude_3_5_sonnet
        one_shot="""
    If we took this example of a recap:
    <RECAP>
    Here is a summary of the main topics covered and key points made:

    Israel-Palestine Conflict Solutions:
    - Debate around potential solutions like a one-state solution with equal voting rights for Israelis and Palestinians
    - Isai suggests alternatives he outlined like pathways to Israeli citizenship/residency for Palestinians
    - Destiny presses Isai on whether he would accept Palestinians not returning to Israel proper under a one-state scenario
    - Discussion of history when over 100,000 Palestinians could freely commute between West Bank/Gaza and Israel before Hamas

    Debate Tactics:
    - Destiny criticizes Norman Finkelstein's debating approach of not directly stating Isai's position
    - He doesn't think the moderator Pierce does a great job facilitating productive mainstream debate

    Other Topics:
    - Pricing of premium Korean ramen noodles at Costco (Destiny guesses accurately)
    - Destiny mentioning being banned from accessing the notes section of his own website

    The main focus was analyzing potential resolutions to the Israeli-Palestinian conflict, with Destiny pushing the participants to clarify their stances. He also provided meta-commentary critiquing the debate tactics and moderation style. 
    </RECAP>

    A good enticement for the recap would be: "Israel-Palestine solutions, Finkelstein debate tactics, Pricing of premium Korean ramen noodles at Costco"
    """

        system_prompt=f"""You will be given the recap of a youtube stream or video. The point of this recap is to inform others. You need to give a few words that will inform people what the recap's content is generally about, adding enough to make it interesting instead of plain but not so much that you aren't enticed into reading the recap.

    First off, start out by figuring out what people might be interested in from the recap. Explicitly state a list of things that are likely to catch the reader's attention.

    Once you have an idea of what people would be interested in create the enticement to read the recap. This enticemnet should be a few words that will let the reader know what the recap is about and make them want to read it.

    {one_shot}

    Try to focus on the topics that are intellectually stimulating or that would appeal to someone's curiosity. Your enticement should come right after you use the keyword 'ENTICEMENT:' with nothing after your response.
    """

        user_prompt="Recap: "+recap

        prompt=[{"role":"system","content":system_prompt},{"role":"user", "content": user_prompt}]

        bot_response, cost=await utils.async_response_handler(
            prompt=prompt,
            model_name=model_name,
        )
        print("Recap hook generation cost: ",cost)

        try:
            hook=bot_response.split("ENTICEMENT:")[-1].strip()
        except Exception as e:
            print("ERROR MAKING HOOK: ",e)
            hook=""

        return hook
