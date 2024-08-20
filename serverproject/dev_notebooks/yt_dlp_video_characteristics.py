import subprocess
import datetime
import asyncio

async def get_video_characteristics(video_id):
    #yt-dlp --skip-download --print "%(upload_date)s | %(channel)s | %(title)s" "VIDEO_URL"
    title=""
    channel=""
    upload_date=""

    try:
        cmd=f'yt-dlp --skip-download --print "%(upload_date)s |]| %(channel)s |]| %(title)s" "https://www.youtube.com/watch?v={video_id}"'
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print("Error in get_video_metadata_cmd", e)
        try:
            print("CMD RESULT:", result)
        except:
            pass
        return {"title": title, "channel": channel, "date": upload_date}
    
    try:
        data=result.stdout.decode("utf-8")
        upload_date, channel, title=data.split("|]|")
    except Exception as e:
        print("Error in parsing video_characteristics", e)
        try:
            print("DATA:", data)
            print("RESULT:", result)
        except:
            pass
        return {"title": title, "channel": channel, "date": upload_date}
    
    try:
        date_obj=datetime.datetime.strptime(upload_date.strip(), "%Y%m%d")
        upload_date=date_obj.strftime("%m/%d/%Y")
    except:
        pass


    title=title.strip()
    if upload_date!="":
        title+="\nStream Date~ "+upload_date

    channel=channel.strip()

    return {"title": title, "channel": channel, "date": upload_date}


video_id="n4L4Z0Kx004"

# run the function
asyncio.run(get_video_characteristics(video_id))
