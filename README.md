# DestinyRecapsApi
This is the API server for the DestinyRecaps website, the frontend github is here: https://github.com/ehlowe/DestinyRecapsWeb.

## How to use
This server fetches Destiny's youtube streams and then runs a summarization on it to recap the stream where its goal is to capture the main topics dicussed as well as many of the smaller topics. That recap is sent out in the news channel on the discord with the website link and youtube video. You can use the website's vector embedding search to find where the recap topics appear in the video.

## How it works
This uses a diarized transcript where Destiny's speach is annotated. This means the chatbot has context of what Destiny, specifically, says. Without this you just get a sense of what was being said but not what Destiny said or what Destiny was talking about (this is especially important when Destiny is watching videos). 

Once the transcript is made it is chunked and vectorized for search, summarized in segments, and then using the summarized segments it is recaped. The AI models are subject to change but this project currently uses claude-sonnet 3.5 for all LLM purposes and Openai's 'text-embedding-3-large' for vector embeddings.

