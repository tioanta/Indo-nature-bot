import os
import requests
import random
from moviepy.editor import VideoFileClip
import json

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def get_pexels_video(query="Saudi Arabia nature", orientation="portrait"):
    headers = {"Authorization": PEXELS_API_KEY}
    # Cari video (ambil 1 random dari 15 hasil teratas)
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=15&orientation={orientation}"
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if not data['videos']:
        print("Video tidak ditemukan.")
        return None

    video_data = random.choice(data['videos'])
    video_files = video_data['video_files']
    
    # Pilih kualitas HD terendah agar ringan diproses
    # Sortir berdasarkan width, ambil yang mendekati 720p/1080p
    chosen_file = sorted(video_files, key=lambda x: x['width'])[0] 
    download_url = chosen_file['link']
    
    print(f"Downloading video: {download_url}")
    
    # Download Video
    r = requests.get(download_url)
    filename = "input_video.mp4"
    with open(filename, 'wb') as f:
        f.write(r.content)
        
    return filename

def process_video(input_file):
    output_file = "final_short.mp4"
    
    clip = VideoFileClip(input_file)
    
    # Potong durasi max 15-20 detik agar aman untuk Shorts
    duration = min(clip.duration, 15) 
    clip = clip.subclip(0, duration)
    
    # Resize ke 1080x1920 (9:16) jika belum
    # Karena kita request 'portrait' dari pexels, biasanya sudah oke.
    # Kita force resize aspect ratio biar aman.
    if clip.w > clip.h:
        # Jika landscape, crop tengah
        clip = clip.crop(x1=clip.w/2 - clip.h*9/32, width=clip.h*9/16, height=clip.h)
    
    clip.write_videofile(output_file, codec="libx264", audio_codec="aac")
    return output_file

if __name__ == "__main__":
    vid = get_pexels_video()
    if vid:
        process_video(vid)
