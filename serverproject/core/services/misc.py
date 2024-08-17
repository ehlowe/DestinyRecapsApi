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

async def get_live_status_youtube(video_id):
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



import asyncio

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

async def get_live_status(video_id):
    live_status=False

    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')

        # Create a Service instance with ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        if "THIRD_PARTY_NOTICES" in service.path:
            service = Service(service.path.replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver.exe"))

        # Initialize the Chrome WebDriver with the specified service and options
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)

        # Go to the page
        driver.get("https://www.destiny.gg/bigscreen")
        await asyncio.sleep(5)

        # Now the page is fully loaded, including content loaded via JavaScript 
        html_content = driver.page_source
        
        # Check if stuff is live at all
        element = driver.find_element(By.CSS_SELECTOR, "#offline-text")

        offline_text_display_mode=element.value_of_css_property("display")
        if offline_text_display_mode=="none":
            live_status=True

        #html_content.split("https://www.youtube.com/embed/")[-1].split("?autoplay=")[0]

        driver.quit()
    except Exception as e:
        driver.quit()
        pass

    return live_status
