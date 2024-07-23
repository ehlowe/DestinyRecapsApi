
from .. import utils
from .. import services

class StreamBot:
    chat_history=[]

    @classmethod
    async def answer_user(self, video_id, test=None):

        stream_recap_data=await utils.get_recap_data(video_id)

        if self.chat_history[-1]["role"]=="user":
            user_prompt=self.chat_history[-1]["content"]
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
        

        # Compile prompt
        system_prompt="""You are a stream bot. You engauge with the user with respect to a past livestream.

        You will be given context from the stream the user is talking about by method of RAG. Do your best to accuracy answer the user's question or engage intelligently given the context of the stream. 

        --------------------------------------------

        Here is the recap for the stream you are to be knowledgeable about:
        {stream_recap}

        --------------------------------------------

        Here is the RAG context raw from the transcript that is potentially relevant to what the user is saying:
        {rag_context}

        --------------------------------------------
        Always try to be concise in what you are saying and talk about things in the direct context of the stream or stream recap.

        """.format(stream_recap=stream_recap_data.recap, rag_context=rag_context_str)

        if self.chat_history==[]:
            self.chat_history=[{"role":"user", "content":user_prompt}]
        else:
            self.chat_history.append({"role":"user", "content":user_prompt})

        response, cost=await utils.async_response_handler([{'role':'system','content':system_prompt}]+self.chat_history, utils.ModelNameEnum.gpt_4o_mini)
        self.chat_history.append({"role":"system", "content":response})

        print("Cost: ",cost)

        return response