import os
import sys

# Django imports
from django.http import JsonResponse
from django.core.cache import cache

# Django Rest Framework imports
from rest_framework.response import Response

# define the boolean values
def str_to_bool(value):
    return value.lower() in ('true', '1', 't', 'y', 'yes')
web_check=str_to_bool(os.environ.get("web_check",""))
redo_enabled=str_to_bool(os.environ.get("redo_enabled",""))
delete_enabled=str_to_bool(os.environ.get("delete_enabled",""))


# Custom Imports
#from destinyapp.middleware import password_checker
from destinyapp.customlibrary import utils

recap_generate_cache_lock_id = 'auto_recaps_generator_lock'


from destinyapp.customlibrary import controller
from rest_framework import serializers
from destinyapp.models import StreamRecapData
from destinyapp.customlibrary import services

from destinyapp.middleware import password_checker



# make a serializer class
class StreamRecapDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamRecapData
        fields = '__all__'




import asyncio
from rest_framework.decorators import api_view


# PAGE LOADING VIEWS
async def get_all_recaps(request):
    filled_meta_data = await utils.get_all_recaps()
    return JsonResponse(filled_meta_data, safe=False)

async def get_linked_transcript(request):
    video_id=request.GET.get("video_id")
    linked_transcript=await utils.database_operations.get_linked_transcript(video_id)
    return JsonResponse(linked_transcript, safe=False)

async def get_recap_details(request):
    video_id=request.GET.get("video_id")
    recap_details=await utils.database_operations.get_recap_details(video_id)
    return JsonResponse(recap_details, safe=False)



# Search View
async def search(request):
    video_id=request.GET.get("video_id")
    query=request.GET.get("query")
    search_results=await services.search(video_id, query)
    return JsonResponse(search_results, safe=False)








# AUTO RECAPS VIEW
@password_checker
async def auto_recaps_request(request):    
    # make thread for auto_recaps_generator
    recap_generation_started=enqueue_auto_recaps_generation()

    if recap_generation_started:
        return JsonResponse({"response":"Recaps Generation Started"})
    else:
        return JsonResponse({"response":"Recaps Generation Already Running"})
def enqueue_auto_recaps_generation():
    if not cache.get(recap_generate_cache_lock_id):
        cache.set(recap_generate_cache_lock_id, True, timeout=7200)
        asyncio.create_task(cache_locked_recap_generate())
        return True
    else:
        return False
async def cache_locked_recap_generate():
    try:
        await controller.auto_recap_controller.run()
    except Exception as e:
        print(e)

    cache.delete('auto_recaps_generator_lock')
    print("DELETED CACHE LOCK,  AUTO RECAPS FINISHED")








