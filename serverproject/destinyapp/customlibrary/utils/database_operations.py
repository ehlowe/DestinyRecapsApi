from asgiref.sync import sync_to_async

from django.core import serializers

from destinyapp.models import StreamRecapData



# Main saving function
async def save_data(video_id, field_data_dict):
    recap_data_exists = await sync_to_async(StreamRecapData.objects.filter(video_id=video_id).exists)()
    # if transcript data exists
    if recap_data_exists:
        recap_data = await sync_to_async(StreamRecapData.objects.get)(video_id=video_id)
        print("updating transcript data")
        for field_name, data in field_data_dict.items():
            setattr(recap_data, field_name, data)
        await sync_to_async(recap_data.save)()
    else:
        print("creating new transcript data")
        recap_data=StreamRecapData(video_id=video_id)
        for field_name, data in field_data_dict.items():
            setattr(recap_data, field_name, data)
        await sync_to_async(recap_data.save)()

# Delete an object
async def delete_stream_recap_data(video_id):
    delete_obj=await sync_to_async(StreamRecapData.objects.filter)(video_id=video_id)
    await sync_to_async(delete_obj.delete)()

# grab transcript data
async def get_recap_data(video_id):
    exists = await sync_to_async(StreamRecapData.objects.filter(video_id=video_id).exists)()
    if exists:
        recap_data = await sync_to_async(StreamRecapData.objects.get)(video_id=video_id)
    else:
        recap_data=None
    return recap_data







from rest_framework.renderers import JSONRenderer
from rest_framework import serializers
import asyncio


# Recaps Homepage display 
class RecapSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamRecapData
        exclude = ['raw_transcript_data', 'linked_transcript', 'transcript', 'summarized_chunks']
async def get_all_recaps():
    # Fetch all metadata asynchronously, deferring certain fields
    all_recap_data = await sync_to_async(
        lambda: list(StreamRecapData.objects.defer('raw_transcript_data', 'linked_transcript', 'transcript', 'summarized_chunks', 'text_chunks', 'text_chunks_summaries').all())
    )()
    
    all_recap_data.reverse()

    # Serialize the data
    serialized_data = await sync_to_async(lambda: RecapSerializer(all_recap_data, many=True).data)()

    return serialized_data




# Recaps Homepage display but only for video_characteristics and recap fields
class LimitedRecapSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamRecapData
        fields = ['video_id', 'video_characteristics', 'recap']
async def get_all_recaps_fast():
    # Fetch all metadata asynchronously, get only the video_characteristics and recap fields
    all_recap_data = await sync_to_async(
        lambda: list(StreamRecapData.objects.only('video_id','video_characteristics', 'recap').all())
    )()

    all_recap_data.reverse()

    # Serialize the data
    serialized_data = await sync_to_async(lambda: LimitedRecapSerializer(all_recap_data, many=True).data)()

    return serialized_data




# Recap Details Load
class RecapDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamRecapData
        fields=["video_id", "video_characteristics", "transcript", "recap", "text_chunks"]

async def get_fast_recap_details(video_id):
    recap_data=await sync_to_async(StreamRecapData.objects.only('video_id','video_characteristics', 'transcript', 'recap', "text_chunks").get)(video_id=video_id)
    serialized_data = await sync_to_async(lambda: RecapDetailsSerializer(recap_data).data)()

    return serialized_data



# Loading linked transcript data
class LinkedTranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamRecapData
        fields = ['linked_transcript']
async def get_linked_transcript(video_id):
    linked_transcript = await sync_to_async(lambda: StreamRecapData.objects.filter(video_id=video_id).values('linked_transcript').first())()

    if linked_transcript:
        serializer = LinkedTranscriptSerializer(data=linked_transcript)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        return serializer.validated_data
    else:
        return None
    
# Load the bigger/longer load time recap details
class SlowRecapDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamRecapData
        fields=["video_id", "video_characteristics", "transcript", "recap", "text_chunks", "chunk_annotations", "plot_clickable_area_data", "plot_image"]
async def get_slow_recap_details(video_id):
    recap_data=await sync_to_async(StreamRecapData.objects.only('video_id','video_characteristics', 'transcript', 'recap', "text_chunks", "chunk_annotations", "plot_clickable_area_data", "plot_image").get)(video_id=video_id)
    serialized_data = await sync_to_async(lambda: SlowRecapDetailsSerializer(recap_data).data)()

    return serialized_data


    



# Load plain transcript data
async def get_plain_transcript(video_id):
    # exclude all other fields .objects.only('transcript').get(pk=some_id)
    transcript = await sync_to_async(StreamRecapData.objects.only('transcript','text_chunks').get)(video_id=video_id)
    return transcript






from bs4 import BeautifulSoup
def find_time_at_char_count(linked_transcript, character_count):
    soup = BeautifulSoup(linked_transcript, 'html.parser')
    soup_list=soup.find_all('a')

    transcript_soup_character_counter=[]
    character_count_total=0
    temp_time=0
    for link in soup_list:
        link_text = link.get_text()
        character_count_total+=len(link_text)

        if link.get('href') is not None:
            temp_time=int(link['href'].split("t=")[-1].split("s")[0])

        transcript_soup_character_counter.append([character_count_total, temp_time])

    def find_nearest_time_at_character_count(transcript_soup_character_counter, character_count):
        # middle sort the list to get to the closest character count quickly
        
        l=0
        r=len(transcript_soup_character_counter)-1

        while l<r:
            m=(l+r)//2
            if transcript_soup_character_counter[m][0]<character_count:
                l=m+1
            else:
                r=m

        if l==0:
            return transcript_soup_character_counter[l][1]
        else:
            if abs(transcript_soup_character_counter[l][0]-character_count)<abs(transcript_soup_character_counter[l-1][0]-character_count):
                return transcript_soup_character_counter[l][1]
            else:
                return transcript_soup_character_counter[l-1][1]
            
    time_seconds=find_nearest_time_at_character_count(transcript_soup_character_counter, character_count)
    return time_seconds