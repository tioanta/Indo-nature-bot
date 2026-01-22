import os
import requests
import random
from moviepy.editor import VideoFileClip

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def get_pexels_video(topic="Nature Scenery", orientation="portrait"):
    headers = {"Authorization": PEXELS_API_KEY}
    
    # Search query ke Pexels
    print(f"Searching Pexels for: {topic}")
    url = f"https://api.pexels.com/videos/search?query={topic}&per_page=15&orientation={orientation}"
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except Exception as e:
        print(f"Error connecting to Pexels: {e}")
        return None
    
    if not data.get('videos'):
        print(f"Maaf, video tentang '{topic}' tidak ditemukan di Pexels.")
        return None

    # Pilih 1 video random dari hasil pencarian
    video_data = random.choice(data['videos'])
    video_files = video_data['video_files']
    
    # Pilih file dengan kualitas HD (lebar min 720px) agar jernih tapi ringan
    # Kita sort dari yang terkecil ke terbesar, lalu ambil yang cukup besar
    valid_files = [v for v in video_files if v['width'] >= 720]
    if not valid_files:
        valid_files = video_files # Fallback jika tidak ada HD
        
    chosen_file = valid_files[0]
    download_url = chosen_file['link']
    
    print(f"Downloading video: {download_url}")
    
    r = requests.get(download_url)
    filename = "input_video.mp4"
    with open(filename, 'wb') as f:
        f.write(r.content)
        
    return filename

def process_video(input_file):
    output_file = "final_short.mp4"
    clip = VideoFileClip(input_file)
    
    # Durasi max 15 detik (Shorts ideal)
    duration = min(clip.duration, 15) 
    clip = clip.subclip(0, duration)
    
    # Resize ke 9:16 (Vertikal)
    # Jika video aslinya landscape, kita crop tengahnya
    if clip.w > clip.h:
        clip = clip.crop(x1=clip.w/2 - clip.h*9/32, width=clip.h*9/16, height=clip.h)
    
    clip.write_videofile(output_file, codec="libx264", audio_codec="aac")
    return output_file
