# DIRECTORY SET
import os
import sys
from pathlib import Path
base_dir=Path(os.getcwd()).parent
# os.chdir(os.path.join(base_dir, 'serverproject'))
os.chdir(base_dir)
print(os.getcwd())

# Load dotenv
import dotenv
dotenv.load_dotenv()

# DJANGO SETUP
import django
sys.path.append(os.path.abspath(''))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "serverproject.settings")
django.setup()

# Import async modules
import asyncio
from asgiref.sync import sync_to_async

# Import display modules
from IPython.display import display, Markdown

# Import other modules
import faiss

# import reloading
from importlib import reload

video_id="Dc9SeVm7efA"


from destinyapp.models import StreamRecapData

from core import services
from core import utils
from core import controllers


if __name__ == "__main__":
    asyncio.run(services.video_and_transcript.download_video(video_id))
    