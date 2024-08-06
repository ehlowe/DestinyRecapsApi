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
    if "THIRD_PARTY_NOTICES" in service.path:
        service = Service(service.path.replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver.exe"))
    
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
        video_ids.reverse()

        # Close the browser
        driver.quit()
        print("Driver closed")

        return video_ids

    except Exception as e:
        driver.quit()
        print("Driver closed, Error: ",e)

        video_ids=[]




async def web_get_recap_image():
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

    try:
        # Go to the page
        # driver.get("https://vyneer.me/vods/")

        driver.get("http://localhost:5173/details?video_id=OqVH_MTBQ6k")

        await asyncio.sleep(5)

        # Now the page is fully loaded, including content loaded via JavaScript 
        html_content = driver.page_source



        # Get the image
        svg_element = driver.find_element(By.CSS_SELECTOR, "svg")

        svg_element.screenshot("recap_image.png")






        # Close the browser
        driver.quit()
        print("Driver closed")

    except Exception as e:
        driver.quit()
        print("Driver closed")