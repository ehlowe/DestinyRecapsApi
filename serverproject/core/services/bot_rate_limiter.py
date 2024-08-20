from django.http import JsonResponse  
from destinyapp.models import BotData
import datetime
from asgiref.sync import sync_to_async
import os

async def bot_run_check() -> bool:
    time_between_bot_runs=int(os.environ.get("time_between_bot_runs","3600"))

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
        if (datetime.datetime.strptime(parsed_time_now_str, "%Y-%m-%d %H:%M:%S")-datetime.datetime.strptime(parsed_bot_last_ran_str, "%Y-%m-%d %H:%M:%S")).seconds<time_between_bot_runs:
            return False
        else:
            bot_data.last_time_ran=time_now_str
            save_function=bot_data.save
            await sync_to_async(save_function)()
    else:
        # create and save the bot data with the current time if the bot data doesn't exist
        bot_data=BotData(bot_id="baseid",last_time_ran=str(datetime.datetime.now()))
        save_function=bot_data.save
        await sync_to_async(save_function)()

    return True