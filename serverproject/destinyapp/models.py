from django.db import models
import json

# Create your models here.
class TranscriptData(models.Model):
    video_id = models.CharField(max_length=100)

    video_characteristics = models.JSONField(default=dict)

    transcript = models.CharField(max_length=1000000,default="")
    linked_transcript = models.CharField(max_length=100000000,default="")
    raw_transcript_data = models.JSONField(default=dict)

    text_chunks = models.JSONField(default=list)
    text_chunks_summaries = models.JSONField(default=list)

    summarized_chunks = models.JSONField(default=list)

    meta= models.CharField(max_length=1000000,default="")
    meta_markdown= models.CharField(max_length=100000,default="")

    # returns a string representation of the object
    def __str__(self):
        data_str=""
        data_str+="Video ID: "+self.video_id+", "

        data_str+="Video Characteristics:"
        for key in self.video_characteristics:
            data_str+=key+": "+str(self.video_characteristics[key])+", "
        
        data_str+="Transcript: "+self.transcript+", "

        # data_str+="Nearest Times:"
        # for key in self.nearest_times:
        #     data_str+=key+": "+str(self.nearest_times[key])+", "
        
        data_str+="Text Chunks:"
        for chunk in self.text_chunks:
            data_str+=chunk+", "

        data_str+="Summarized Chunks:"

        data_str+=json.dumps(self.summarized_chunks)+", "

        data_str+="Meta: "+self.meta

        return data_str
        

        



class BotData(models.Model):
    bot_id=models.CharField(max_length=100)

    last_time_ran = models.DateTimeField(default="")