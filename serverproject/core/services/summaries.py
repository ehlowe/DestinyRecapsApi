import math
import asyncio
import time


from core import utils


class SummarizedSegmentGenerator:
    
        model_name=utils.ModelNameEnum.claude_3_5_sonnet

        summarization_prompt="Your purpose is to take a transcript from a youtube streamer named Destiny and give a synopsis of the content and the sentiment/takes of the speaker. Include all of the topics even if they are covered briefly instead of just covering the main topic."

        long_summarization_prompt="""Your purpose is to take a transcript from a youtube streamer named Destiny and give a synopsis of the content and the sentiment/takes of the speaker. Include all of the topics even if they are covered briefly instead of just covering the main topic although you should do that as well. The main topic or seeming focus of the segment and all of the things said or discussed. This should be quite long.
        
FYI: The transcript is diarized, Destiny should be annotated 'Destiny' with other speaker being a default from the transcription engine like b, c, d ... etc. You may have to use some intuition to figure out what is happening."""
        summarization_prompt=long_summarization_prompt

        long_summarization_prompt="""You are given a transcript from a youtube stream focused on a streamer named Destiny. The transcript is diarized, Destiny should be annotated 'Destiny' with other speaker being a default from the transcription engine like b, c, d ... etc. You may have to use some intuition to figure out what is happening because Destiny may say something but he is reading chat or he may be watching something and it may look like he is in a conversation when he is just reacting or he might actually be talking with or debating someone.
         
Your job is to create an excellent summary of the segment of the transcript given to you. This can be done in two parts, main focus and all topics. Include all of the topics even if they are covered briefly because it helps build a full sense of what happened. It is also important to know the majority of what happened and what was happening in the segment in general. This should be quite long, try to get into the specifics, that is where the value is."""
   
        async def fetch_response(input_data, model_name=model_name, summarization_prompt=summarization_prompt):
            transcript_segment=input_data["transcript"]

            # find where text appears in the transcript
            # segment_index=transcript.find(transcript_segment)

            index=input_data["index"]


            conv_messages=[{"role":"system","content":summarization_prompt}, {"role": "user", "content": "Transcript: "+transcript_segment}]
            
            bot_response=""
            fails=0
            cost=0
            while True:
                if fails>5:
                    print("Failed to get response for index: ",index)
                    return ["",index]

                bot_response=""
                print(str(index)+" ", end="")
                try:
                    bot_response, cost=await utils.async_response_handler(
                        prompt=conv_messages,
                        model_name=model_name,
                    )
                    break
                except Exception as e:
                    fails+=1
                    print("Error:",e,str(index)+" ", end="")
                    time.sleep(10+(fails*2))
                    print("Retrying:",str(index)+" ", end="")

            return [bot_response, index, cost]


        @classmethod
        async def generate_summarized_segments(self, transcript, segments=150, increment_chars=10000, model_name=model_name, summarization_prompt=summarization_prompt):
            """
            Create transcript segements and summarize them.
            
            Returns a list of dictionaries with the summaries annotated by 'summary'
            """

            # get a certain number of segments
            char_start_index=0
            model_responses=[]
            index=0
            while (len(model_responses)<segments) and ((char_start_index)<=len(transcript)):
                input_transcript=transcript[char_start_index:char_start_index+increment_chars]

                # display start and endtime
                start_second_raw=0#get_time_at_length_transcript(nearest_times, char_start_index)
                hours = math.floor(start_second_raw / 3600)
                minutes = math.floor((start_second_raw % 3600) / 60)
                seconds = start_second_raw % 60

                # calculate end time
                end_second_raw=1#get_time_at_length_transcript(nearest_times, char_start_index+increment_chars)
                hours_end = math.floor(end_second_raw / 3600)
                minutes_end = math.floor((end_second_raw % 3600) / 60)
                seconds_end = end_second_raw % 60

                sf_str=f"Start time {int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}  End time {int(hours_end):02d}:{int(minutes_end):02d}:{seconds_end:06.3f}"
                
                model_responses.append({"summary": "","transcript": input_transcript,"time_string":sf_str,"char_start_finish_indexes":[char_start_index,char_start_index+increment_chars], "index":index, "start_second":start_second_raw, "end_second":end_second_raw})

                index+=1
                char_start_index+=increment_chars-300
            
            # Run segmention process
            summary_responses=await asyncio.gather(*(self.fetch_response(in_data) for in_data in model_responses))

            # setup data to feed into model
            total_cost=0
            for i in range(len(summary_responses)):
                model_responses[i]["summary"]=summary_responses[i][0]
                print(i, model_responses[i]["index"])
                total_cost+=summary_responses[i][2]
            print("Total cost: ",total_cost)
            
            return model_responses
        
        