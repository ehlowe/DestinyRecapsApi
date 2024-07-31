from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import os
import asyncio

async def make_plot_save_request(video_id):
    # Set chromedriver options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    # Create a Service instance with ChromeDriverManager
    service = Service(ChromeDriverManager().install())
    if "THIRD_PARTY_NOTICES" in service.path:
        service = Service(service.path.replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver.exe"))

    driver = webdriver.Chrome(service=service, options=options)

    driver.implicitly_wait(10)

    if os.environ.get("mode","")=="production":
        driver.get("https://destinyrecaps.com/backend?video_id="+video_id+"&p="+os.environ['req_pass'])
    else:
        driver.get("http://localhost:5173/backend?video_id=OqVH_MTBQ6k&p="+os.environ['req_pass'])

    await asyncio.sleep(5)

    driver.quit()


