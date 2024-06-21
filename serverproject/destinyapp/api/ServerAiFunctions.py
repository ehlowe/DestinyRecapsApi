# Imports
import openai
import tiktoken
import asyncio
import faiss
import numpy as np
import datetime
import math
import time
import json
import os
import requests
import random
from enum import Enum
from youtube_transcript_api import YouTubeTranscriptApi
from IPython.display import display, HTML
from asgiref.sync import sync_to_async
from moviepy.editor import AudioFileClip, concatenate_audioclips
import yt_dlp
import copy


# import from base directory
from destinyapp import views

# import django models
from destinyapp.models import TranscriptData

# Transcript Summarization Prompt
transcript_summarization_prompt="Your purpose is to take a transcript from a youtube streamer named Destiny and give a synopsis of the content and the sentiment/takes of the speaker. Include all of the topics even if they are covered briefly instead of just covering the main topic."
transcript_summarization_prompt2="Your purpose is to take a transcript from a youtube streamer named Destiny and give a synopsis of the content and the sentiment/takes of the speaker. Include all of the topics even if they are covered briefly instead of just covering the main topic."


# # AI MODEL SETUP AND FUNCTIONS
# Text tokenizer for costs
enc=tiktoken.get_encoding("cl100k_base")
# Enum for model names
class ModelCompanyEnum(str, Enum):
    openai= "openai"
    anthropic= "anthropic"
class ModelNameEnum(str, Enum):
    gpt_4_turbo = "gpt-4-turbo"
    gpt_4o = "gpt-4o"
    gpt_3_5_turbo = "gpt-3.5-turbo"
    claude_3_5_sonnet = "claude-3-5-sonnet-20240620"
    claude_3_sonnet = "claude-3-sonnet-20240229"
    claude_3_opus = "claude-3-opus-20240229"

# Response Handler
async def async_response_handler(
    prompt,
    modelcompany,
    modelname,
    temp=0.0,
    frequency_penalty=0,
    presence_penalty=0,
):
    if modelcompany==ModelCompanyEnum.openai:
        response = await views.async_openai_client.chat.completions.create(
                model=modelname,
                messages=prompt,
                temperature=temp,
                top_p=1,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
        return response.choices[0].message.content
    
    elif modelcompany==ModelCompanyEnum.anthropic:
        system_message=prompt[0]["content"]
        response = await views.async_anthropic_client.messages.create(
                model=modelname,
                max_tokens=4000,
                temperature=temp,
                system=system_message,
                messages=prompt[1:]
            )
        return response.content[0].text
    
    else:
        raise Exception("Model company not recognized")
    
# calculate cost
def calculate_cost(model_name, tokens):
    cost_rates={"claude-3-sonnet-20240229": {"input": 3/1000000.0, "output": 15/1000000.0}}
    cost_rate=cost_rates[model_name]

    input_cost = tokens[0] * cost_rate["input"]
    output_cost = tokens[1] * cost_rate["output"]
    return {"input": input_cost, "output": output_cost}























# # DATABASE FUNCTIONS
# Main saving function
async def save_data(video_id, field_data_dict):
    transcript_exists = await sync_to_async(TranscriptData.objects.filter(video_id=video_id).exists)()
    # if transcript data exists
    if transcript_exists:
        transcript_data = await sync_to_async(TranscriptData.objects.get)(video_id=video_id)
        print("updating transcript data")
        for field_name, data in field_data_dict.items():
            setattr(transcript_data, field_name, data)
        await sync_to_async(transcript_data.save)()
    else:
        print("creating new transcript data")
        transcript_data=TranscriptData(video_id=video_id)
        for field_name, data in field_data_dict.items():
            setattr(transcript_data, field_name, data)
        await sync_to_async(transcript_data.save)()

# grab transcript data
async def grab_transcript_data(video_id):
    exists = await sync_to_async(TranscriptData.objects.filter(video_id=video_id).exists)()
    if exists:
        transcript_data = await sync_to_async(TranscriptData.objects.get)(video_id=video_id)
    else:
        transcript_data=None
    return transcript_data

# Get all data
async def get_all_data(verbose=False):
    all_data = await sync_to_async(list)(TranscriptData.objects.all())
    if verbose:
        for data in all_data:
            print(data.video_id)
    return all_data






# # MAIN GENERATION FUNCTIONS
# Video Download
async def video_download(video_id):#, output_folder, output_name):
    """Takes a video id, downloads the video from youtube, concatenates the video with a pre-recorded audio file of the target speaker
    
    This allows targeted diarization of the audio file."""

    # Download video
    def download_video_thread(video_id):
        # Set download parameters
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'workingaudio/raw'+'.%(ext)s',#os.path.join(output_folder,output_name)+'.%(ext)s',
            'age_limit': 21, 
        }

        # delete previous audio file with 'raw' in the name
        audio_dir_files=os.listdir("workingaudio")
        for file_name in audio_dir_files:
            if 'raw' in file_name:
                os.remove("workingaudio/"+file_name)
                break

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(['https://youtu.be/'+video_id])

        # open destinyspeaking.mp3
        destiny_speech_path="workingaudio/destinyspeaking.mp3"
        destiny_speech = AudioFileClip(destiny_speech_path)
        audio_dir_files=os.listdir("workingaudio")

        # find the audio file with 'raw' in the name
        for file_name in audio_dir_files:
            if 'raw' in file_name:
                youtube_audio_path="workingaudio/"+file_name
                break

        # Concatentate the two audio files
        youtube_video = AudioFileClip(youtube_audio_path)
        merged_audio = concatenate_audioclips([destiny_speech, youtube_video])
        merged_audio.write_audiofile("workingaudio/merged_audio.mp3")

    await asyncio.to_thread(download_video_thread, video_id)

    
# Raw Transcript Generation
async def assembly_transcript_generation(video_id, file_path):
    """
    Creates a transcript of the audio file without any processing"""
    def transcribe_audio_thread(file_path):
        transcriber = views.aai.Transcriber()
        config = views.aai.TranscriptionConfig(speaker_labels=True, speech_model="nano")
        transcript = transcriber.transcribe(file_path, config=config)
        return transcript.json_response["utterances"]
    thread_response=await asyncio.to_thread(transcribe_audio_thread, file_path)
    return thread_response


# Process Raw Transcript into transcript and linked transcript
async def process_raw_transcript(input_raw_transcript, video_id):
    """
    Parses out the speaking target initial speech segment and corrects the time offsets of the transcript.
    
    Returns a dictionary of the 'transcript' and 'linked_transcript'"""

    # make deep copy of raw transcript
    raw_transcript=copy.deepcopy(input_raw_transcript)

    # Diarization Cutoff
    diarization_cutoff=True
    if diarization_cutoff:
        def clean_speech_segment(speech_segment, diarization_word_count):
            utterances=speech_segment["words"]
            corrected_text=""
            corrected_words=[]
            corrected_text_list=[]
            corrected_start=utterances[diarization_word_count]["start"]
            for utterance in utterances[diarization_word_count:]:
                corrected_words.append(utterance)
                corrected_text_list.append(utterance["text"])

            corrected_text=" ".join(corrected_text_list)
            speech_segment["words"]=corrected_words
            speech_segment["text"]=corrected_text
            speech_segment["start"]=corrected_start
            return speech_segment

        # Words which end the speech segment for diarization targeting
        end_of_cuttof=["chief", "looks"]#["chief","looks","white."]
        #end_of_cuttof2=["chief", "looks"]
        speech_segment=raw_transcript[0]
        last_several_words=["",""]
        word_count=0
        for utterance in speech_segment["words"]:
            # check the last 3 sequence
            last_several_words=[last_several_words[1],utterance["text"]]
            word_count+=1

            # if end sequence is found
            if last_several_words==end_of_cuttof:
                print(utterance)
                print(word_count)
                print(len(speech_segment["words"]))

                # if the end sequence is NOT the end of the speech segment then destiny starts
                if (word_count+2)<len(speech_segment["words"]):
                    print("Destiny starts")
                    speech_segment=clean_speech_segment(speech_segment, word_count+1)
                    raw_transcript[0]=speech_segment
                else:
                    print("Destiny doesn't start")
                    raw_transcript=raw_transcript[1:]
                break
        print("Finished diarization cutoff")
        
        # Adjust time offsets
        def negative_fix(input_number):
            if input_number<0:
                return 0
            return input_number
        time_offset=(186*1000)+1500
        for i in range(len(raw_transcript)):
            speech_segment=raw_transcript[i]
            speech_segment["start"]=negative_fix(speech_segment["start"]-time_offset)
            speech_segment["end"]=negative_fix(speech_segment["end"]-time_offset)
            for i in range(len(speech_segment["words"])):
                speech_segment["words"][i]["start"]=negative_fix(speech_segment["words"][i]["start"]-time_offset)
                speech_segment["words"][i]["end"]=negative_fix(speech_segment["words"][i]["end"]-time_offset)
        
    # Create Base Transcript
    transcript=""
    for utterance in raw_transcript:
        speaker=utterance["speaker"]
        if speaker=="A":
            speaker="Destiny"
        transcript+=speaker+": "+utterance["text"]
        transcript+="\n\n"

    # Create Linked Transcript
    linked_transcript=""
    new_lines=0
    word_count=0
    for utterance in raw_transcript:#[0:12]:
        speaker=utterance["speaker"]
        if speaker=="A":
            speaker="Destiny"
        text=utterance["text"]
        base_link="https://www.youtube.com/watch?v={video_id}&t={time}s"
        html_transcript_text=""
        for i, word in enumerate(utterance["words"]):
            word_count+=1
            time_start=int(word["start"]/1000)
            link=f"https://youtu.be/{video_id}?t={time_start}"
            temp_text=word['text']+" "
            #</a><a href="https://www.youtube.com/watch?v=PTjCp3RJ4ag&t=5416s" target="_blank">
            if i==len(utterance["words"])-1:
                temp_text=temp_text.strip()+"\n\n"
            html_transcript_text+="<a href=\""+link+"\" target=\"_blank\" class=\"underline-hover\">"+temp_text+"</a>"

                
        linked_transcript+=speaker+": "+html_transcript_text
        linked_transcript+="<br/><br/>"
        new_lines+=2
    
    return {"transcript": transcript, "linked_transcript":linked_transcript}


# Generate vectordb and chunks for assemblyai transcript
async def assembly_generate_vectordb_and_chunks(video_id, transcript):
    """
    Saves a vectordb to the 'video_id'.index file 
    
    Creates text chunks tied to the vectordb 
    
    Returns dictionary of 'vector_db' and 'text_chunks'"""
    # Make chunks
    chunk_size=1000
    overlap=500
    text_chunks=[transcript[i:i+chunk_size] for i in range(0, len(transcript), (chunk_size-overlap))]
    print("Number of chunks: ",len(text_chunks))

    # make vector db
    async def make_vector_db_fast(openai_client, text_chunks):
        # Async function to fetch embeddings
        async def generate_embeddings_async(text_chunks, model):
            model="text-embedding-3-large"
            async def fetch_embedding(chunk):
                # Simulate an async call to the embeddings API
                #return await asyncio.to_thread(openai_client.embeddings.create, input=chunk, model=model)
                return await openai_client.embeddings.create(input=chunk, model=model)

            responses = await asyncio.gather(*(fetch_embedding(chunk) for chunk in text_chunks))
            embeddings = [response.data[0].embedding for response in responses]
            return np.array(embeddings)

        # Generate embeddings
        model="text-embedding-3-large"
        embeddings=await generate_embeddings_async(text_chunks, model)
        print("Finished generating embeddings")

        # Make vector db
        vector_db=faiss.IndexFlatL2(embeddings.shape[1])
        vector_db.add(np.array(embeddings))
        print("Finished making vector db")

        return vector_db
    
    # Make vectordb
    vector_db= await make_vector_db_fast(views.async_openai_client, text_chunks)

    # Save vector db
    if not os.path.isdir("destinyapp/vector_dbs"):
        os.mkdir("destinyapp/vector_dbs")
    faiss.write_index(vector_db, "destinyapp/vector_dbs/"+video_id+".index")
    print("Saved vector db to:", "destinyapp/vector_dbs/"+video_id+".index")
    
    # return vector db and text chunks
    return {"vector_db":vector_db, "text_chunks":text_chunks}




# # Generate Summarized Segments 
# Tester for prompting
async def generate_summarized_segments_tester(transcript, segments=150, increment_chars=10000):
    return await generate_summarized_segments(transcript, segments, increment_chars, prompt_info=2)
async def generate_summarized_segments(transcript, segments=150, increment_chars=10000, prompt_info=None):
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
        
        model_responses.append({"summary": "","transcript": input_transcript,"time_string":sf_str,"char_start_finsih_indexes":[char_start_index,char_start_index+increment_chars], "index":index, "start_second":start_second_raw, "end_second":end_second_raw})

        index+=1
        char_start_index+=increment_chars-300

    # get approximate cost of run
    input_cost=0
    output_cost=0
    prev_cost=input_cost+output_cost
    temp_input_cost=0
    temp_output_cost=0
    for m in model_responses: 
        seg_costs=calculate_cost("claude-3-sonnet-20240229", [len(enc.encode(m["transcript"])), len(enc.encode("a b c"*200))])
        temp_input_cost+=seg_costs["input"]
        temp_output_cost+=seg_costs["output"]
    print("Approximate cost: ",temp_input_cost+temp_output_cost-prev_cost, "  Number of segments: ",len(model_responses))

    async def fetch_response(input_data):
        transcript_segment=input_data["transcript"]

        # find where text appears in the transcript
        segment_index=transcript.find(transcript_segment)

        


        index=input_data["index"]

        if prompt_info!=None:
            conv_messages=[{"role":"system","content":transcript_summarization_prompt2}, {"role": "user", "content": "Transcript: "+transcript_segment}]
        else:
            conv_messages=[{"role":"system","content":transcript_summarization_prompt}, {"role": "user", "content": "Transcript: "+transcript_segment}]
        bot_response=""
        fails=0
        while True:
            if fails>5:
                print("Failed to get response for index: ",index)
                return ["",index]

            bot_response=""
            print(str(index)+" ", end="")
            try:
                model_company=ModelCompanyEnum.anthropic
                model_name=ModelNameEnum.claude_3_5_sonnet
                bot_response=await async_response_handler(
                    prompt=conv_messages,
                    modelcompany=model_company,
                    modelname=model_name,
                )
                break
            except Exception as e:
                fails+=1
                print("Error:",e,str(index)+" ", end="")
                time.sleep(10+(fails*2))
                print("Retrying:",str(index)+" ", end="")

        return [bot_response,index]
    
    # Run segmention process
    summary_responses=await asyncio.gather(*(fetch_response(in_data) for in_data in model_responses))

    # setup data to feed into model
    for i in range(len(summary_responses)):
        model_responses[i]["summary"]=summary_responses[i][0]
        print(i, model_responses[i]["index"])
    
    return model_responses


# # Generate Meta Summary
# Tester for prompting
async def generate_meta_summary_tester(summarized_chunks, video_id=None):
    return await generate_meta_summary(summarized_chunks, video_id, prompt_info=2)
async def generate_meta_summary(summarized_chunks, video_id=None,prompt_info=None, bias_injection_bool=False):
    """
    Takes in list of dictionaries with 'summary' field and generates a meta summary
    
    Returns string of the meta summary."""
    
    all_summaries=""
    for mr in summarized_chunks:
        #all_summaries+=mr["time_string"]+"\n"+mr["summary"]+"\n\n"
        all_summaries+=mr["summary"]+"\n\n"
    #print(all_summaries)

    # print expected cost and ask if user wants to proceed
    print("Expected cost: ",len(enc.encode(all_summaries))*(3/1000000.0))
    if True:
        # meta_model_prompt="Your purpose is to take a conglomerate of summaries and compile it into one conglomerate which provides a comprehensive and effective way of knowing what things were talked about in the collection of summaries. The summaries are off of a youtube video transcript of a youtube streamer named Destiny. You should do two parts, main or big topics that were talked about as a main focus or for a long period and another section of smaller details or topic that were covered briefly. These should be two large sections, each may be 300-500 words. In total you need to write around 1000 words. Be sure to include a lot of detail and be comprehensive to get to that 1000 word mark."
        meta_model_prompt="Your purpose is to take a conglomerate of summaries and compile it into one conglomerate which provides a comprehensive and effective way of knowing what things were talked about in the collection of summaries. The summaries are off of a youtube video transcript of a youtube streamer named Destiny. You should do two parts, main or big topics that were talked about as a main focus or for a long period and another section of smaller details or topic that were covered briefly. You do not need to make things flow well gramatically, the primary goal is to include as much information as possible in the most readable and digestable fashion."
        
        if prompt_info:
            meta_model_prompt="""Your purpose is to take a conglomerate of summaries and compile it into one conglomerate which provides a comprehensive and effective way of knowing what things were talked about in the collection of summaries. The summaries are off of a youtube video transcript of a youtube streamer named Destiny. You should do two parts, main or big topics that were talked about as a main focus or for a long period and another section of smaller details or topic that were covered briefly. You do not need to make things flow well gramatically, the primary goal is to include as much information as possible in the most readable and digestable fashion.
            
            USE MARKDOWN FOR READABILITY. Be clever with your markdown to make the summary more readable. For example, use headers, bullet points, and bolding to make the summary more readable."""
        

        #These should be two large sections, each may be 300-500 words. In total you need to write around 1000 words. Be sure to include a lot of detail and be comprehensive to get to that 1000 word mark."

        if bias_injection_bool:
            bias_injection="Some information about me the user, I like technology, specifically software but technology generally, I am interested in full democracy, I am probably a bit right leaning and am curious about critiques to conservative views, I am curious about science, and I enjoy humor. "
            if bias_injection!="":
                meta_model_prompt+=" If the user states information about them, cater the summary to their interests."

        # Meta summary
        model_company=ModelCompanyEnum.anthropic
        model_name=ModelNameEnum.claude_3_5_sonnet
        if prompt_info:
            model_company=ModelCompanyEnum.openai
            model_name=ModelNameEnum.gpt_4o

        if bias_injection_bool:
            prompt=[{"role":"system","content":meta_model_prompt},{"role":"user", "content": bias_injection+"Collection of summaries for the video/transcript: "+all_summaries}]
        else:
            prompt=[{"role":"system","content":meta_model_prompt},{"role":"user", "content": "Collection of summaries for the video/transcript: "+all_summaries}]
        
        bot_response=await async_response_handler(
            prompt=prompt,
            modelcompany=model_company,
            modelname=model_name,
        )

        return bot_response
    else:
        return ""
    
# # Generate hook for recap
async def generate_recap_hook(recap, video_title=None, version_select=None):
    model_company=ModelCompanyEnum.anthropic
    model_name=ModelNameEnum.claude_3_5_sonnet
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

    bot_response=await async_response_handler(
        prompt=prompt,
        modelcompany=model_company,
        modelname=model_name,
    )

    try:
        hook=bot_response.split("ENTICEMENT:")[-1].strip()
    except Exception as e:
        print("ERROR MAKING HOOK: ",e)
        hook=""

    return hook












# # SEARCH FUNCTIONS
# vector search transcript
async def search_vectordb(vector_db, query):
    """
    Searches given vectordb with query
    
    Returns tuple of 'D' and 'I'"""
    # Generate query embedding
    query_embedding = await views.async_openai_client.embeddings.create(input=query,model="text-embedding-3-large")
    query_embedding_np = np.array(query_embedding.data[0].embedding).astype('float32').reshape(1, -1)
    k=vector_db.ntotal
    if k>5:
        k=5

    D, I = vector_db.search(query_embedding_np, k)
    return (D,I)
