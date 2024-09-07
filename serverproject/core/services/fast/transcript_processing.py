
def process_yt_transcript(yt_transcript, video_id):
    linked_transcript=""
    transcript=""
    new_lines=0
    word_count=0
    for utterance in yt_transcript:
        text=utterance["text"]
        start=int(utterance["start"]*1000)
        base_link="https://www.youtube.com/watch?v={video_id}&t={time}s"
        link=f"https://youtu.be/{video_id}?t={start}"
        linked_transcript+="<a href=\""+link+"\" target=\"_blank\" class=\"underline-hover\">"+text+"</a>"
        transcript+=text

    return transcript, linked_transcript