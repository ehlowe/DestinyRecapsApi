import datetime

import yt_dlp as youtube_dl
from pytube import YouTube

async def get_video_metadata(video_id):
    ydl_opts = {}
    full_title=""
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            info_dict_g=info_dict
            upload_date = info_dict['upload_date']
            upload_date
            date_obj=datetime.datetime.strptime(upload_date, "%Y%m%d")
            date_str=date_obj.strftime("%m/%d/%Y")
            title=info_dict["title"]
            full_title=title+"\nStream Date~ "+date_str
    except Exception as e:
        pass
    return full_title

async def get_live_status(video_id):
    # Get video
    url = 'https://www.youtube.com/watch?v='+video_id
    yt = YouTube(url)

    # Fill attributes
    try:
        for attr in dir(yt):
            value=getattr(yt, attr)
    except Exception as e:
        pass

    # Get Live status
    try:
        vid_info=getattr(yt, "_vid_info")
        live_bool=vid_info["videoDetails"]["isLive"]
    except Exception as e:
        live_bool=False
    return live_bool