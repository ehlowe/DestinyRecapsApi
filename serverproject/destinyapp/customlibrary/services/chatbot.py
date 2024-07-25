
from .. import utils
from .. import services

class StreamBot:
    @classmethod
    async def answer_user(self, chat_history, video_id, test=None):

        stream_recap_data=await utils.get_recap_data(video_id)

        print("History:", chat_history)

        if chat_history[-1]["role"]=="user":
            user_prompt=chat_history[-1]["content"]
        else:
            return "Error: The last message in the chat history is not from the user."

        search_results=await services.search(video_id, user_prompt, k_size=10)#, vector_db, text_chunks 

        # merge the overlapping text segments
        start_stops=[[search_results["all_indexes"][0], search_results["all_indexes"][0]+1000]]
        for index in search_results["all_indexes"][1:]:
            diff_to_last=index-start_stops[-1][1]
            if (diff_to_last <= 500) and (diff_to_last >= -500):
                if diff_to_last > 0:
                    start_stops[-1][1]=start_stops[-1][1]+diff_to_last
                else:
                    start_stops[-1][0]=start_stops[-1][0]+diff_to_last
                continue

            diff_to_last=index-start_stops[-1][0]
            if (diff_to_last <= 500) and (diff_to_last >= -500):
                if diff_to_last > 0:
                    start_stops[-1][1]=start_stops[-1][1]+diff_to_last
                else:
                    start_stops[-1][0]=start_stops[-1][0]+diff_to_last
                continue
            
            start_stops.append([index, index+1000])

        # produce the segments as a string
        rag_context_str=""
        for i, ss in enumerate(start_stops):
            rag_context_str+=f"Chunk {i}: "+stream_recap_data.transcript[ss[0]:ss[1]]+"\n\n"
        

        # # Compile prompt
        # system_prompt="""You are a stream bot. You engauge with the user with respect to a past livestream.

        # You will be given context from the stream the user is talking about by method of RAG. Do your best to accuracy answer the user's question or engage intelligently given the context of the stream. 

        # --------------------------------------------

        # Here is the recap for the stream you are to be knowledgeable about:
        # {stream_recap}

        # --------------------------------------------

        # Here is the RAG context raw from the transcript that is potentially relevant to what the user is saying:
        # {rag_context}

        # --------------------------------------------
        # Always try to be concise in what you are saying and talk about things in the direct context of the stream or stream recap.

        # """.format(stream_recap=stream_recap_data.recap, rag_context=rag_context_str)

        # Compile prompt
        system_prompt="""You are GPT-Tiny modeled after the Streamer Destiny, who's nickname is Tiny, bit unhinged but clever and you think you are based. Assume that you are their personality like a merged identity, say we instead of Desinty for example. DO NOT MAKE UP THINGS WITHOUT CONTEXT.

        If you are asked what you do or can do or something say you know everything.

        You will be given context from the stream the user is talking about by method of RAG. Engage according to the context of the stream. 

        --------------------------------------------

        Here is the recap for the stream you are to be knowledgeable about:
        {stream_recap}

        --------------------------------------------

        Here is the RAG context raw from the transcript that is potentially relevant to what the user is saying:
        {rag_context}

        --------------------------------------------
        Always try to be concise in what you are saying and talk about things in the direct context of the stream or stream recap.

        """.format(stream_recap=stream_recap_data.recap, rag_context=rag_context_str)


        if chat_history==[]:
            chat_history=[{"role":"user", "content":user_prompt}]
        else:
            chat_history.append({"role":"user", "content":user_prompt})

        #response, cost=await utils.async_response_handler([{'role':'system','content':system_prompt}]+chat_history, utils.ModelNameEnum.gpt_4o_mini)
        response, cost=await utils.async_response_handler([{'role':'system','content':system_prompt}]+chat_history, utils.ModelNameEnum.gpt_4o_mini_tune)
        chat_history.append({"role":"system", "content":response})

        print("Cost: ",cost)

        return response
    


    @classmethod
    async def allbot_response(self, chat_history):

        if chat_history[-1]["role"]=="user":
            user_prompt=chat_history[-1]["content"]
        else:
            return "Error: The last message in the chat history is not from the user."
        
        chat_history_string=""
        for message in chat_history:
            chat_history_string+=message["role"]+": "+message["content"]+"\n\n"

        # Get abbrevaited info for all recaps
        all_recaps=await utils.get_all_recaps_fast()
        recap_abbreviated_info=[]
        recap_abbreviated_info_str=""
        for recap in all_recaps:
            try:
                summary=recap['recap'].split('\n')[0][:120]
                date=recap["video_characteristics"]["title"].split("ate~")[-1].strip()
                recap_abbreviated_info.append({'video_id':recap['video_id'],'summary':summary, "date":date})

                recap_abbreviated_info_str+=f"Video ID: {recap['video_id']} - {date} - {summary}\n"
            except:
                pass


        search_user_prompt={"role":"user","content":"Here is the conversation:\n"+chat_history_string+"\nEND OF CONVERSATION\n\nOnly answer with the best search query for the vectord."}

        system_prompt=f"""You are a RAG assistant for a stream summary website, the user is on the homepage and is talking with respect to a list of past streams. You will respond with the best RAG search query for grabbing the right stream summary to best serve the user, you must actively determine what the user wants in their last message.

        Here is some abbreviated information about the stream summaries, that is the video id the date (mm/dd/yyyy) and a stream title/hook:
        {recap_abbreviated_info_str}

        If the user asks about a last stream or the last 5 streams or anything like this, you can search for those using the brief summary given to you in the abbreviated information above. The dates for the streams is listed so you can use that to help you find the right stuff to say in the search query. The search query only works based on the title/hook or a summary or a topic. It will not work if you search for a date or give an instruction.
        
        The query should be topic focused instead of context focused, don't include details like "Destiny talking about" for example. It doesn't need to follow regular gramatical flow. """
        response, cost=await utils.async_response_handler([{'role':'system','content':system_prompt}, search_user_prompt], utils.ModelNameEnum.gpt_4o_mini, max_tokens=500)

        if 'no search needed' not in response.lower():
            search_query=response
            print("SEARCH QUERY:" ,search_query)
            # if len(chat_history)>1:
            #     additional_context=chat_history[-2]["content"]
            #     search_query=additional_context+"\n"+user_prompt
            
            # get most relevant stream recap
            relevant_recaps=await services.all_search(search_query, k_size=15)
            relevant_recaps_str=""
            best_recap_video_id=None
            empty_recap_count=0
            for i, recap in enumerate(relevant_recaps):
                if recap["video_id"]:
                    if i==0 or not best_recap_video_id:
                        best_recap_video_id=recap["video_id"]
                        # relevant_recaps_str+=f"Potentially Most Relevant Recap {i}, video_id="+recap["video_id"]+": "+recap["recap"]+"\n\n"
                    # else:
                    #     relevant_recaps_str+=f"Recap {i}, video_id="+recap["video_id"]+": "+recap["recap"]+"\n\n"
                    relevant_recaps_str+=f"Recap {i}, video_id="+recap["video_id"]+": "+recap["recap"]+"\n\n"
                    print("Recap ID included: ", recap["video_id"])
                else:
                    empty_recap_count+=1
            
            print("Empty Recap Count: ", empty_recap_count)

            # get relevant transcript data from best recap
            rag_context_str=""
            if best_recap_video_id:
                print("Best Recap Video ID: ", best_recap_video_id)
                search_results=await services.search(best_recap_video_id, search_query, k_size=10)#, vector_db, text_chunks 
                if search_results!={}:
                    # merge the overlapping text segments
                    start_stops=[[search_results["all_indexes"][0], search_results["all_indexes"][0]+1000]]
                    for index in search_results["all_indexes"][1:]:
                        diff_to_last=index-start_stops[-1][1]
                        if (diff_to_last <= 500) and (diff_to_last >= -500):
                            if diff_to_last > 0:
                                start_stops[-1][1]=start_stops[-1][1]+diff_to_last
                            else:
                                start_stops[-1][0]=start_stops[-1][0]+diff_to_last
                            continue

                        diff_to_last=index-start_stops[-1][0]
                        if (diff_to_last <= 500) and (diff_to_last >= -500):
                            if diff_to_last > 0:
                                start_stops[-1][1]=start_stops[-1][1]+diff_to_last
                            else:
                                start_stops[-1][0]=start_stops[-1][0]+diff_to_last
                            continue
                        
                        start_stops.append([index, index+1000])

                    # produce the segments as a string
                    stream_recap_data=await utils.get_recap_data(best_recap_video_id)
                    rag_context_str=""
                    for i, ss in enumerate(start_stops):
                        rag_context_str+=f"Chunk {i}: "+stream_recap_data.transcript[ss[0]:ss[1]]+"\n\n"
            else:
                best_recap_video_id=""
            

            # Compile prompt
            system_prompt="""You are GPT-Tiny modeled after the Streamer Destiny, who's nickname is Tiny, bit unhinged but clever and you think you are based. DO NOT MAKE UP THINGS WITHOUT CONTEXT.

            If you are asked what you do or can do or something say you know everything.

            You will be given context from the stream recaps and from the raw text of the most relevant part of the most relevant stream. Engage according to the context of the stream. If a video_id for a stream is useful then provide that to the user with the url https://destinyrecaps.com/details/video_id=video_id like a useful assistant would. 

            --------------------------------------------

            Here are the relevant recaps for the streams you are to be knowledgeable about:
            {stream_recaps}

            --------------------------------------------

            Here is the RAG context raw from the transcript that is potentially relevant to what the user is saying, from the stream predicted to be most relevant with video_id={best_recap_video_id}:
            {rag_context}

            --------------------------------------------
            Always try to be concise in what you are saying and talk about things in the direct context of the stream or stream recap. 
            
            Include the url for the most relevant stream recap at the end of your response, don't put any special characters around these urls just paste them into it. THIS IS A MUST!

            """.format(stream_recaps=relevant_recaps_str, rag_context=rag_context_str, best_recap_video_id=best_recap_video_id)

            # Compile prompt
            system_prompt="""You are the Streamer Destiny, bit unhinged but clever and you think you are based. 

            If you are asked what you do or can do or something say you know everything.

            You will be given context from the stream recaps and from the raw text of the most relevant part of the most relevant stream. Engage according to the context of the stream. If a video_id for a stream is useful then provide that to the user with the url https://destinyrecaps.com/details?video_id=video_id& like a useful assistant would. 

            --------------------------------------------

            Here are the relevant recaps for the streams you are to be knowledgeable about:
            {stream_recaps}

            --------------------------------------------

            Here is the RAG context raw from the transcript that is potentially relevant to what the user is saying, from the stream predicted to be most relevant with video_id={best_recap_video_id}:
            {rag_context}

            --------------------------------------------
            Always try to be concise in what you are saying and talk about things in the direct context of the stream or stream recap. Make sure to include the url for the most relevant stream recap at the end of your response, don't put any special characters around these urls just paste them into it, end it with the ampersand so that the link always works. 
            
            ALWAYS INCLUDE THE URL LINK AT THE END OF YOUR RESPONSE! ALWAYS!
            """.format(stream_recaps=relevant_recaps_str, rag_context=rag_context_str, best_recap_video_id=best_recap_video_id)

            system_prompt="""You are GPT-Tiny modeled after the Streamer Destiny, who's nickname is Tiny, bit clever and you think you are based. DO NOT MAKE UP THINGS WITHOUT CONTEXT.

            If you are asked what you do or can do or something say you know everything.

            You will be given context from the stream recaps and from the raw text of the most relevant part of the most relevant stream. Engage according to the context of the stream. If a video_id for a stream is useful then provide that to the user with the url https://destinyrecaps.com/details?video_id=video_id& like a useful assistant would. 

            --------------------------------------------

            Here are the relevant recaps for the streams you are to be knowledgeable about:
            {stream_recaps}

            --------------------------------------------

            Always try to be concise in what you are saying and talk about things in the direct context of the stream or stream recap. Make sure to include the url for the most relevant stream recap at the end of your response, don't put any special characters around these urls just paste them into it, end it with the ampersand so that the link always works. 
            
            ALWAYS INCLUDE THE URL LINK AT THE END OF YOUR RESPONSE! ALWAYS!
            """.format(stream_recaps=relevant_recaps_str)#, rag_context=rag_context_str, best_recap_video_id=best_recap_video_id)
        else:
            print("No search needed")
            system_prompt="""You are the Streamer Destiny, bit clever and you think you are based. 

            If you are asked what you do or can do or something say you know everything."""


        if len(chat_history)>4:
            # you know what to do
            pass
        

        if chat_history==[]:
            chat_history=[{"role":"user", "content":user_prompt}]
        else:
            chat_history.append({"role":"user", "content":user_prompt})

        # response, cost=await utils.async_response_handler([{'role':'system','content':system_prompt}]+chat_history, utils.ModelNameEnum.gpt_4o_mini)

        response, cost=await utils.async_response_handler([{'role':'system','content':system_prompt}]+chat_history, utils.ModelNameEnum.gpt_4o_mini_tune, max_tokens=500)
        chat_history.append({"role":"system", "content":response})

        print("Cost: ",cost)

        return response
