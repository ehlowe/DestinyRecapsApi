# os imports
import os
import sys

# define the boolean values
def str_to_bool(value):
    return value.lower() in ('true', '1', 't', 'y', 'yes')
web_check=str_to_bool(os.environ.get("web_check",""))
redo_enabled=str_to_bool(os.environ.get("redo_enabled",""))
delete_enabled=str_to_bool(os.environ.get("delete_enabled",""))

# get the passcode
passcode=os.environ.get("req_pass","")


# setup utils

# Django Imports
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.core.cache import cache
from django.utils.decorators import sync_and_async_middleware


# Django Rest Framework Imports
from rest_framework.response import Response
from rest_framework import serializers

# Async Imports
from asgiref.sync import iscoroutinefunction
from asgiref.sync import sync_to_async
import asyncio
import aiohttp

# Basic Imports
import re
import json
import time
import datetime
from pathlib import Path
import traceback
import html2text

# Youtube downloader
from pytube import YouTube
import yt_dlp as youtube_dl
from chat_downloader import ChatDownloader

# Webdriver on vyneer website
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Discord imports
import discord
from discord.ext import commands

# Import custom modules
# from destinyapp.customlibrary import ServerAiFunctions as saf
# from destinyapp.models import TranscriptData, BotData

# Distribute keys and create clients
# import faiss
# import openai
# from openai import AsyncOpenAI
# import anthropic
# from anthropic import AsyncAnthropic
# import assemblyai as aai
# openai_client=openai.OpenAI(api_key=os.environ.get("openai",""))
# async_openai_client=AsyncOpenAI(api_key=os.environ.get("openai",""))
# anthropic_client=anthropic.Anthropic(api_key=os.environ.get("anthropic",""))
# async_anthropic_client=AsyncAnthropic(api_key=os.environ.get("anthropic",""))
# discord_key=os.environ.get("discord","")
# aai.settings.api_key = os.environ.get("assemblyai","")


# Password middleware
@sync_and_async_middleware
def password_checker(get_response):
    if iscoroutinefunction(get_response):
        async def middleware(request):
            if passcode!=request.GET.get("mra"):
                return JsonResponse({"response":""})
            else:
                response = await get_response(request)
                return response
    else:
        def middleware(request):
            if passcode!=request.GET.get("mra"):
                return JsonResponse({"response":""})
            else:
                response = get_response(request)
                return response

    return middleware





# from destinyapp.customlibrary import controls as cl

# async def get_all_metas(request):
#     filled_meta_data = await cl.get_all_metas(request)
#     return JsonResponse(filled_meta_data, safe=False)











































































































































# # # MISC FUNCTIONS
# # delete all transcript data, delete_enabled has to be set in keys.json
# async def delete_transcripts(request):
#     if delete_enabled:
#         request_data=request.GET.get("mra")
#         if (request_data==passcode):
#             print("Deleting all data")
#             # delete all data
#             all_data=await saf.get_all_data()
#             for data in all_data:
#                 await sync_to_async(data.delete)()
#                 print("deleted: ",data.video_id)
#             return JsonResponse({"response":"delted all data"})
#         else:
#             print("Delete request denied")
#     else:
#         print("Delete not enabled")

#     return JsonResponse({"response":"Operation not eceuted"})









# # # RECAPS GENERATOR FUNCTIONS

# async def auto_recaps_request(request):
#     # Get form data from request
#     print("Request:",request)
#     request_data=request.GET.get("mra")
#     if not (request_data==passcode):
#         print("Wrong password: ", request_data)
#         return(JsonResponse({}))
    
#     # make thread for auto_recaps_generator
#     enqueue_auto_recaps_generator()

#     return JsonResponse({"response":"Auto Recaps Generator Started"})

# def enqueue_auto_recaps_generator():
#     lock_id = 'auto_recaps_generator_lock'
#     # Check if the task is already queued or running
#     if not cache.get(lock_id):
#         # Set the lock with a timeout (e.g., 2 hours)
#         cache.set(lock_id, True, timeout=7200)
#         asyncio.create_task(auto_recaps_generator())
#         print("Task queued")
#         # async_task('auto_recaps_generator')
#     else:
#         print("Task is already queued or running.")

# # Auto recaps generator
# async def auto_recaps_generator():    
#     # time to wait between requests
#     ran_wait_time=36
#     # ran_wait_time=5

#     # check if the bot has ran within the hour
#     bot_data=await sync_to_async(BotData.objects.filter)(bot_id="baseid")
#     existing_bot_data=await sync_to_async(bot_data.exists)()
#     if existing_bot_data:
#         bot_data=await sync_to_async(BotData.objects.get)(bot_id="baseid")
#     if existing_bot_data and (bot_data.last_time_ran!=""):
#         time_now_str=str(datetime.datetime.now())
#         bot_last_ran_str=bot_data.last_time_ran

#         # if the bot has ran within the hour then return
#         parsed_time_now_str=time_now_str.split(".")[0]
#         parsed_bot_last_ran_str=str(bot_last_ran_str).split(".")[0]

#         #if the seconds are within 3600
#         if (datetime.datetime.strptime(parsed_time_now_str, "%Y-%m-%d %H:%M:%S")-datetime.datetime.strptime(parsed_bot_last_ran_str, "%Y-%m-%d %H:%M:%S")).seconds<ran_wait_time:
#             return JsonResponse({"response":"Bot already ran within the hour"})
#         else:
#             bot_data.last_time_ran=time_now_str
#             save_function=bot_data.save
#             await sync_to_async(save_function)()
#     else:
#         # create and save the bot data with the current time if the bot data doesn't exist
#         bot_data=BotData(bot_id="baseid",last_time_ran=str(datetime.datetime.now()))
#         save_function=bot_data.save
#         await sync_to_async(save_function)()



#     print("Starting Recap Generations")
#     pattern = r"https://youtu.be/([\w-]+)"


#     # Get the youtube ids
#     if web_check:
#         # Create a Chrome Options instance and make it headless
#         options = Options()
#         options.add_argument('--headless')
#         options.add_argument('--disable-gpu')
#         options.add_argument('--no-sandbox')

#         # Create a Service instance with ChromeDriverManager
#         service = Service(ChromeDriverManager().install())

#         # Initialize the Chrome WebDriver with the specified service and options
#         driver = webdriver.Chrome(service=service, options=options)

#         # Go to the page
#         driver.get("https://vyneer.me/vods/")
#         # Now the page is fully loaded, including content loaded via JavaScript 
#         html_content = driver.page_source
#         yt_ids = [match.group(1) for match in re.finditer(pattern, html_content)]
#         print("ALL YT IDS:",yt_ids)
#         yt_ids=yt_ids[:3]

#         # # testing
#         # yt_ids=[yt_ids[1]]
#     else:
#         yt_ids=["QZqGqsDlFrQ"]
#         yt_ids=["hAf0iOS-2V4"]
#         yt_ids=["CXFDaEbl9UI"]
#         yt_ids=["ZeNt2JM6xMs"]
#         yt_ids=["2O8rCcpFswk"]
#     print("YT IDS TO RUN:",yt_ids)

#     # initialize the discord recaps to send
#     discord_recaps_to_send=[]

#     # # # Discord Testing
#     # yt_ids=[]
#     # discord_recaps_to_send=[{"meta":"Test","yt_id":"3kJr7ODrwNw"}]
#     # trancript_model_data=await saf.grab_transcript_data(discord_recaps_to_send[0]["yt_id"])
#     # recap = await saf.meta_summary_generator.generate_meta_summary(trancript_model_data.summarized_chunks)
#     # recap_hook=await saf.generate_recap_hook(recap)
#     # recap=recap_hook+"\n"+recap+"\n\nDISCLAIMER: This is all AI generated and there are frequent errors."
#     # discord_recaps_to_send[0]["meta"]=recap
#     # print("Recap Generated: ",recap)

#     # redo a transcript
#     skip_transcript=False
#     skip_generation=False
#     skip_discord=False
#     # skip_transcript=True
#     # skip_generation=True
#     # skip_discord=True
    
#     # Loop through the yt_ids and produce the recaps
#     for yt_id in yt_ids:
#         print("YT ID:",yt_id)
#         try:
#             transcript_data=await saf.grab_transcript_data(yt_id)
#             live_bool=await saf.get_live_status(yt_id)
#             if live_bool:
#                 print("Live Video Not Supported, Skipping")
#             if ((not transcript_data) or (skip_transcript)) and (not live_bool):
#                 if not skip_transcript:
#                     # Download Video
#                     output_folder="workingaudio/"+yt_id
#                     output_filename="audio"
#                     await saf.video_download(yt_id)#, output_folder, output_filename)
#                     print("Video Downloaded")

#                     # Create Raw Transcript Data
#                     raw_transcript_data=await saf.assembly_transcript_generation(yt_id, "workingaudio/merged_audio.mp3")#os.path.join(output_folder,audio_file_name))
#                     save_raw_transcript_data={"raw_transcript_data": raw_transcript_data}
#                     print("Raw Transcript Finished")
#                 else:
#                     transcript_model_data=await saf.grab_transcript_data(yt_id)
#                     raw_transcript_data=transcript_model_data.raw_transcript_data
#                     save_raw_transcript_data={"raw_transcript_data": raw_transcript_data}

#                 if not skip_generation:
#                     # Process to make regular and linked_transcript
#                     save_processed_transcripts=await saf.process_raw_transcript(raw_transcript_data, yt_id)
#                     transcript=save_processed_transcripts["transcript"]
#                     linked_transcript=save_processed_transcripts["linked_transcript"]
#                     print("Transcript finished")#, transcript)

#                     # Make vector db
#                     vectordb_and_textchunks=await saf.assembly_generate_vectordb_and_chunks(yt_id, save_processed_transcripts["transcript"])
#                     text_chunks=vectordb_and_textchunks["text_chunks"]
#                     print("Text Chunks Finished")# ", text_chunks)

#                     # Generate summarized segments
#                     model_responses=await saf.generate_summarized_segments(save_processed_transcripts["transcript"])#,[], 10)
#                     print("Summarized Chunks Finished")#, model_responses)

#                     # Make meta summary
#                     # meta_summary=await saf.generate_meta_summary(model_responses)
#                     meta_summary=await saf.meta_summary_generator.generate_meta_summary(model_responses)
#                     print("Meta Summary Finished: ", meta_summary)

#                     # add the hook to the meta summary
#                     recap_hook=await saf.generate_recap_hook(meta_summary)
#                     meta_summary=recap_hook+"\n"+meta_summary+"\n\nDISCLAIMER: This is all AI generated and there are frequent errors."


#                     # get some video metadata
#                     async def get_video_metadata(video_id):
#                         ydl_opts = {}
#                         full_title=""
#                         try:
#                             with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#                                 info_dict = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
#                                 info_dict_g=info_dict
#                                 upload_date = info_dict['upload_date']
#                                 upload_date
#                                 date_obj=datetime.datetime.strptime(upload_date, "%Y%m%d")
#                                 date_str=date_obj.strftime("%m/%d/%Y")
#                                 title=info_dict["title"]
#                                 full_title=title+"\nStream Date~ "+date_str
#                         except Exception as e:
#                             pass
#                         return full_title
#                     full_title=await get_video_metadata(yt_id)

#                     # Save everything
#                     await saf.save_data(yt_id, {"video_characteristics":{"title":full_title}})
#                     await saf.save_data(yt_id, save_raw_transcript_data)
#                     await saf.save_data(yt_id, save_processed_transcripts)
#                     await saf.save_data(yt_id, {"text_chunks":vectordb_and_textchunks["text_chunks"]})
#                     await saf.save_data(yt_id, {"summarized_chunks":model_responses})
#                     await saf.save_data(yt_id, {"meta":meta_summary})

#                 # Send the data to discord
#                 if not skip_discord:
#                     discord_recaps_to_send.append({"meta":meta_summary,"yt_id":yt_id, "title":full_title, "hook": None})
#             else:
#                 print("Transcript Data already exists:",yt_id)
#         # print any exceptions
#         except Exception as e:
#             print("ERROR: ",e)
#             print(traceback.format_exc())

#     # Using discord_recaps_to_send to send recaps to discord
#     async def send_discord_recaps():
#         class MessageSendingClient(discord.Client):
#             async def on_ready(self):
#                 async def send_recap(recap):
#                     # Send discord message header
#                     destinyrecaps_url="https://destinyrecaps.com"+"/details?video_id="+recap["yt_id"]
#                     destinyrecaps_msg="Full transcript and embedding search at "+destinyrecaps_url
#                     if recap.get("title",None)!=None:
#                         youtube_msg=recap["title"]+": "+"https://www.youtube.com/watch?v="+recap["yt_id"]
#                     else:
#                         youtube_msg="https://www.youtube.com/watch?v="+recap["yt_id"]

#                     header_message=f"{youtube_msg}\n{destinyrecaps_msg}"
#                     await channel.send(header_message)

#                     # initialize variables for recap message
#                     tag_message="@everyone \n"
#                     message_str=tag_message+html2text.html2text(recap["meta"])
#                     start_index=0
#                     recap_chunks={}
#                     recap_chunks["start_finish"]=[0]
#                     recap_chunks["segments"]=[]
#                     increment_size=1500

#                     # increment for the number of segments needed
#                     for i in range((len(message_str)//increment_size)+1):
                        
#                         # find the the reasonable end of the segment
#                         finish_index=start_index+increment_size
#                         if finish_index>=len(message_str):
#                             finish_index=None
#                         else:
#                             while message_str[finish_index]!="\n":
#                                 finish_index+=1
#                                 if (finish_index-start_index)>2100:
#                                     print("Didn't find a newline")
#                                     break
#                                 if finish_index>=len(message_str):
#                                     finish_index=None
#                                     break
                        
#                         # append the segments to the list
#                         recap_chunks["segments"].append(message_str[start_index:finish_index])
#                         start_index=finish_index
#                         recap_chunks["start_finish"].append(start_index)

#                         if finish_index==None:
#                             break

#                     print("Sending chunks: ",len(recap_chunks["segments"]))
#                     for recap_chunk in recap_chunks["segments"]:
#                         await channel.send(recap_chunk)


#                 print(f'Discord logged in as {self.user}')
#                 channels=self.get_all_channels()
#                 for channel in channels:
#                     print(channel.name)
#                     if channel.name=="recaps":
#                         if channel:
#                             for recap in discord_recaps_to_send:
#                                 print("Sending Recap")
#                                 try:
#                                     await send_recap(recap)
#                                 except Exception as e:
#                                     # print as much as possible
#                                     print("ERROR: ",e)
#                                     print(traceback.format_exc())

#                 await self.close()
#                 print("Send and client closed")

#         intents = discord.Intents.default()
#         intents.messages = True 
#         client = MessageSendingClient(intents=intents)

#         await client.start(os.environ.get("discord"))

#     # start the discord recaps sending
#     try:
#         await send_discord_recaps()
#     except Exception as e:
#         print("ERROR: ",e)
#         print(traceback.format_exc())
    
#     cache.delete('auto_recaps_generator_lock')

#     # return that the process is complete
#     return JsonResponse({"response":"completed"})



    








































































# @password_checker
# async def redo_recaps_request(request):
#     # Get form data from request
#     print("Request:",request)
#     if not redo_enabled:
#         return(JsonResponse({}))
    
#     # make thread for auto_recaps_generator
#     item_count=request.GET.get("item_count",None)
#     if item_count==None:
#         item_count=1
#     else:
#         item_count=int(item_count)
#     enqueue_redo_recaps_generator(item_count)

#     return JsonResponse({"response":"Redo Recaps Generator Started"})

# def enqueue_redo_recaps_generator(item_count):
#     lock_id = 'auto_recaps_generator_lock'
#     # Check if the task is already queued or running
#     if not cache.get(lock_id):
#         # Set the lock with a timeout (e.g., 2 hours)
#         cache.set(lock_id, True, timeout=7200)
#         asyncio.create_task(redo_recap_controller(item_count=item_count))
#         print("Task queued")
#         # async_task('auto_recaps_generator')
#     else:
#         print("Task is already queued or running.")

# async def redo_recap_controller(item_count=1):
#     all_transcript_data = await saf.get_all_data()
#     if item_count>len(all_transcript_data):
#         item_count=len(all_transcript_data)
#     print(f"REDOING RECAPS FOR {item_count} ITEMS")

#     selected_transcript_model_datas=[]
#     for i, transcript_model_data in enumerate(all_transcript_data[::-1][:item_count]):
#         print(i, transcript_model_data.video_id, transcript_model_data.video_characteristics)
#         selected_transcript_model_datas.append(transcript_model_data)

#     await redo_recaps(selected_transcript_model_datas)

# async def redo_recaps(transcript_model_datas, vector_embeedding_bool=True, summary_segments_bool=True, meta_summary_bool=True, video_metadata_bool=True):

#     discord_recaps_to_send=[]
#     for transcript_model_data in transcript_model_datas:
#         yt_id=transcript_model_data.video_id
#         print("REDOING RECAP FOR: ", yt_id)
#         raw_transcript_data=transcript_model_data.raw_transcript_data
#         save_raw_transcript_data={"raw_transcript_data": raw_transcript_data}

#         # Process to make regular and linked_transcript
#         save_processed_transcripts=await saf.process_raw_transcript(raw_transcript_data, yt_id)
#         transcript=save_processed_transcripts["transcript"]
#         linked_transcript=save_processed_transcripts["linked_transcript"]
#         print("Transcript finished")#, transcript)

#         # Make vector db
#         if vector_embeedding_bool:
#             vectordb_and_textchunks=await saf.assembly_generate_vectordb_and_chunks(yt_id, save_processed_transcripts["transcript"])
#             text_chunks=vectordb_and_textchunks["text_chunks"]
#             print("Text Chunks Finished")# ", text_chunks)

#         # Generate summarized segments
#         if summary_segments_bool:
#             model_responses=await saf.generate_summarized_segments(save_processed_transcripts["transcript"])#,[], 10)
#             print("Summarized Chunks Finished")#, model_responses)

#         # Make meta summary
#         if meta_summary_bool:
#             # meta_summary=await saf.generate_meta_summary(model_responses)
#             meta_summary=await saf.meta_summary_generator.generate_meta_summary(model_responses)
#             print("Meta Summary Finished: ", meta_summary)

#             # add the hook to the meta summary
#             recap_hook=await saf.generate_recap_hook(meta_summary)
#             meta_summary=recap_hook+"\n"+meta_summary+"\n\nDISCLAIMER: This is all AI generated and there are frequent errors."


#         # get some video metadata
#         if video_metadata_bool:
#             # get some video metadata
#             async def get_video_metadata(video_id):
#                 ydl_opts = {}
#                 full_title=""
#                 try:
#                     with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#                         info_dict = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
#                         info_dict_g=info_dict
#                         upload_date = info_dict['upload_date']
#                         upload_date
#                         date_obj=datetime.datetime.strptime(upload_date, "%Y%m%d")
#                         date_str=date_obj.strftime("%m/%d/%Y")
#                         title=info_dict["title"]
#                         full_title=title+"\nStream Date~ "+date_str
#                 except Exception as e:
#                     pass
#                 return full_title

#         # Save everything
#         await saf.save_data(yt_id, save_processed_transcripts)
#         if vector_embeedding_bool:
#             await saf.save_data(yt_id, {"text_chunks":vectordb_and_textchunks["text_chunks"]})
#         if summary_segments_bool:
#             await saf.save_data(yt_id, {"summarized_chunks":model_responses})
#         if meta_summary_bool:
#             await saf.save_data(yt_id, {"meta":meta_summary})
#         if video_metadata_bool:
#             await saf.save_data(yt_id, {"video_characteristics":{"title":full_title}})

        
#         # Setup discord to send message
#         new_transcript_model_data=await saf.grab_transcript_data(yt_id)
#         if new_transcript_model_data.video_characteristics.get("title", None)!=None:
#             full_title=new_transcript_model_data.video_characteristics["title"]
#         else:
#             full_title=None
#         discord_recaps_to_send.append({"meta":new_transcript_model_data.meta,"yt_id":yt_id, "title":full_title})

    
#     # Using discord_recaps_to_send to send recaps to discord
#     async def send_discord_recaps():
#         class MessageSendingClient(discord.Client):
#             async def on_ready(self):
#                 async def send_recap(recap):
#                     # Send discord message header
#                     destinyrecaps_url="https://destinyrecaps.com"+"/details?video_id="+recap["yt_id"]
#                     destinyrecaps_msg="Full transcript and embedding search at "+destinyrecaps_url
#                     if recap.get("title",None)!=None:
#                         youtube_msg=recap["title"]+": "+"https://www.youtube.com/watch?v="+recap["yt_id"]
#                     else:
#                         youtube_msg="https://www.youtube.com/watch?v="+recap["yt_id"]

#                     header_message=f"{youtube_msg}\n{destinyrecaps_msg}"
#                     await channel.send(header_message)

#                     # initialize variables for recap message
#                     tag_message="@everyone \n"
#                     message_str=tag_message+html2text.html2text(recap["meta"])
#                     start_index=0
#                     recap_chunks={}
#                     recap_chunks["start_finish"]=[0]
#                     recap_chunks["segments"]=[]
#                     increment_size=1500

#                     # increment for the number of segments needed
#                     for i in range((len(message_str)//increment_size)+1):
                        
#                         # find the the reasonable end of the segment
#                         finish_index=start_index+increment_size
#                         if finish_index>=len(message_str):
#                             finish_index=None
#                         else:
#                             while message_str[finish_index]!="\n":
#                                 finish_index+=1
#                                 if (finish_index-start_index)>2100:
#                                     print("Didn't find a newline")
#                                     break
#                                 if finish_index>=len(message_str):
#                                     finish_index=None
#                                     break
                        
#                         # append the segments to the list
#                         recap_chunks["segments"].append(message_str[start_index:finish_index])
#                         start_index=finish_index
#                         recap_chunks["start_finish"].append(start_index)

#                         if finish_index==None:
#                             break

#                     print("Sending c-hunks: ",len(recap_chunks["segments"]))
#                     for recap_chunk in recap_chunks["segments"]:
#                         await channel.send(recap_chunk)


#                 print(f'Discord logged in as {self.user}')
#                 channels=self.get_all_channels()
#                 for channel in channels:
#                     print(channel.name)
#                     if channel.name=="recaps":
#                         if channel:
#                             for recap in discord_recaps_to_send:
#                                 print("Sending Recap")
#                                 try:
#                                     await send_recap(recap)
#                                 except Exception as e:
#                                     # print as much as possible
#                                     print("ERROR: ",e)
#                                     print(traceback.format_exc())

#                 await self.close()
#                 print("Send and client closed")

#         intents = discord.Intents.default()
#         intents.messages = True 
#         client = MessageSendingClient(intents=intents)

#         await client.start(os.environ.get("discord"))

#     # start the discord recaps sending
#     try:
#         await send_discord_recaps()
#     except Exception as e:
#         print("ERROR: ",e)
#         print(traceback.format_exc())

#     cache.delete('auto_recaps_generator_lock')















































































# # # # WEBSITE VIEWS
# # # PAGE DATA
# # Sends the summaies for every video
# def get_all_metas(request):
#     t_start=time.time()
#     #all_meta_data=TranscriptData.objects.all()

#     all_meta_data=TranscriptData.objects.defer('raw_transcript_data','linked_transcript','transcript','summarized_chunks').all()
    
    
#     filled_meta_data=[] 
#     for meta_data in all_meta_data:
#         if meta_data.meta=="":
#             meta_data.meta="No meta available"
#         print(meta_data.video_id)
#         if (meta_data.meta!=""):
#             #print(meta_data.meta)
#             if meta_data.video_characteristics.get("title","")!="":
#                 filled_meta_data.append({'video_id':meta_data.video_id,"meta":meta_data.meta,"title": meta_data.video_characteristics.get("title",None)})
#             else:
#                 filled_meta_data.append({'video_id':meta_data.video_id,"meta":meta_data.meta,"title":"No title available"})
#         elif meta_data.linked_transcript!="":
#             filled_meta_data.append({'video_id':meta_data.video_id,"meta":"None","title":"No title available","linked_transcript":meta_data.linked_transcript})

#     filled_meta_data.reverse()

#     print("Time to get all metas: ",time.time()-t_start)

#     return JsonResponse(filled_meta_data, safe=False)

# # Sends detailed video information given a video id
# async def get_meta_details(request):
#     t_start=time.time()
#     # get the query params from request
#     video_id=request.GET.get("video_id")

#     # get the data from the database
#     # meta_data=await sync_to_async(TranscriptData.objects.get)(video_id=video_id)
#     meta_data=await sync_to_async(TranscriptData.objects.defer('raw_transcript_data','linked_transcript','summarized_chunks').get)(video_id=video_id)

#     # summary_chunks=meta_data.summarized_chunks
#     # summary_chunks_str=""
#     # for chunk in summary_chunks:
#     #     summary_chunks_str+=chunk["summary"]+"\n\n"

#     transcript=meta_data.transcript

    
#     index_v=100000

#     return_dict={'meta': meta_data.meta, "title": meta_data.video_characteristics.get("title",None), "video_id":meta_data.video_id, "transcript":transcript}

#     # return_dict={'meta': meta_data.meta, "title": meta_data.video_characteristics.get("title",None), "video_id":meta_data.video_id, "transcript":transcript,"linked_transcript":meta_data.linked_transcript}
    
#     print("Time to get meta details: ",time.time()-t_start)
#     try:
#         JsonResponse(return_dict, safe=False)
#     except Exception as e:
#         print("KNOWN ERROR: ",e)
#     return JsonResponse(return_dict, safe=False)


# async def get_meta_linked_transcript(request):
#     video_id=request.GET.get("video_id")

#     # await asyncio.sleep(2)

#     meta_data=await sync_to_async(TranscriptData.objects.defer('raw_transcript_data').get)(video_id=video_id)

#     return_dict={"linked_transcript":meta_data.linked_transcript}

#     return JsonResponse(return_dict, safe=False)

# # # Search view
# # Takes video id and query text, returns the character index to scroll to
# async def get_scroll_index(request):
#     # get the query params from request
#     video_id=request.GET.get("video_id")
#     query=request.GET.get("query")

#     # get transcript_data
#     transcript_data=await saf.grab_transcript_data(video_id)

#     if transcript_data:
#         # load vector db from file
#         index_path=os.path.join("destinyapp/vector_dbs",video_id+".index")
#         # actually load the vector with code in this file
#         index = faiss.read_index(index_path)
#         d,i=await saf.search_vectordb(index, query)

#         query_character_index=transcript_data.transcript.find(transcript_data.text_chunks[i[0][0]])
#         all_indexes=[]
#         for index_value in i[0]:
#             all_indexes.append(transcript_data.transcript.find(transcript_data.text_chunks[index_value]))

#         print("ALL INDEXES: ",all_indexes)

#         return_data={"index":query_character_index,"all_indexes":all_indexes}
#         return JsonResponse(return_data, safe=False)
#     else:
#         return JsonResponse({"index":0,"all_indexes":[0]},safe=False)





# # # # Debugging
# # # View raw transcripts
# # from functools import wraps


# # def password_checker(view_function):
# #     @wraps(view_function)
# #     def wrap(request):
# #         # Any preprocessing conditions..etc.
# #         password=request.GET.get("mra")
# #         if password!=passcode:
# #             return JsonResponse({"response":"NAW DUDE"})

# #         return view_function(request)
# #     return wrap





# @password_checker
# async def view_raw_transcripts(request):
#     print("Viewing Raw Transcripts")

#     yt_id=request.GET.get("video_id")

#     transcript_model_data=await saf.grab_transcript_data(yt_id)

#     raw_transcript_data=transcript_model_data.raw_transcript_data

#     return JsonResponse({"response":raw_transcript_data})