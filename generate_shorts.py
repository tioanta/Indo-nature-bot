import os
import requests
import random
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import json

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def get_music(topic):
    """Cari musik singkat yang sesuai vibe"""
    print(f"   [Shorts] Mencari BGM untuk: {topic}")
    topic_lower = topic.lower()
    
    if "manchester" in topic_lower or "football" in topic_lower:
        keywords = ["Epic sport cinematic ogg", "Stadium drums ogg", "Energetic rock ogg"]
    elif "masjid" in topic_lower or "makkah" in topic_lower:
        keywords = ["Middle eastern ambient ogg", "Islamic ney flute ogg", "Desert wind ambient ogg"]
    elif "japan" in topic_lower or "tokyo" in topic_lower:
        keywords = ["Lofi japan ogg", "City pop instrumental ogg", "Koto ambient ogg", "Rain jazz ogg"]
    else:
        keywords = ["Cinematic ambient ogg"]

    # Gunakan fungsi search Wikimedia yg sama (copy logic simple di sini)
    api_url = "https://commons.wikimedia.org/w/api.php"
    headers = {'User-Agent': 'BotShorts/1.0'}
    
    for kw in keywords:
        params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": kw, "gsrnamespace": 6, "prop": "imageinfo", "iiprop": "url"}
        try:
            r = requests.get(api_url, params=params, headers=headers).json()
            pages = list(r["query"]["pages"].values())
            if pages:
                url = pages[0]["imageinfo"][0]["url"]
                # Download
                r_audio = requests.get(url, stream=True, headers=headers)
                with open("bg_shorts.ogg", 'wb') as f:
                    for chunk in r_audio.iter_content(chunk_size=1024): f.write(chunk)
                return "bg_shorts.ogg"
        except:
            continue
    return None

def get_vertical_video(topic):
    """Cari video Pexels dengan orientasi PORTRAIT"""
    print(f"   [Shorts] Mencari Video Vertical: {topic}")
    headers = {"Authorization": PEXELS_API_KEY}
    
    # Keyword mapping
    topic_lower = topic.lower()
    if "manchester" in topic_lower:
        query = "football stadium red"
    elif "masjid" in topic_lower:
        query = "mosque architecture" # Pexels mungkin terbatas utk Masjidil Haram spesifik, pakai generic mosque/architecture
    elif "japan" in topic_lower:
        query = "Tokyo street night"
    else:
        query = topic

    # Tambahkan parameter orientation=portrait
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=5"
    
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        if data.get('videos'):
            video = random.choice(data['videos'])
            # Pilih file HD tapi ringan
            files = video['video_files']
            # Cari yang width < height (Vertical)
            vertical_files = [v for v in files if v['width'] < v['height'] and v['width'] >= 720]
            if not vertical_files: vertical_files = files
            
            download_url = vertical_files[0]['link']
            with open("raw_shorts.mp4", 'wb') as f:
                f.write(requests.get(download_url).content)
            return "raw_shorts.mp4"
    except Exception as e:
        print(f"Error Pexels: {e}")
    return None

def create_short_video(music_path, topic, duration=58):
    output_file = "final_shorts.mp4"
    try:
        # 1. Audio
        audio = AudioFileClip(music_path)
        if audio.duration < duration:
            # Loop audio jika kependekan
            from moviepy.editor import concatenate_audioclips
            loops = int(duration / audio.duration) + 1
            audio = concatenate_audioclips([audio]*loops)
        audio = audio.subclip(0, duration)

        # 2. Video
        video_path = get_vertical_video(topic)
        if not video_path: return None
        
        clip = VideoFileClip(video_path)
        
        # Loop video visual
        if clip.duration < duration:
            loops = int(duration / clip.duration) + 1
            clip = concatenate_videoclips([clip]*loops)
        
        clip = clip.subclip(0, duration)
        
        # Resize/Crop center ke 1080x1920 (9:16)
        # Jika video sudah portrait, biasanya resize width ke 1080 cukup
        if clip.w / clip.h > 9/16: # Terlalu lebar
            clip = clip.resize(height=1920)
            clip = clip.crop(x1=clip.w/2 - 540, y1=0, width=1080, height=1920)
        else:
            clip = clip.resize(width=1080)
            # Crop height kalau terlalu tinggi (jarang terjadi)
        
        # 3. Text Overlay (Simple Title)
        # Gunakan text simple di tengah bawah
        txt = TextClip(topic, fontsize=60, color='white', font='Arial-Bold', stroke_color='black', stroke_width=2)
        txt = txt.set_pos(('center', 1400)).set_duration(duration)
        
        final = CompositeVideoClip([clip, txt]).set_audio(audio)
        
        final.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
        
        # Cleanup
        audio.close()
        clip.close()
        return output_file
        
    except Exception as e:
        print(f"Error render: {e}")
        return None
