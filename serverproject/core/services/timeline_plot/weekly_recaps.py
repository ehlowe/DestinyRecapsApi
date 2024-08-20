
import requests
import io
import base64
import datetime

import PIL



from core import utils
from destinyapp.models import StreamRecapData

async def run_week_recap(applied_date):
    limited_recap_data=await utils.get_all_recaps_fast()
    stream_rundowns, weeks_video_idss=await get_week_context_prompt(limited_recap_data, applied_date)

    cost=0
    week_recap, temp_cost=await generate_week_recap(stream_rundowns)
    cost+=temp_cost

    week_hook, temp_cost=await generate_week_hook(stream_rundowns)
    cost+=temp_cost

    week_image, temp_cost=await generate_week_image(stream_rundowns)
    cost+=temp_cost








async def get_week_context_prompt(limited_recap_data, applied_date):
    earliest_stream_in_zone=applied_date-datetime.timedelta(days=7)
    stream_date_dict={}
    weeks_video_ids=[]
    for recap in limited_recap_data:
        # Get the stream date
        stream_recap_limited=StreamRecapData(**recap)
        stream_date=stream_recap_limited.video_characteristics.get('date',"")
        if stream_date=="":
            title=stream_recap_limited.video_characteristics.get("title","")
            stream_date=title.split("Stream Date~")[-1].strip()
        
        #use datetime to check if the date is valid
        try:
            stream_date=datetime.datetime.strptime(stream_date, "%m/%d/%Y")
        except ValueError:
            continue
        
        # Check if the stream is within the week
        if stream_date>=earliest_stream_in_zone and stream_date<=applied_date:
            weeks_video_ids.append(stream_recap_limited.video_id)
            stream_date_dict[stream_recap_limited.video_id]=stream_date



    # Get the prompt context for the full week
    full_stream_recap_datas=[]
    stream_rundowns="Today is "+str(datetime.datetime.now().strftime("%A"))+"\nStream Rundowns Start Below:\n\n"
    for id in weeks_video_ids[::-1]:
        try:
            stream_recap_data=await utils.get_recap_data(id)
            stream_rundowns+=get_stream_rundown(stream_recap_data, stream_date_dict)+"\n\n"
            full_stream_recap_datas.append(stream_recap_data)
        except Exception as e:
            pass
    return stream_rundowns, weeks_video_ids


def get_stream_rundown(full_recap, stream_date_dict):
    abstractions=full_recap.plot_object["abstractions"]
    stream_rundown="Stream Title: "+full_recap.video_characteristics["title"]+"\nStream Date: "+stream_date_dict[full_recap.video_id].strftime("%A")+"\nTOPICS PROPORTION AND CONTENT:\n"
    abstraction_rundowns=""
    for key, value in abstractions.items():
        if key!="non categorized":
            abstraction_rundown="   Topic: "+key+" | Relative Proportion: "+str(int(value["size"]*100))+"%\nCONTENT: "+value["recap"]
            abstraction_rundowns+=abstraction_rundown+"\n\n"

    stream_rundown+=abstraction_rundowns
    return stream_rundown
















# # # Generative Requests
async def generate_week_recap(stream_rundowns):
    system_prompt="""The user will give you a stream rundown for all the streams of the last week and your job is to make a week recap.

Don't talk about percentages of topics or the exact date, use the day of the week when referring to the stream date.

Your recap should be a 1 paragraph 3-5 sentence summary of what happened with as much specifics as possible. Be informal to condense the content as it doesn't need to be gramatically correct. SPECIFICS ARE KEY."""

    user_prompt="Here are all the stream rundowns:\n"+stream_rundowns

    prompt=[{"role":"system", "content": system_prompt}, {"role":"user", "content": stream_rundowns}]

    week_recap, temp_cost=await utils.async_response_handler(
        prompt,
        utils.ModelNameEnum.claude_3_5_sonnet
    )

    return week_recap, temp_cost

async def generate_week_hook(stream_rundowns):
    system_prompt="""The user will give you a stream rundown for all the streams of the last week and your job is to make a headline hook for the week. It should be more like topics separated by commas and not a full sentence.

Do not say anything other than the hook and get right into it. It should be max 3 items."""

    user_prompt="Here are all the stream rundowns:\n"+stream_rundowns

    prompt=[{"role":"system", "content": system_prompt}, {"role":"user", "content": stream_rundowns}]

    week_hook, temp_cost=await utils.async_response_handler(
        prompt,
        utils.ModelNameEnum.claude_3_5_sonnet
    )

    return week_hook, temp_cost

async def generate_week_image(stream_rundowns):
    system_prompt="""The user will give you a stream rundown for all the streams of the last week and your job is to make a prompt for an image generator to symbolize the week.
    
    Include nothing else in your response besides what will be directly placed in the image generation prompt."""

    user_prompt="Here are all the stream rundowns:\n"+stream_rundowns

    prompt=[{"role":"system", "content": system_prompt}, {"role":"user", "content": stream_rundowns}]

    week_image_prompt, temp_cost=await utils.async_response_handler(
        prompt,
        utils.ModelNameEnum.claude_3_5_sonnet
    )


    image_url=await utils.generate_image(week_image_prompt)
    response = requests.get(image_url[0])
    img_b64=base64.b64encode(response.content).decode('utf-8')


    # downscale the iamge to be 400x400
    img = PIL.Image.open(io.BytesIO(response.content))
    img = img.resize((400, 400))
    
    # make the image a base64 string 
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return img_b64, temp_cost+0.03

