import discord
import html2text
import traceback
import os
import io
import base64

# import from a directory below
from core import utils




class DiscordMessageHandler:
    async def compile_discord_messages(video_ids):
        discord_messages=[]
        for video_id in video_ids:
            recap_data=await utils.get_recap_data(video_id)
            if recap_data:
                discord_messages.append(recap_data)
        
        return discord_messages


    # Using discord_recaps_to_send to send recaps to discord
    async def send_discord_recaps(discord_recaps_to_send):
        class MessageSendingClient(discord.Client):
            # Sends a single recap to a channel
            async def send_recap(self, recap, channel):
                # Send discord message header
                destinyrecaps_url="https://destinyrecaps.com"+"/details?video_id="+recap.video_id
                destinyrecaps_msg="Full transcript and embedding search at "+destinyrecaps_url
                if recap.video_characteristics.get("title",None)!=None:
                    youtube_msg=recap.video_characteristics["title"]+": "+"https://www.youtube.com/watch?v="+recap.video_id
                else:
                    youtube_msg="https://www.youtube.com/watch?v="+recap.video_id

                header_message=f".\n.\n.\n{youtube_msg}\n{destinyrecaps_msg}"

                # send base64 image
                if len(recap.plot_image)>100:
                    # Decode the base64 image
                    image_binary = base64.b64decode(recap.plot_image)
                    image_file = discord.File(io.BytesIO(image_binary), filename="recap_image.png")
                    await channel.send(header_message, file=image_file)
                    # close the file
                    image_file.fp.close()
                else:
                    await channel.send(header_message)

                    
                


                # initialize variables for recap message
                tag_message="@everyone \n"
                if channel.name!="recaps":
                    tag_message=""

                message_str=tag_message+html2text.html2text(recap.recap)
                start_index=0
                recap_chunks={}
                recap_chunks["start_finish"]=[0]
                recap_chunks["segments"]=[]
                increment_size=1500

                # if len(recap.plot_image)>100:
                #     hook=message_str[0:500].split("\n")[0]
                #     await channel.send(hook)

                # else:
                if True:
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

                        if finish_index==None:
                            break

                    print("Sending chunks: ",len(recap_chunks["segments"]))
                    for recap_chunk in recap_chunks["segments"]:
                        await channel.send(recap_chunk)

            # On ready function
            async def on_ready(self):
                try:
                    print(f'Discord logged in as {self.user}')
                    channels=self.get_all_channels()
                    for channel in channels:
                        print(channel.name)
                        if channel.name==os.environ.get("discord_channel"):
                            if channel:
                                for recap in discord_recaps_to_send:
                                    print("Sending Recap video_id: ",recap.video_id, " to channel: ",channel.name)
                                    try:
                                        await self.send_recap(recap, channel)
                                    except Exception as e:
                                        # print as much as possible
                                        print("ERROR: ",e)
                                        print(traceback.format_exc())

                    await self.close()
                    print("Send and client closed")
                except Exception as e:
                    print("ERROR: ",e)
                    print(traceback.format_exc())
                    await self.close()

        intents = discord.Intents.default()
        intents.messages = True 
        client = MessageSendingClient(intents=intents)

        await client.start(os.environ.get("discord"))