import os
import requests
import random
from moviepy.editor import VideoFileClip

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def get_pexels_video(topic="Saudi Arabia nature", orientation="portrait"):
    headers = {"Authorization": PEXELS_API_KEY}
    # Cari video berdasarkan Topik Spesifik
    url = f"https://api.pexels.com/videos/search?query={topic}&per_page=10&orientation={orientation}"
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if not data.get('videos'):
        print(f"Video tentang '{topic}' tidak ditemukan.")
        return None

    # Pilih 1 video random
    video_data = random.choice(data['videos'])
    video_files = video_data['video_files']
    
    # Pilih kualitas HD (width >= 720) agar hemat kuota runner tapi tetap bagus
    chosen_file = sorted(video_files, key=lambda x: x['width'])[0]
    download_url = chosen_file['link']
    
    print(f"Downloading video ({topic}): {download_url}")
    
    r = requests.get(download_url)
    filename = "input_video.mp4"
    with open(filename, 'wb') as f:
        f.write(r.content)
        
    return filename

def process_video(input_file):
    output_file = "final_short.mp4"
    clip = VideoFileClip(input_file)
    
    # Durasi max 15 detik
    duration = min(clip.duration, 15) 
    clip = clip.subclip(0, duration)
    
    # Force Resize ke 9:16 (1080x1920)
    if clip.w > clip.h:
        clip = clip.crop(x1=clip.w/2 - clip.h*9/32, width=clip.h*9/16, height=clip.h)
    
    clip.write_videofile(output_file, codec="libx264", audio_codec="aac")
    return output_file
