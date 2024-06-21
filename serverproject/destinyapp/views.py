from django.shortcuts import render
import os
import requests
import aiohttp
import re
import json
import asyncio
from asgiref.sync import sync_to_async
import time
import faiss
from django.http import HttpResponseRedirect
from django.http import JsonResponse
import datetime
from pathlib import Path
import traceback
from chat_downloader import ChatDownloader
from pytube import YouTube

# webdriver on vyneer website
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# discord imports
import discord
from discord.ext import commands


# import Response
from rest_framework.response import Response


# Import custom modules
from .api import ServerAiFunctions as saf
from destinyapp.models import TranscriptData, BotData


# Get keys and create clients
import openai
from openai import AsyncOpenAI
import anthropic
from anthropic import AsyncAnthropic
import assemblyai as aai

import dotenv

# # Load the .env file
# dotenv.load_dotenv()


# Setup Keys
if os.path.exists(r"D:\PROGRAMS\DestinyFolder\DestinyAIBot\local\working_folder\keys.json"):
    keys=json.load(open(r"D:\PROGRAMS\DestinyFolder\DestinyAIBot\local\working_folder\keys.json"))
if os.path.exists(os.path.join(Path(os.getcwd()).parent, "keys.json")):
    keys=json.load(open(os.path.join(Path(os.getcwd()).parent, "keys.json")))
openai_client=openai.OpenAI(api_key=keys['openai'])
async_openai_client=AsyncOpenAI(api_key=keys['openai'])
anthropic_client=anthropic.Anthropic(api_key=keys['anthropic'])
async_anthropic_client=AsyncAnthropic(api_key=keys['anthropic'])
discord_key=keys['discord']
aai.settings.api_key = keys['assemblyai']
print("Keys loaded")






# # MISC FUNCTIONS
# delete all transcript data, delete_enabled has to be set in keys.json
async def delete_transcripts(request):
    if keys.get("delete_enabled",False):
        request_data=request.GET.get("mra")
        if (request_data==keys["req_pass"]):
            print("Deleting all data")
            # delete all data
            all_data=await saf.get_all_data()
            for data in all_data:
                await sync_to_async(data.delete)()
                print("deleted: ",data.video_id)
            return JsonResponse({"response":"delted all data"})
        else:
            print("Delete request denied")
    else:
        print("Delete not enabled")

    return JsonResponse({"response":"Operation not eceuted"})








# # RECAPS GENERATOR FUNCTIONS
# Auto recaps generator
async def auto_recaps_generator(request):
    # Get form data from request
    print("Request:",request)
    request_data=request.GET.get("mra")
    if not (request_data==keys["req_pass"]):
        print("Wrong password: ", request_data)
        return(JsonResponse({}))
    
    # time to wait between requests
    ran_wait_time=36
    # ran_wait_time=5

    # check if the bot has ran within the hour
    bot_data=await sync_to_async(BotData.objects.filter)(bot_id="baseid")
    existing_bot_data=await sync_to_async(bot_data.exists)()
    if existing_bot_data:
        bot_data=await sync_to_async(BotData.objects.get)(bot_id="baseid")
    if existing_bot_data and (bot_data.last_time_ran!=""):
        time_now_str=str(datetime.datetime.now())
        bot_last_ran_str=bot_data.last_time_ran

        # if the bot has ran within the hour then return
        parsed_time_now_str=time_now_str.split(".")[0]
        parsed_bot_last_ran_str=str(bot_last_ran_str).split(".")[0]

        #if the seconds are within 3600
        if (datetime.datetime.strptime(parsed_time_now_str, "%Y-%m-%d %H:%M:%S")-datetime.datetime.strptime(parsed_bot_last_ran_str, "%Y-%m-%d %H:%M:%S")).seconds<ran_wait_time:
            return JsonResponse({"response":"Bot already ran within the hour"})
        else:
            bot_data.last_time_ran=time_now_str
            save_function=bot_data.save
            await sync_to_async(save_function)()
    else:
        # create and save the bot data with the current time if the bot data doesn't exist
        bot_data=BotData(bot_id="baseid",last_time_ran=str(datetime.datetime.now()))
        save_function=bot_data.save
        await sync_to_async(save_function)()



    print("Starting Recap Generations")
    pattern = r"https://youtu.be/([\w-]+)"


    # Get the youtube ids
    web_check=keys.get("web_check",False)
    if web_check:
        # Create a Chrome Options instance and make it headless
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')

        # Create a Service instance with ChromeDriverManager
        service = Service(ChromeDriverManager().install())

        # Initialize the Chrome WebDriver with the specified service and options
        driver = webdriver.Chrome(service=service, options=options)

        # Go to the page
        driver.get("https://vyneer.me/vods/")
        # Now the page is fully loaded, including content loaded via JavaScript 
        html_content = driver.page_source
        yt_ids = [match.group(1) for match in re.finditer(pattern, html_content)]
        print("ALL YT IDS:",yt_ids)
        yt_ids=yt_ids[:3]

        # # testing
        # yt_ids=[yt_ids[1]]
    else:
        yt_ids=["QZqGqsDlFrQ"]
        yt_ids=["hAf0iOS-2V4"]
        yt_ids=["CXFDaEbl9UI"]
    print("YT IDS TO RUN:",yt_ids)

    # initialize the discord recaps to send
    discord_recaps_to_send=[]

    # # Discord Testing
    # yt_ids=[]
    # discord_recaps_to_send=[{"meta":"Test","yt_id":"QZqGqsDlFrQ"}]

    # redo a transcript
    skip_transcript=False
    skip_generation=False
    skip_discord=False
    # skip_transcript=True
    # skip_generation=True
    # skip_discord=True
    
    # Loop through the yt_ids and produce the recaps
    for yt_id in yt_ids:
        print("YT ID:",yt_id)
        try:
            transcript_data=await saf.grab_transcript_data(yt_id)
            live_bool=await saf.get_live_status(yt_id)
            if live_bool:
                print("Live Video Not Supported, Skipping")
            if ((not transcript_data) or (skip_transcript)) and (not live_bool):
                if not skip_transcript:
                    # Download Video
                    output_folder="workingaudio/"+yt_id
                    output_filename="audio"
                    await saf.video_download(yt_id)#, output_folder, output_filename)
                    print("Video Downloaded")

                    # Create Raw Transcript Data
                    #audio_file_name=os.listdir(output_folder)[0]
                    raw_transcript_data=await saf.assembly_transcript_generation(yt_id, "workingaudio/merged_audio.mp3")#os.path.join(output_folder,audio_file_name))
                    save_raw_transcript_data={"raw_transcript_data": raw_transcript_data}
                    print("Raw Transcript Finished")
                else:
                    transcript_model_data=await saf.grab_transcript_data(yt_id)
                    raw_transcript_data=transcript_model_data.raw_transcript_data
                    save_raw_transcript_data={"raw_transcript_data": raw_transcript_data}

                if not skip_generation:
                    # Process to make regular and linked_transcript
                    save_processed_transcripts=await saf.process_raw_transcript(raw_transcript_data, yt_id)
                    transcript=save_processed_transcripts["transcript"]
                    linked_transcript=save_processed_transcripts["linked_transcript"]
                    print("Transcript finished")#, transcript)

                    # Make vector db
                    vectordb_and_textchunks=await saf.assembly_generate_vectordb_and_chunks(yt_id, save_processed_transcripts["transcript"])
                    text_chunks=vectordb_and_textchunks["text_chunks"]
                    print("Text Chunks Finished")# ", text_chunks)

                    # Generate summarized segments
                    model_responses=await saf.generate_summarized_segments(save_processed_transcripts["transcript"])#,[], 10)
                    print("Summarized Chunks Finished")#, model_responses)

                    # Make meta summary
                    meta_summary=await saf.generate_meta_summary(model_responses)
                    print("Meta Summary Finished: ", meta_summary)

                    # add the hook to the meta summary
                    recap_hook=await saf.generate_recap_hook(meta_summary)
                    meta_summary=recap_hook+"\n"+meta_summary+"\n\nDISCLAIMER: This is all AI generated and there are frequent errors."


                    # get some video metadata
                    async def get_video_metadata(video_id):
                        url = 'https://www.youtube.com/watch?v='+video_id
                        yt = YouTube(url)
                        return yt.title
                    youtube_title=await get_video_metadata(yt_id)

                    # Save everything
                    await saf.save_data(yt_id, {"video_characteristics":{"title":youtube_title}})
                    await saf.save_data(yt_id, save_raw_transcript_data)
                    await saf.save_data(yt_id, save_processed_transcripts)
                    await saf.save_data(yt_id, {"text_chunks":vectordb_and_textchunks["text_chunks"]})
                    await saf.save_data(yt_id, {"summarized_chunks":model_responses})
                    await saf.save_data(yt_id, {"meta":meta_summary})

                # Send the data to discord
                if not skip_discord:
                    discord_recaps_to_send.append({"meta":meta_summary,"yt_id":yt_id, "title":youtube_title, "hook": None})
            else:
                print("Transcript Data already exists:",yt_id)
        # print any exceptions
        except Exception as e:
            print("ERROR: ",e)
            print(traceback.format_exc())
            




    # Using discord_recaps_to_send to send recaps to discord
    async def send_discord_recaps():
        class MessageSendingClient(discord.Client):
            async def on_ready(self):
                async def send_recap(recap):
                    # Send discord message header
                    destinyrecaps_url="https://destinyrecaps.com"+"/details?video_id="+recap["yt_id"]
                    destinyrecaps_msg="Full transcript and embedding search at "+destinyrecaps_url
                    if recap.get("title",None)!=None:
                        youtube_msg=recap["title"]+": "+"https://www.youtube.com/watch?v="+recap["yt_id"]
                    else:
                        youtube_msg="https://www.youtube.com/watch?v="+recap["yt_id"]

                    header_message=f"{youtube_msg}\n{destinyrecaps_msg}"
                    await channel.send(header_message)

                    # initialize variables for recap message
                    tag_message="@everyone \n"
                    message_str=tag_message+recap["meta"]
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


                print(f'Discord logged in as {self.user}')
                channels=self.get_all_channels()
                for channel in channels:
                    print(channel.name)
                    if channel.name=="recaps":
                        if channel:
                            for recap in discord_recaps_to_send:
                                print("Sending Recap")
                                await send_recap(recap)
                await self.close()

        intents = discord.Intents.default()
        intents.messages = True 
        client = MessageSendingClient(intents=intents)

        await client.start(keys["discord"])

    # start the discord recaps sending
    await send_discord_recaps()

    # return that the process is complete
    return JsonResponse({"response":"completed"})



    




















































































# # # WEBSITE VIEWS
# # PAGE DATA
# Sends the summaies for every video
def get_all_metas(request):
    all_meta_data=TranscriptData.objects.all()
    
    filled_meta_data=[] 
    for meta_data in all_meta_data:
        if meta_data.meta=="":
            meta_data.meta="No meta available"
        print(meta_data.video_id)
        if (meta_data.summarized_chunks!=[]) and (meta_data.meta!=""):
            #print(meta_data.meta)
            if meta_data.video_characteristics.get("title","")!="":
                filled_meta_data.append({'video_id':meta_data.video_id,"meta":meta_data.meta,"title": meta_data.video_characteristics.get("title",None)})
            else:
                filled_meta_data.append({'video_id':meta_data.video_id,"meta":meta_data.meta,"title":"No title available"})
        elif meta_data.linked_transcript!="":
            filled_meta_data.append({'video_id':meta_data.video_id,"meta":"None","title":"No title available","linked_transcript":meta_data.linked_transcript})

    filled_meta_data.reverse()

    return JsonResponse(filled_meta_data, safe=False)

# Sends detailed video information given a video id
async def get_meta_details(request):
    print(request)

    # get the query params from request
    video_id=request.GET.get("video_id")

    # get the data from the database
    meta_data=await sync_to_async(TranscriptData.objects.get)(video_id=video_id)

    # turn meta data into a dictionary
    #meta_data=meta_data.meta

    summary_chunks=meta_data.summarized_chunks
    summary_chunks_str=""
    for chunk in summary_chunks:
        summary_chunks_str+=chunk["summary"]+"\n\n"

    transcript=meta_data.transcript

    
    index_v=100000

    return_dict={'meta': meta_data.meta, "title": meta_data.video_characteristics.get("title",None), "video_id":meta_data.video_id, 'summary_chunks':summary_chunks_str, "transcript":transcript,"linked_transcript":meta_data.linked_transcript, "index": index_v}
    try:
        JsonResponse(return_dict, safe=False)
    except Exception as e:
        print("KNOWN ERROR: ",e)

    return JsonResponse(return_dict, safe=False)

# # Search view
# Takes video id and query text, returns the character index to scroll to
async def get_scroll_index(request):
    # get the query params from request
    video_id=request.GET.get("video_id")
    query=request.GET.get("query")

    # get transcript_data
    transcript_data=await saf.grab_transcript_data(video_id)

    if transcript_data:
        # load vector db from file
        index_path=os.path.join("destinyapp/vector_dbs",video_id+".index")
        # actually load the vector with code in this file
        index = faiss.read_index(index_path)
        d,i=await saf.search_vectordb(index, query)

        query_character_index=transcript_data.transcript.find(transcript_data.text_chunks[i[0][0]])
        all_indexes=[]
        for index_value in i[0]:
            all_indexes.append(transcript_data.transcript.find(transcript_data.text_chunks[index_value]))

        print("ALL INDEXES: ",all_indexes)

        return_data={"index":query_character_index,"all_indexes":all_indexes}
        return JsonResponse(return_data, safe=False)
    else:
        return JsonResponse({"index":0,"all_indexes":[0]},safe=False)





# # # Debugging
# # View raw transcripts
async def view_raw_transcripts(request):
    password=request.GET.get("mra")
    if password!=keys["req_pass"]:
        return JsonResponse({"response":""})
    
    yt_id=request.GET.get("video_id")

    transcript_model_data=await saf.grab_transcript_data(yt_id)

    raw_transcript_data=transcript_model_data.raw_transcript_data

    return JsonResponse({"response":raw_transcript_data})