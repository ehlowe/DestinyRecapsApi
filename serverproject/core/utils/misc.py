

def check_if_channel(sort_channel, video_characteristics):
    channel=video_characteristics.get("channel","")
    if (channel!="") and (channel!=sort_channel):
        return False
    return True