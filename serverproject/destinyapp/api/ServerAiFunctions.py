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
from pytube import YouTube
import re
from bs4 import BeautifulSoup


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
    claude_3_haiku = "claude-3-haiku-20240307"
class ModelCostEnum(str, Enum):
    gpt_4_turbo = {"input": 10/1000000.0, "output": 30/1000000.0}
    gpt_4o = {"input": 5/1000000.0, "output": 20/1000000.0}
    gpt_3_5_turbo = {"input": 1/1000000.0, "output": 8/1000000.0}
    claude_3_5_sonnet = {"input": 3/1000000.0, "output": 15/1000000.0}
    claude_3_sonnet = {"input": 3/1000000.0, "output": 15/1000000.0}
    claude_3_opus = {"input": 10/1000000.0, "output": 60/1000000.0}
    claude_3_haiku = {"input": 0.25/1000000.0, "output": 1.25/1000000.0}


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
def calculate_cost(model_name, input="", output=""):
    # get the cost rates for the model name
    for model_enum_name in ModelNameEnum:
        if model_name==model_enum_name.value:
            cost_rate = ModelCostEnum[model_enum_name.name].value
            cost_rate=eval(cost_rate)

            input_cost = len(enc.encode(input)) * cost_rate["input"]
            output_cost = len(enc.encode(output)) * cost_rate["output"]
            # print(input_cost, output_cost, len(input), len(output))
            # return {"input": input_cost, "output": output_cost}
            cost=input_cost+output_cost
            return cost
    
    return 0























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
# Determine if video is live
async def get_live_status(yt_id):
    # Get video
    url = 'https://www.youtube.com/watch?v='+yt_id
    yt = YouTube(url)

    # Fill attributes
    try:
        for attr in dir(yt):
            value=getattr(yt, attr)
    except Exception as e:
        pass

    # Get Live status
    try:
        vid_info=getattr(yt, "_vid_info")
        live_bool=vid_info["videoDetails"]["isLive"]
    except Exception as e:
        live_bool=False
    return live_bool

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
        print("download thread finished")
        return

    await asyncio.to_thread(download_video_thread, video_id)
    print("download thread closed")

    
# Raw Transcript Generation
async def assembly_transcript_generation(video_id, file_path):
    """
    Creates a transcript of the audio file without any processing"""
    def transcribe_audio_thread(file_path):
        transcriber = views.aai.Transcriber()
        # config = views.aai.TranscriptionConfig(speaker_labels=True, speech_model="nano")
        config = views.aai.TranscriptionConfig(speaker_labels=True, speech_model="best")
        transcript = transcriber.transcribe(file_path, config=config)
        return transcript.json_response["utterances"]
    print("Starting assembly transcription thread")
    thread_response=await asyncio.to_thread(transcribe_audio_thread, file_path)
    print("Finished assembly transcription thread")
    return thread_response

# Raw Transcript Generation
async def testing_assembly_transcript_generation(video_id, file_path):
    """
    Creates a transcript of the audio file without any processing"""
    def transcribe_audio_thread(file_path):
        transcriber = views.aai.Transcriber()
        config = views.aai.TranscriptionConfig(speaker_labels=True, speech_model="nano")
        # config = views.aai.TranscriptionConfig(speaker_labels=True, speech_model="best")
        transcript = transcriber.transcribe(file_path, config=config)
        return transcript.json_response["utterances"]
    print("Starting assembly transcription thread")
    thread_response=await asyncio.to_thread(transcribe_audio_thread, file_path)
    print("Finished assembly transcription thread")
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


class vectordb_and_text_chunks_generator:
    model_company=ModelCompanyEnum.anthropic
    model_name=ModelNameEnum.claude_3_haiku
    text_chunk_summary_batch_prompt="""You will be given a transcript that is broken down into segments and you must give a overview and a 1-2 sentence summary for each text segment, label the segments with a number like (1.) and then give the overview and summary. No more than 200 characters per segment. The segments are from a youtube streamer named Destiny. The overview should be a general idea that you would present to someone as a topic. The summary should have more detail, like 2 sentences.

The overview is meant to be used by a vector embedding model to allow users to search for the spot something happened in from the transcript. People are going to search topics from a recap provided to them which is the need for this.

Here is an example of a segment and the overview and summary:
Text Segment: This says someone was assaulted with a cigarette and had burns on their body. They were attacked after getting into an argument with a customer. What is this, Jesus. Why are people so unhinged. Is there any proof of this story or is this just some random person saying something. 
Overview: Discussion of alleged cigarette burns and injuries in an unverified story.
Summary: A person was allegedly assaulted with a cigarette and had burns on their body after an argument with a customer. The story is unverified and the speaker questions the validity of the story.


    
Here is an example of the formatting:
"
(1.) Overview:
Summary:

(2.)Overview:
Summary:
...

When generating the points it should be from the context of the text segments provided by the user, generate for every single segment in the context provided.
"""

    async def text_chunk_summary_batch(text_batch, sys_prompt=text_chunk_summary_batch_prompt, model_name=model_name, model_company=model_company):
        prompt=[{"role":"system","content":sys_prompt}, {"role": "user", "content": "Here are the text segments: "+text_batch}]
        response_str=await async_response_handler(
            prompt=prompt,
            modelcompany=model_company,
            modelname=model_name,
        )

        cost=calculate_cost(model_name, prompt[0]["content"]+prompt[1]["content"], response_str)

        return response_str, cost


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
    model_company=ModelCompanyEnum.anthropic
    model_name=ModelNameEnum.claude_3_5_sonnet

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

    # get approximate cost of run
    input_cost=0
    output_cost=0
    prev_cost=input_cost+output_cost
    temp_input_cost=0
    temp_output_cost=0
    temp_cost=0
    for m in model_responses: 
        temp_cost+=calculate_cost(model_name, m["transcript"], "a b c"*200)
    print("Approximate cost: ",temp_cost, "  Number of segments: ",len(model_responses))

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

class summarized_segment_generator:
    
        model_company=ModelCompanyEnum.anthropic
        model_name=ModelNameEnum.claude_3_5_sonnet

        summarization_prompt="Your purpose is to take a transcript from a youtube streamer named Destiny and give a synopsis of the content and the sentiment/takes of the speaker. Include all of the topics even if they are covered briefly instead of just covering the main topic."

        long_summarization_prompt="""Your purpose is to take a transcript from a youtube streamer named Destiny and give a synopsis of the content and the sentiment/takes of the speaker. Include all of the topics even if they are covered briefly instead of just covering the main topic although you should do that as well. The main topic or seeming focus of the segment and all of the things said or discussed. This should be quite long.
        
FYI: The transcript is diarized, Destiny should be annotated 'Destiny' with other speaker being a default from the transcription engine like b, c, d ... etc. You may have to use some intuition to figure out what is happening."""
        summarization_prompt=long_summarization_prompt

        long_summarization_prompt="""You are given a transcript from a youtube stream focused on a streamer named Destiny. The transcript is diarized, Destiny should be annotated 'Destiny' with other speaker being a default from the transcription engine like b, c, d ... etc. You may have to use some intuition to figure out what is happening because Destiny may say something but he is reading chat or he may be watching something and it may look like he is in a conversation when he is just reacting or he might actually be talking with or debating someone.
         
Your job is to create an excellent summary of the segment of the transcript given to you. This can be done in two parts, main focus and all topics. Include all of the topics even if they are covered briefly because it helps build a full sense of what happened. It is also important to know the majority of what happened and what was happening in the segment in general. This should be quite long, try to get into the specifics, that is where the value is."""


        async def generate_summarized_segments(transcript, segments=150, increment_chars=10000, model_name=model_name, model_company=model_company, summarization_prompt=summarization_prompt):
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

            # get approximate cost of run
            input_cost=0
            output_cost=0
            prev_cost=input_cost+output_cost
            temp_input_cost=0
            temp_output_cost=0
            temp_cost=0
            for m in model_responses: 
                temp_cost+=calculate_cost(model_name, m["transcript"], "a b c"*200)
            print("Approximate cost: ",temp_cost, "  Number of segments: ",len(model_responses))

            async def fetch_response(input_data):
                transcript_segment=input_data["transcript"]

                # find where text appears in the transcript
                segment_index=transcript.find(transcript_segment)

                


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
                        bot_response=await async_response_handler(
                            prompt=conv_messages,
                            modelcompany=model_company,
                            modelname=model_name,
                        )
                        cost=calculate_cost(model_name, conv_messages[0]["content"]+conv_messages[1]["content"], bot_response)
                        break
                    except Exception as e:
                        fails+=1
                        print("Error:",e,str(index)+" ", end="")
                        time.sleep(10+(fails*2))
                        print("Retrying:",str(index)+" ", end="")

                return [bot_response,index, cost]
            
            # Run segmention process
            summary_responses=await asyncio.gather(*(fetch_response(in_data) for in_data in model_responses))

            # setup data to feed into model
            total_cost=0
            for i in range(len(summary_responses)):
                model_responses[i]["summary"]=summary_responses[i][0]
                print(i, model_responses[i]["index"])
                total_cost+=summary_responses[i][2]
            print("Total cost: ",total_cost)
            
            return model_responses
    
        


# # Generate Meta Summary
# Tester for prompting
async def generate_meta_summary_tester(summarized_chunks, video_id=None):
    return await meta_summary_generator.generate_meta_summary(summarized_chunks, video_id, prompt_info=2)

class meta_summary_generator:

    model_company=ModelCompanyEnum.anthropic
    model_name=ModelNameEnum.claude_3_5_sonnet

    meta_model_prompt="Your purpose is to take a conglomerate of summaries and compile it into one conglomerate which provides a comprehensive and effective way of knowing what things were talked about in the collection of summaries. The summaries are off of a youtube video transcript of a youtube streamer named Destiny. You should do two parts, main or big topics that were talked about as a main focus or for a long period and another section of smaller details or topic that were covered briefly. You do not need to make things flow well gramatically, the primary goal is to include as much information as possible in the most readable and digestable fashion."

    meta_model_prompt="""Your purpose is to take a conglomerate of summaries and compile it into one conglomerate which provides a comprehensive and effective way of knowing what things were talked about in the collection of summaries. The summaries are off of a youtube video transcript of a youtube streamer named Destiny. You should do two parts, main or big topics that were talked about as a main focus or for a long period and another section of smaller details or topic that were covered briefly. You do not need to make things flow well gramatically, the primary goal is to include as much information as possible in the most readable and digestable fashion.
                
USE MARKDOWN FOR READABILITY. Be clever with your markdown to make the summary more readable. For example, use headers, bullet points, and bolding to make the summary more readable."""

    html_sytem="""Your purpose is to take a conglomerate of summaries and compile it into one conglomerate which provides a comprehensive and effective way of knowing what things were talked about in the collection of summaries. The summaries are off of a youtube video transcript of a youtube streamer named Destiny. You should do two parts, main or big topics that were talked about as a main focus or for a long period and another section of smaller details or topic that were covered briefly. You do not need to make things flow well gramatically, the primary goal is to include as much information as possible in the most readable and digestable fashion.
                
USE HTML FOR READABILITY. Be clever with your HTML to make the summary more readable. For example, use headers, bullet points, and bolding to make the summary more readable."""

    user_prompt="Collection of summaries for the video/transcript: "

    async def generate_meta_summary(summarized_chunks=None, model_name=model_name, model_company=model_company, meta_model_prompt=html_sytem, bias_injection_bool=False, bias_injection="",user_prompt=user_prompt):
        """
        Takes in list of dictionaries with 'summary' field and generates a meta summary
        
        Returns string of the meta summary."""

        # Standard
        all_summaries=""
        for mr in summarized_chunks:
            all_summaries+=mr["summary"]+"\n\n"
        # print expected cost and ask if user wants to proceed
        print("Expected cost: ",len(enc.encode(all_summaries))*(3/1000000.0))

        # if bias_injection_bool:
        #     bias_injection="Some information about me the user, I like technology, specifically software but technology generally, I am interested in full democracy, I am probably a bit right leaning and am curious about critiques to conservative views, I am curious about science, and I enjoy humor. "
        #     if bias_injection!="":
        #         meta_model_prompt+=" If the user states information about them, cater the summary to their interests."

        # if bias_injection_bool:
        #     prompt=[{"role":"system","content":meta_model_prompt},{"role":"user", "content": bias_injection+"Collection of summaries for the video/transcript: "+all_summaries}]
        # else:
        #     prompt=[{"role":"system","content":meta_model_prompt},{"role":"user", "content": "Collection of summaries for the video/transcript: "+all_summaries}]

        prompt=[{"role":"system","content":meta_model_prompt},{"role":"user", "content": user_prompt+all_summaries}]
        
        bot_response=await async_response_handler(
            prompt=prompt,
            modelcompany=model_company,
            modelname=model_name,
        )

        return bot_response
    

class recap_zoomed_in_generator:

    model_company=ModelCompanyEnum.anthropic
    model_name=ModelNameEnum.claude_3_5_sonnet
    zoom_generator_model_name=ModelNameEnum.claude_3_haiku

    system_prompt="""Your goal is to take a stream recap and the summaries that were used to constitute the recap and create extra detail for the line items of the recap. The recap has two sections, a main topics section and a smaller topics section. You must recommend a summary chunks that could be used to make a more detailed pane for each of these line items. The summaried chunks will be numbered like '(Summary Chunk X.)'
    
When giving the chunks for each topic or thing it is important to be able to tie a key to the thing so that which one you are talking about can be parsed. To do this for the main topics you should take the title and use that title to be the key, for the smaller details you should take the list item and use that. Here is what that might look like this:
"Large topics: 
<'Watching Basketball': 0, 3>
<'Debating about gun control': 4, 7, 8>

Smaller topics:
<'Thoughts on chat drama': 3>
"""

    system_prompt="""Your goal is to take a stream recap and the summaries that were used to constitute the recap and create extra detail for the line items of the recap. The recap has two sections, a main topics section and a smaller topics section. You must recommend a summary chunks that could be used to make a more detailed pane for each of these line items. The summaried chunks will be numbered like '(Summary Chunk X.)'
    
When giving the chunks for each topic or thing it is important to be able to tie a key to the thing and have the context of it so that which one you are talking about can be parsed. To do this for the main topics you should take the title and use that title to be the key for the chunks. For the main topics you should also include the content under the title if there are bullets under that title. For the smaller details you should take the list item and use that. Here is what that might look like this:
"Large topics: 
{{{"Watching Basketball": [0, 3], "content": ["<strong>Watching Basketball</strong> Debating about the NBA and the players", "<strong>Watching Basketball</strong> Reacting to clips of basketball games"]}}}
{{{"Debating about gun control": [4, 7, 8], "content": ["<strong>Weapon modification</strong> Debating about bump stocks and other modifications and the impact", "<strong>Gun control</strong> Debating about the effectiveness of gun control"]}}}

Smaller topics:
{{{"Thoughts on chat drama": [3],  "content": ["<strong>Chat drama</strong> Reacting to chat drama"]}}}
"""

    zoom_prompt="""You are giving selected chunks of a youtube transcript and your purpose is to pull out a description of the topics given with respect to what is seen in the transcript. Basically the stream was recapped with bullet points and now you are filling out a more detailed description for those titles and bullet points. What you generated should be more paragraph style than bullet point style.

Try to use as much literal detail from the transcript about what was said or done, don't use any fluff. Your response doesn't need to flow well as long as you are able to concisely provide accurate and in-depth information about the subject matter. Always get right into, no introduction.

Do not analyize the content or speak on what the conclusion is just simply report what was said or done in the transcript."""
    zoom_prompt="""You are giving selected chunks of a youtube transcript and your purpose is to pull out a description of the topics given with respect to what is seen in the transcript. Basically the stream was recapped with bullet points and now you are filling out a more detailed description for those titles and bullet points. What you generated should be more paragraph style than bullet point style.

The only thing you can speak about is actually what was said or what happened, no other commentary is allowed. Be as concise as possible and as detailed as possible in what you include, quotes are encouraged."""

    zoom_prompt="""You are to give the most unbiased and detailed description of the topic as possible and nothing else. No bullet points, no lists. NEVER BE IN FAVOR OR AGAINST ANYTHING MENTIONED YOUR TAKE IS NOT WARRANTED."""#BE EXTREMELY GOOFY IN THE RESPONSE THOUGH THIS IS A REQUIREENT."""

    zoom_prompt="""You are to give a 0 fluff, 0 emotion, 0 opinion paragraph. A singular paragraph. This can be long so include quotes and get as close to the transcript as possible. NO INTRO, JUST PARAGRAPH, NO BULLETPOINTS NO LIST."""# This should aim to be longer rather than shorter."""


    reformat_prompt="""You are a recap reformatter, you will need to take the context of a recap and use the topic and zoom pairs to create a list of dictionaries for [{'title': title, 'summary':original_content, 'zoom':zoom_content}]
    
For each of those items (title, original_content, zoom_content) those strings of html should be in tripple quotation marks."""

    async def reformat_recap(recap, topic_prompts, zooms, reformat_prompt=reformat_prompt, model_name=model_name, model_company=model_company):

        reformat_task_prompts=[]
        for topic_prompt, zoom in zip(topic_prompts, zooms):
            reformat_task_prompt=f"""
--------------------------------
Topic: {topic_prompt}
Zoom: {zoom}
--------------------------------
"""
            reformat_task_prompts.append(reformat_task_prompt)

        reformat_tasks_prompt="\n".join(reformat_task_prompts)
            

        prompt=[{"role":"system","content":reformat_prompt},{"role":"user", "content": f"Here is the recap: {recap}\n\nHere are the pairs of sections and zoom: {reformat_tasks_prompt}"}]

        bot_response=await async_response_handler(
            prompt=prompt,
            modelcompany=model_company,
            modelname=model_name,
        )

        return bot_response

    @classmethod
    async def generate_zoom(cls, topic_prompt_str, transcript_chunks_str, model_name=zoom_generator_model_name, model_company=model_company, zoom_prompt=zoom_prompt):

        prompt=[{"role":"system","content":zoom_prompt},{"role":"user", "content": f"Here is the transcript data to look at {transcript_chunks_str}\n\nHere is your only focus, you must cover directly on these topics as a category, imagine someone asked you a question with respect to the direction of these topics: {topic_prompt_str}"}]

        prompt=[{"role":"system","content":zoom_prompt},{"role":"user", "content": f"Here is the transcript data to look at {transcript_chunks_str}\n\nMake a paragraph on this that is your only focus: {topic_prompt_str}"}]

        cost=0
        cost+=calculate_cost(model_name, input=(prompt[0]["content"]+prompt[1]["content"]))
        
        bot_response=await async_response_handler(
            prompt=prompt,
            modelcompany=model_company,
            modelname=model_name,
        )
        cost+=calculate_cost(model_name, output=bot_response)
        
        return bot_response, cost
    
    @classmethod
    async def generate_all_zooms(cls, topic_prompts, transcript_chunks_prompts, model_name=zoom_generator_model_name, model_company=model_company, zoom_prompt=zoom_prompt):
        tasks=[]
        for i, (topic_prompt, transcript_chunks_str) in enumerate(zip(topic_prompts, transcript_chunks_prompts)):
            tasks.append(cls.generate_zoom(topic_prompt, transcript_chunks_str, model_name=model_name, model_company=model_company, zoom_prompt=zoom_prompt))
        
        results=await asyncio.gather(*tasks)
        zooms=[]
        costs=0
        for result in results:
            zooms.append(result[0])
            costs+=result[1]
        print(costs)
        return zooms

    def prepare_zoom_inputs(summarized_chunks, chunk_annotations_str):
        # Turn annotation string into list of dictionaries
        pattern=re.compile(r'\{\{\{.*?\}\}\}')
        chunk_annotations_temp=pattern.findall(chunk_annotations_str)
        chunk_annotations_temp=[chunk_annotation.replace("{{{", "{").replace("}}}", "}") for chunk_annotation in chunk_annotations_temp]
        chunk_annotations=[]
        for chunk_annotation in chunk_annotations_temp:
            chunk_annotations.append(json.loads(chunk_annotation))

        # turn summarized chunks into prompt contexts
        topic_prompts=[]
        transcript_chunks_prompts=[]
        for chunk_annotation in chunk_annotations:
            # get topic prompt and chunk indexes for transcript prompt
            temp_prompt_str=""
            chunk_indexes=[]
            for key, value in chunk_annotation.items():
                if key=="content":
                    temp_prompt_str+="\n"+", ".join(value)
                else:
                    chunk_indexes=value
                    temp_prompt_str+=key
            topic_prompts.append(temp_prompt_str)
            
            # get transcript prompt from the indexes
            temp_transcript_str=""
            for chunk_index in chunk_indexes:
                temp_transcript_str+=summarized_chunks[chunk_index]["transcript"]+"\n\n"
            transcript_chunks_prompts.append(temp_transcript_str)

        return chunk_annotations, topic_prompts, transcript_chunks_prompts
        
    async def annotate_zoom_chunks(summaized_chunks, recap, model_name=model_name, model_company=model_company, system_prompt=system_prompt):
        """Takes in list of dictionaries with 'summary' field and generates a zoomed in recap
        
        Returns string of the zoomed in recap."""
        # Standard
        all_summaries=""
        i=0
        for mr in summaized_chunks:
            all_summaries+=f"(Summary Chunk {i})."+mr["summary"]+"\n\n"
            i+=1
        # print expected cost and ask if user wants to proceed
        print("Expected cost: ",len(enc.encode(all_summaries))*(3/1000000.0))

        # if bias_injection_bool:
        #     bias_injection="Some information about me the user, I like technology, specifically software but technology generally, I am interested in full democracy, I am probably a bit right leaning and am curious about critiques to conservative views, I am curious about science, and I enjoy humor. "
        #     if bias_injection!="":
        #         meta_model_prompt+=" If the user states information about them, cater the summary to their interests."

        # if bias_injection_bool:
        #     prompt=[{"role":"system","content":meta_model_prompt},{"role":"user", "content": bias_injection+"Collection of summaries for the video/transcript: "+all_summaries}]
        # else:
        #     prompt=[{"role":"system","content":meta_model_prompt},{"role":"user", "content": "Collection of summaries for the video/transcript: "+all_summaries}]

        prompt=[{"role":"system","content":system_prompt},{"role":"user", "content": "Collection of summaries for the video/transcript: "+all_summaries+"\n\nRecap: "+recap}]
        
        bot_response=await async_response_handler(
            prompt=prompt,
            modelcompany=model_company,
            modelname=model_name,
        )

        return bot_response
    



    
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





















































# # TEST FUNCTIONS
# send a discord message in test channel
import discord
async def discord_test(test_message):
    class MessageSendingClient(discord.Client):
        async def on_ready(self):
            async def send_message(message_str):
                start_index=0
                recap_chunks={}
                recap_chunks["start_finish"]=[0]
                recap_chunks["segments"]=[]
                increment_size=1500

                # increment for the number of segments needed
                for i in range((len(message_str)//increment_size)+1):
                    
                    # find the the reasonable end of the segment
                    finish_index=start_index+increment_size
                    if finish_index>=len(message_str):
                        finish_index=None
                    else:
                        while message_str[finish_index]!="\n":
                            finish_index+=1
                            if (finish_index-start_index)>2100:
                                print("Didn't find a newline")
                                break
                            if finish_index>=len(message_str):
                                finish_index=None
                                break
                    
                    # append the segments to the list
                    recap_chunks["segments"].append(message_str[start_index:finish_index])
                    start_index=finish_index
                    recap_chunks["start_finish"].append(start_index)

                for recap_chunk in recap_chunks["segments"]:
                    await channel.send(recap_chunk)
            
            try:
                channels=self.get_all_channels()
                for channel in channels:
                    print(channel.name)
                    if channel.name=="test":
                        if channel:
                            await send_message(test_message)
                            # await channel.send(test_message)
                await self.close()
            except Exception as e:
                print("Error: ",e)
                await self.close()
    
    try:
        intents = discord.Intents.default()
        intents.messages = True 
        client = MessageSendingClient(intents=intents)

        await client.start(views.keys["discord"])

        return "Completed"
    except Exception as e:
        print("Error: ",e)
        return e
    



# chat processing


# linked transcript has links on almost everything so to get the link at a given character count we must go throught hte nodes and count the characters
def get_time_at_char_count(char_count, linked_transcript):

    #example of linked_transcript: <a href="https://youtu.be/23K0euDg0FU?t=201" target="_blank">What\'s </a><a href="https://youtu.be/23K0euDg0FU?t=202" target="_blank">this? </a>
    # Initialize BeautifulSoup with the linked transcript
    soup = BeautifulSoup(linked_transcript, 'html.parser')
    
    # Track the cumulative count of characters processed
    cumulative_count = 0

    temp_time=""
    
    # Iterate through each <a> tag in the transcript
    for link in soup.find_all('a'):
        # Text inside the current <a> tag
        link_text = link.get_text()
        
        # Update the cumulative count of characters by adding the length of the current link's text
        cumulative_count += len(link_text)
        
        # Check if the cumulative character count has reached or exceeded the specified character count
        if link.get('href') is not None:
            temp_time=link['href'].split("t=")[-1].split("s")[0]
        if cumulative_count >= char_count:
            # Return the URL (href attribute) of the current <a> tag
            return temp_time 
        
    print("Cumulative count", cumulative_count)
    # If no link is found at the specified character count, return None
    return temp_time

def get_chats_in_start_end(simplified_messsages ,start_time=0,end_time=1):
    chats_in_segment_dict={}
    chats_in_segment=[]
    chats_txt=""
    chats_txt_numbered=""
    chat_before_end=True
    i=0
    chat_num=0
    while chat_before_end:
        try:
            # Get chat time
            chat_msg_time=simplified_messsages[i]["time"]
            if chat_msg_time.count(":")==1:
                chat_time=datetime.datetime.strptime(chat_msg_time, '%M:%S')
                chat_time=chat_time.minute*60+chat_time.second
            else:
                chat_time=datetime.datetime.strptime(chat_msg_time, '%H:%M:%S')
                chat_time=chat_time.hour*3600+chat_time.minute*60+chat_time.second
            
            if (chat_time>end_time) or (chat_num>len(simplified_messsages)):
                chat_before_end=False
            elif chat_time>start_time:
                #print(all_chat_messages[i])
                chats_in_segment.append(simplified_messsages[i])
                # chats_in_segment_dict[str(chat_num)]=simplified_messsages[i]
                # chats_txt+=simplified_messsages[i]+"\n"
                # chats_txt_numbered+=str(chat_num)+": "+simplified_messsages[i]+"\n"
                chat_num+=1

        except Exception as e:
            pass
            #print("Error", e)
        i+=1

        if i>len(simplified_messsages):
            chat_before_end=False

    print(len(chats_in_segment))
    return chats_in_segment



async def analyze_chat(segment_summary, chats_txt):
    chat_summary_prompt="""The user will give you a chat log and transcript summary over a certain period of a livestream and you will parse out serious chat messages. You will do this by going over each number and saying yes or no for each, yes if serious and no if not. Here is an example of the formatting for your response: 0: no-(a word 1 word description as to what it is)\n1: yes-(brief description)\n...
    
At the end of this process you will need to mention the non serious messages. Start this line with 'Non serious messages: ', this section should explicitly state what people are thinking with examples, be as accurate and precise with the sentiment as you can be, sometimes they can be a little bit toxic but it is ok to represent that accurately. VAUGE AND GENERAL DESCRIPTIONS ARE NOT ACCEPTABLE."""
    # chat_summary_prompt="The user will give you a chat log and transcript summary over a certain period of a livestream and you will parse out serious chat messages. You will do this by going over each number and saying yes or no for each, yes if serious and no if not. Here is an example of the formatting for your response: 0: no\n1: yes\n..." 

    user_prompt="Here is the transcript summary: {transcript_summary}\n\nHere is the chat: {chat}\n\nThere are {number} chat messages and you must annotate all of them with yes or no."
    #f_user_prompt=user_prompt.format(transcript_summary=transcript_segment["bot"], chat=chats_txt)


    prompt=[{"role":"system","content":chat_summary_prompt},{"role":"user", "content": user_prompt.format(transcript_summary=segment_summary, chat=chats_txt,number=len(chats_txt.split("\n")))}]

    model_company=ModelCompanyEnum.anthropic
    model_name=ModelNameEnum.claude_3_haiku

    chats_number_response=await async_response_handler(prompt, model_company, model_name)

    print(calculate_cost(model_name, prompt[0]["content"]+prompt[1]["content"], chats_number_response))

    return chats_number_response


















# Stream Visualizer
class stream_visualizer:
    model_company=ModelCompanyEnum.anthropic
    model_name=ModelNameEnum.claude_3_5_sonnet
    system_prompt="""You annotate where segments of a stream are. 
    
The user will give you a recap (like a summary) of a stream and the transcript for that stream.

You must take the recap, go through each item/topic in it, and denote where in the transcript that item begins and ends. To do this you must give the item then about 10 words that start the item/topic and then the 10 words that end the item/topic. 

This will be programmatically parsed to create segments. """

    async def annotate_segments(meta, transcript,system_prompt=system_prompt, model_name=model_name, model_company=model_company):
        prompt=[{"role":"system","content":system_prompt},{"role":"user", "content": "This is the recap: "+meta+"\n\n\nThis is the transcript: "+transcript+"\n\nYou must take the recap, go through each item/topic in it, and denote where in the transcript that item begins and ends. To do this you must give the item then about 10 words that start the item/topic and then the 10 words that end the item/topic. "}]
        bot_response=await async_response_handler(
            prompt=prompt,
            modelcompany=model_company,
            modelname=model_name,
        )

        return bot_response, calculate_cost(model_name, prompt[0]["content"]+prompt[1]["content"], bot_response), prompt
    