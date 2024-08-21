import datetime

from . import weekly_recaps

from destinyapp.models import WeeklyRecapData

from core import utils
# import sync to async
from asgiref.sync import sync_to_async

logic_trigger_day="Saturday"
weekly_recap_day="Friday"


async def attempt_weekly_recap():
    applied_date=datetime.datetime.now()
    global logic_trigger_day
    global weekly_recap_day
    # logic_trigger_day="Tuesday"
    # weekly_recap_day="Monday"

    if applied_date.strftime("%A")!=logic_trigger_day:
        print("Not the right day for a weekly recap")
        return
    else:
        # go back to the last friday
        applied_date=applied_date-datetime.timedelta(days=1)
        search_result = await sync_to_async(WeeklyRecapData.objects.filter)(applied_date=applied_date.strftime("%m/%d/%Y"))
        exists = await sync_to_async(search_result.exists)()

        if exists:
            print("Weekly Recap Already Exists")
            return
        else:
            await generate_week_recap(applied_date)


async def update_weekly_recaps():
    global logic_trigger_day
    days_to_go_back=100

    applied_dates=[]
    time_now=datetime.datetime.now()
    for i in range(days_to_go_back):
        applied_dates.append(time_now-datetime.timedelta(days=i))


    for applied_date in applied_dates:
        if applied_date.strftime("%A")!=logic_trigger_day:
            continue
        else:
            applied_date=applied_date-datetime.timedelta(days=1)
            search_result = await sync_to_async(WeeklyRecapData.objects.filter)(applied_date=applied_date.strftime("%m/%d/%Y"))
            exists = await sync_to_async(search_result.exists)()
            exists=False

            if exists:
                print("Weekly Recap Already Exists")
                continue
            else:
                await generate_week_recap(applied_date)


async def generate_week_recap(applied_date):
    # check if a weekly recap with the applied date already exists
    weeks_video_ids, week_hook, week_recap, week_image, stream_date_dict, earliest_date=await weekly_recaps.run_week_recap(applied_date)

    applied_date_str=applied_date.strftime("%m/%d/%Y")
    earliest_date_str=earliest_date.strftime("%m/%d/%Y")

    weekly_recap_data=await sync_to_async(WeeklyRecapData.objects.create)(
        applied_date=applied_date_str, 
        earliest_date=earliest_date_str,

        stream_dates=stream_date_dict,
        video_ids=weeks_video_ids, 

        week_recap=week_recap, 
        week_hook=week_hook, 
        week_image=week_image
    )

    await sync_to_async(weekly_recap_data.save)()
    print("Weekly Recap Data Saved")
        