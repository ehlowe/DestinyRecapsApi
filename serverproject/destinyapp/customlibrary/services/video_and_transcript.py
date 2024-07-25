import os
import asyncio

import yt_dlp
from moviepy.editor import AudioFileClip, concatenate_audioclips

import assemblyai as aai



# Video Download
async def download_video(video_id):#, output_folder, output_name):
    """Takes a video id, downloads the video from youtube, concatenates the video with a pre-recorded audio file of the target speaker
    
    This allows targeted diarization of the audio file."""

    # Download video
    def download_video_thread(video_id):
        folder_path="destinyapp/working_folder/working_audio/"

        # Set download parameters
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': folder_path+'raw'+'.%(ext)s',#os.path.join(output_folder,output_name)+'.%(ext)s',
            'age_limit': 21, 
        }

        # delete previous audio file with 'raw' in the name
        audio_dir_files=os.listdir(folder_path)
        for file_name in audio_dir_files:
            if 'raw' in file_name:
                os.remove(folder_path+file_name)
                break

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(['https://youtu.be/'+video_id])

        # open destinyspeaking.mp3
        destiny_speech_path=folder_path+"destinyspeaking.mp3"
        destiny_speech = AudioFileClip(destiny_speech_path)
        audio_dir_files=os.listdir(folder_path)

        # find the audio file with 'raw' in the name
        for file_name in audio_dir_files:
            if 'raw' in file_name:
                youtube_audio_path=folder_path+file_name
                break

        # Concatentate the two audio files
        youtube_video = AudioFileClip(youtube_audio_path)
        merged_audio = concatenate_audioclips([destiny_speech, youtube_video])
        merged_audio.write_audiofile(folder_path+"merged_audio.mp3")
        print("download thread finished")
        return

    await asyncio.to_thread(download_video_thread, video_id)
    print("download thread closed")

# Raw Transcript Generation
async def generate_assembly_transcript():
    """
    Creates a transcript of the audio file without any processing"""
    folder_path="destinyapp/working_folder/working_audio/"
    file_path=folder_path+"merged_audio.mp3"
    def transcribe_audio_thread(file_path):
        transcriber = aai.Transcriber()
        config = aai.TranscriptionConfig(speaker_labels=True, speech_model="nano")
        # config = aai.TranscriptionConfig(speaker_labels=True, speech_model="best")
        transcript = transcriber.transcribe(file_path, config=config)
        return transcript.json_response["utterances"]
    print("Starting assembly transcription thread")
    thread_response=await asyncio.to_thread(transcribe_audio_thread, file_path)
    print("Finished assembly transcription thread")
    return thread_response










import copy

def clean_speech_segment(speech_segment, diarization_word_count):
    utterances=speech_segment["words"]
    corrected_text=""
    corrected_words=[]
    corrected_text_list=[]
    corrected_start=utterances[diarization_word_count]["start"]
    for utterance in utterances[diarization_word_count:]:
        corrected_words.append(utterance)
        corrected_text_list.append(utterance["text"])

    corrected_text=" ".join(corrected_text_list)
    speech_segment["words"]=corrected_words
    speech_segment["text"]=corrected_text
    speech_segment["start"]=corrected_start
    return speech_segment
def negative_fix(input_number):
    if input_number<0:
        return 0
    return input_number

# Process Raw Transcript into transcript and linked transcript
async def process_raw_transcript(input_raw_transcript, video_id):
    """
    Parses out the speaking target initial speech segment and corrects the time offsets of the transcript.
    
    Returns a dictionary of the 'transcript' and 'linked_transcript'"""

    # make deep copy of raw transcript
    raw_transcript=copy.deepcopy(input_raw_transcript)

    diarization_annotation_length=187.4

    # Diarization Cutoff
    diarization_cutoff=True
    if diarization_cutoff:
        # Words which end the speech segment for diarization targeting
        end_of_cuttof=["chief", "looks"]

        # Get portion of speech segment for determining who starts

        segment_index_at_transition=0
        for speech_segment in raw_transcript:
            if (speech_segment["end"]/1000)>diarization_annotation_length-5:
                break
            segment_index_at_transition+=1


        last_several_words=["",""]
        word_count=0
        for utterance in speech_segment["words"]:
            # check the last 3 sequence
            last_several_words=[last_several_words[1],utterance["text"]]
            word_count+=1

            # if end sequence is found
            if last_several_words==end_of_cuttof:
                print(utterance)
                print(word_count)
                print(len(speech_segment["words"]))

                # if the end sequence is NOT the end of the speech segment then destiny starts
                if (word_count+2)<len(speech_segment["words"]):
                    print("Destiny starts")
                    speech_segment=clean_speech_segment(speech_segment, word_count+1)
                    raw_transcript=raw_transcript[(segment_index_at_transition):]
                    raw_transcript[0]=speech_segment
                else:
                    print("Destiny doesn't start")
                    raw_transcript=raw_transcript[(segment_index_at_transition+1):]
                break
        print("Finished diarization cutoff")
        
        # Adjust time offsets
        time_offset=(186*1000)+1500
        for i in range(len(raw_transcript)):
            speech_segment=raw_transcript[i]
            speech_segment["start"]=negative_fix(speech_segment["start"]-time_offset)
            speech_segment["end"]=negative_fix(speech_segment["end"]-time_offset)
            for i in range(len(speech_segment["words"])):
                speech_segment["words"][i]["start"]=negative_fix(speech_segment["words"][i]["start"]-time_offset)
                speech_segment["words"][i]["end"]=negative_fix(speech_segment["words"][i]["end"]-time_offset)
        
    # Create Base Transcript
    transcript=""
    for i in range(len(raw_transcript)):
        utterance=raw_transcript[i]
        speaker=utterance["speaker"]
        if speaker=="A":
            speaker="Destiny"

        prev_word_stop=None
        utterance_text=""
        for j in range(len(raw_transcript[i]["words"])):
            if prev_word_stop and ((raw_transcript[i]["words"][j]["start"]-prev_word_stop)>2000):
                raw_transcript[i]["words"][j]["text"]="\n"+raw_transcript[i]["words"][j]["text"]
            utterance_text+=raw_transcript[i]["words"][j]["text"]+" "
            prev_word_stop=raw_transcript[i]["words"][j]["end"]

        raw_transcript[i]["text"]=utterance_text
        transcript+=speaker+": "+raw_transcript[i]["text"]
        transcript+="\n\n"

    # Create Linked Transcript
    linked_transcript=""
    new_lines=0
    word_count=0
    for utterance in raw_transcript:#[0:12]:
        speaker=utterance["speaker"]
        if speaker=="A":
            speaker="Destiny"
        text=utterance["text"]
        base_link="https://www.youtube.com/watch?v={video_id}&t={time}s"
        html_transcript_text=""
        for i, word in enumerate(utterance["words"]):
            word_count+=1
            time_start=int(word["start"]/1000)
            link=f"https://youtu.be/{video_id}?t={time_start}"
            temp_text=word['text']+" "
            #</a><a href="https://www.youtube.com/watch?v=PTjCp3RJ4ag&t=5416s" target="_blank">
            if i==len(utterance["words"])-1:
                temp_text=temp_text.strip()+"\n\n"
            
            added_link="<a href=\""+link+"\" target=\"_blank\" class=\"underline-hover\">"+temp_text+"</a>"

            # if it is the last word in the utterance
            if i!=len(utterance["words"])-1:
                if "\n" in temp_text:
                    new_lines+=1
                    added_link="<br/>"+added_link

            # add the link to the html_transcript_text
            html_transcript_text+=added_link

                
        linked_transcript+=speaker+": "+html_transcript_text
        linked_transcript+="<br/><br/>"
        new_lines+=2
    
    return transcript, linked_transcript