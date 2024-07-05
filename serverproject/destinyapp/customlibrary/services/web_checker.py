import asyncio
import re

# Webdriver on vyneer website
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By




async def web_view_recent_stream_ids():
    pattern = r"https://youtu.be/([\w-]+)"

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    # Create a Service instance with ChromeDriverManager
    service = Service(ChromeDriverManager().install())

    # Initialize the Chrome WebDriver with the specified service and options
    driver = webdriver.Chrome(service=service, options=options)

    driver.implicitly_wait(10)

    try:
        # Go to the page
        driver.get("https://vyneer.me/vods/")

        await asyncio.sleep(5)

        # Now the page is fully loaded, including content loaded via JavaScript 
        html_content = driver.page_source
        video_ids = [match.group(1) for match in re.finditer(pattern, html_content)]
        print("ALL YT IDS:",video_ids)
        video_ids=video_ids[:3]

        # Close the browser
        driver.quit()
        print("Driver closed")

        return video_ids

    except Exception as e:
        driver.quit()
        print("Driver closed, Error: ",e)

        video_ids=[]