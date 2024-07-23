# Base Imports
import os
import sys
import traceback
import asyncio


# Django imports
from django.http import JsonResponse
from django.core.cache import cache
recap_generate_cache_lock_id = 'auto_recaps_generator_lock'
download_lock_id = 'download_lock'


# Django Rest Framework imports
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.decorators import api_view


# define the boolean values
def str_to_bool(value):
    return value.lower() in ('true', '1', 't', 'y', 'yes')
web_check=str_to_bool(os.environ.get("web_check",""))
redo_enabled=str_to_bool(os.environ.get("redo_enabled",""))
delete_enabled=str_to_bool(os.environ.get("delete_enabled",""))


# Custom Imports
from destinyapp.customlibrary import utils
from destinyapp.customlibrary import controller
from destinyapp.customlibrary import services
from destinyapp.models import StreamRecapData
from destinyapp.middleware import password_checker


# Make a serializer class
class StreamRecapDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamRecapData
        fields = '__all__'


# PAGE LOADING VIEWS
async def get_all_recaps(request):
    filled_meta_data = await utils.get_all_recaps_fast()
    return JsonResponse(filled_meta_data, safe=False)

async def get_linked_transcript(request):
    video_id=request.GET.get("video_id")
    linked_transcript=await utils.database_operations.get_linked_transcript(video_id)
    return JsonResponse(linked_transcript, safe=False)

async def get_recap_details(request):
    video_id=request.GET.get("video_id")
    recap_details=await utils.database_operations.get_fast_recap_details(video_id)
    return JsonResponse(recap_details, safe=False)

async def get_slow_recap_details(request):
    video_id=request.GET.get("video_id")
    recap_details=await utils.database_operations.get_slow_recap_details(video_id)
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

    # print the error if any with as much information as possible
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Controller error")
        print(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        print(e)
        print("End of Controller error")

    cache.delete('auto_recaps_generator_lock')
    print("DELETED CACHE LOCK,  AUTO RECAPS FINISHED")






# AUTO RECAPS VIEW
@password_checker
async def recap_update_request(request):    
    # make thread for auto_recaps_generator
    recap_generation_started=enqueue_recap_update()

    if recap_generation_started:
        return JsonResponse({"response":"Recaps Update Started"})
    else:
        return JsonResponse({"response":"Recaps Update Already Running"})
def enqueue_recap_update():
    if not cache.get(recap_generate_cache_lock_id):
        cache.set(recap_generate_cache_lock_id, True, timeout=7200)
        asyncio.create_task(cache_locked_recap_update())
        return True
    else:
        return False
async def cache_locked_recap_update():
    try:
        await controller.update_controller.update()

    # print the error if any with as much information as possible
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Controller update error")
        print(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        print(e)
        print("End of Controller update error")

    cache.delete(recap_generate_cache_lock_id)
    print("DELETED CACHE LOCK,  UPDATE FINISHED")







# Download Stream Recap Data
async def serialize_stream_recap_data(stream_recap_data):
    serialized_data = StreamRecapDataSerializer(stream_recap_data).data
    return serialized_data

async def download_stream_recap_data(request):
    def check_dl_cache_lock(cache_lock_id):
        if not cache.get(cache_lock_id):
            cache.set(cache_lock_id, True, timeout=7200)
            return True
        else:
            return False
    
    dl_locked=check_dl_cache_lock(download_lock_id)
    try:
        if not dl_locked:
            video_id=request.GET.get("video_id")
            print("video_id", video_id)
            stream_recap_data=await utils.database_operations.get_recap_data(video_id)

            if stream_recap_data:
                serialized_data=await serialize_stream_recap_data(stream_recap_data)
                return JsonResponse(serialized_data, safe=False)
            else:
                test_return={"status":"no data"}
                return JsonResponse(test_return, safe=False)
        else:
            test_return={"status":"locked someone else is downloading"}
            return JsonResponse(test_return, safe=False)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("Download error")
        print(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        print(e)
        print("End of Download error")
        # remove lock if error
        try:
            cache.delete(download_lock_id)
        except:
            pass
        return JsonResponse({"status":"error"}, safe=False)
    






# Delete Stream Recap Data
@password_checker
async def delete_stream_recap_data(request):
    video_id=request.GET.get("video_id")
    print("video_id", video_id)
    if not delete_enabled:
        return JsonResponse({"status":"deletion not enabled"}, safe=False)
    await utils.database_operations.delete_stream_recap_data(video_id)
    return JsonResponse({"status":"deleted"}, safe=False)


