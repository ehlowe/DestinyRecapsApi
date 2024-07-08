import time
from destinyapp.models import StreamRecapData
import asyncio
from asgiref.sync import sync_to_async


from . import services
from . import utils





# Auto Recap Gen Controller
class auto_recap_controller:

    @classmethod
    async def run(self):
        video_ids=await self.get_video_ids()

        if video_ids!=[]:
            discord_message_video_ids=await self.generate_all(video_ids)

            if discord_message_video_ids!=[]:
                await self.send_discord_messages(discord_message_video_ids)






    async def get_video_ids():
        # Ensure that the bot can run
        bot_run_bool=await services.bot_run_check()
        if not bot_run_bool:
            print("Bot cannot run at this time, it has not been long enough since the last run.")
            return []

        # Get video ids to run on
        video_ids=await services.web_view_recent_stream_ids()

        return video_ids

        

    @classmethod
    async def generate_all(self, video_ids):
        # video_id_test="Gej2eHRwlM0"
        # video_id_test="kDsuggCYdyE"
        video_id_test="SPaeA8shXFg"

        discord_message_video_ids=[]

        # Loop through video ids
        for video_id in video_ids:

            video_id=video_id_test

            # Check run conditions for video_id
            test_stream_recap_data=await utils.get_recap_data(video_id)
            live_bool=await services.get_live_status(video_id)

            # Must not have existing data and must not be live
            if (not live_bool) and (test_stream_recap_data==None):

                # Get all transcript data
                transcript, linked_transcript, raw_transcript_data=await self.produce_transcript_data(video_id)

                # Get all recap data
                vectordb, text_chunks, segments_and_summaries, finalized_recap, full_title=await self.produce_recap_data(video_id, transcript)

                # Save the data
                await self.save_data(video_id, full_title, raw_transcript_data, transcript, linked_transcript, text_chunks, segments_and_summaries, finalized_recap)

                # add the video id to the list of video ids to send discord messages for
                discord_message_video_ids.append(video_id)

        return discord_message_video_ids

    # Produce Transcript Data
    async def produce_transcript_data(video_id):
        # Download video
        await services.download_video(video_id)

        # Generate Assembly Transcript
        raw_transcript_data = await services.generate_assembly_transcript()

        # Process Raw Transcript
        transcript, linked_transcript = await services.process_raw_transcript(raw_transcript_data, video_id)

        return transcript, linked_transcript, raw_transcript_data
    

    # Generate Everything Needed for Recap
    async def produce_recap_data(video_id, transcript):
        # Generate Vector DB and Text Chunks
        vectordb, text_chunks = await services.VectorDbAndTextChunksGenerator.generate_basic_vectordb_and_chunks(video_id, transcript)

        # Generate Summarized Segments
        segments_and_summaries = await services.SummarizedSegmentGenerator.generate_summarized_segments(transcript)

        # Generate Recap
        recap = await services.RecapGenerator.generate_recap(segments_and_summaries)

        # Generate Recap Hook
        recap_hook=await services.RecapGenerator.generate_recap_hook(recap)

        # Format and finalize the recap
        finalized_recap=recap_hook+"\n"+recap+"\n\nDISCLAIMER: This is all AI generated and there are frequent errors."

        # Get stream title
        full_title=await services.get_video_metadata(video_id)

        return vectordb, text_chunks, segments_and_summaries, finalized_recap, full_title
    
    # Save the data
    async def save_data(video_id, full_title, raw_transcript_data, transcript, linked_transcript, text_chunks, segments_and_summaries, finalized_recap):
        stream_recap_data=StreamRecapData(video_id=video_id, video_characteristics={"title":full_title}, raw_transcript_data=raw_transcript_data, transcript=transcript, linked_transcript=linked_transcript, text_chunks=text_chunks, summarized_chunks=segments_and_summaries, recap=finalized_recap)

        await sync_to_async(stream_recap_data.save)()


    async def send_discord_messages(discord_message_video_ids):
        #oldest to newest
        discord_message_video_ids.reverse()

        # Compile data for recap messages
        discord_recaps_to_send=await services.DiscordMessageHandler.compile_discord_messages(discord_message_video_ids)

        # Send recaps to discord
        await services.DiscordMessageHandler.send_discord_recaps(discord_recaps_to_send)




















    # async def run_old():
    #     video_id_test="Gej2eHRwlM0"

    #     # Ensure that the bot can run
    #     bot_run_bool=await services.bot_run_check()
    #     if not bot_run_bool:
    #         print("Bot cannot run at this time, it has not been long enough since the last run.")
    #         return

    #     # Get video ids to run on
    #     video_ids=await services.web_view_recent_stream_ids()

    #     discord_message_video_ids=[]

    #     # Loop through video ids
    #     for video_id in video_ids:

    #         video_id=video_id_test

    #         # Check run conditions for video_id
    #         test_stream_recap_data=await utils.get_recap_data(video_id)
    #         live_bool=await services.get_live_status(video_id)

    #         # Must not have existing data and must not be live
    #         if (not live_bool) and (test_stream_recap_data==None):

    #             # Download video
    #             await services.download_video(video_id)

    #             # Generate Assembly Transcript
    #             raw_transcript = await services.generate_assembly_transcript()

    #             # Process Raw Transcript
    #             transcript, linked_transcript = await services.process_raw_transcript(raw_transcript, video_id)

    #             # Generate Vector DB and Text Chunks
    #             vectordb, text_chunks = await services.VectorDbAndTextChunksGenerator.generate_basic_vectordb_and_chunks(video_id, transcript)

    #             # Generate Summarized Segments
    #             segments_and_summaries = await services.SummarizedSegmentGenerator.generate_summarized_segments(transcript)

    #             # Generate Recap
    #             recap = await services.RecapGenerator.generate_recap(segments_and_summaries)

    #             # Generate Recap Hook
    #             recap_hook=await services.RecapGenerator.generate_recap_hook(recap)

    #             # Format and finalize the recap
    #             finalized_recap=recap_hook+"\n"+recap+"\n\nDISCLAIMER: This is all AI generated and there are frequent errors."

    #             # Get stream title
    #             full_title=await services.get_video_metadata(video_id)

    #             # Save the data
    #             stream_recap_data=StreamRecapData(video_id=video_id, video_characteristics={"title":full_title}, raw_transcript_data=raw_transcript, transcript=transcript, linked_transcript=linked_transcript, text_chunks=text_chunks, summarized_chunks=segments_and_summaries, recap=finalized_recap)
    #             await sync_to_async(stream_recap_data.save)()

    #             # Discord video ids to run
    #             discord_message_video_ids.append(video_id)
        

    #     # oldest to newest
    #     discord_message_video_ids.reverse()

    #     # Compile data for recap messages
    #     discord_recaps_to_send=await services.DiscordMessageHandler.compile_discord_messages(discord_message_video_ids)

    #     # Send recaps to discord
    #     await services.DiscordMessageHandler.send_discord_recaps(discord_recaps_to_send)