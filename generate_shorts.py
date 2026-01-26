import os
import requests
import random
import numpy as np
from PIL import Image # <--- Tambahan import
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import json

# === FIX BUG PILLOW 10+ (AttributeError: 'module' object has no attribute 'ANTIALIAS') ===
if not hasattr(Image, 'ANTIALIAS'):
    try:
        from PIL.Image import Resampling
        Image.ANTIALIAS = Resampling.LANCZOS
    except ImportError:
        Image.ANTIALIAS = Image.LANCZOS
# =========================================================================================

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

    api_url = "https://commons.wikimedia.org/w/api.php"
    headers = {'User-Agent': 'BotShorts/1.0'}
    
    # Coba satu per satu keyword sampai dapat
    for kw in keywords:
        params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": kw, "gsrnamespace": 6, "prop": "imageinfo", "iiprop": "url"}
        try:
            r = requests.get(api_url, params=params, headers=headers).json()
            if "query" in r and "pages" in r["query"]:
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
    
    # Keyword mapping agar hasil pencarian lebih relevan
    topic_lower = topic.lower()
    if "manchester" in topic_lower:
        query = "football stadium"
    elif "masjid" in topic_lower:
        query = "mosque architecture"
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
            # Pilih random dari 5 hasil teratas
            video = random.choice(data['videos'])
            
            files = video['video_files']
            # Prioritaskan file yang aspect ratio-nya vertical (width < height) dan HD
            vertical_files = [v for v in files if v['width'] < v['height'] and v['width'] >= 720]
            
            # Fallback: ambil file apa saja jika tidak ada yang strict vertical
            target_file = vertical_files[0] if vertical_files else files[0]
            
            download_url = target_file['link']
            print(f"      Downloading video: {download_url[:50]}...")
            with open("raw_shorts.mp4", 'wb') as f:
                f.write(requests.get(download_url).content)
            return "raw_shorts.mp4"
    except Exception as e:
        print(f"Error Pexels: {e}")
    return None

def create_short_video(music_path, topic, duration=58):
    output_file = "final_shorts.mp4"
    try:
        # 1. Audio Processing
        audio = AudioFileClip(music_path)
        # Jika audio kependekan, di-loop
        if audio.duration < duration:
            from moviepy.editor import concatenate_audioclips
            loops = int(duration / audio.duration) + 1
            audio = concatenate_audioclips([audio]*loops)
        audio = audio.subclip(0, duration)

        # 2. Video Processing
        video_path = get_vertical_video(topic)
        if not video_path: 
            print("Video tidak ditemukan.")
            return None
        
        clip = VideoFileClip(video_path)
        
        # Loop video visual jika kependekan
        if clip.duration < duration:
            loops = int(duration / clip.duration) + 1
            clip = concatenate_videoclips([clip]*loops)
        
        clip = clip.subclip(0, duration)
        
        # Resize/Crop center ke 1080x1920 (9:16)
        # Logika: Pastikan tingginya 1920, lalu crop lebarnya, ATAU pastikan lebarnya 1080, crop tingginya.
        if clip.w / clip.h > 9/16: 
            # Video terlalu lebar (landscape/square) -> Resize tinggi dulu ke 1920
            clip = clip.resize(height=1920)
            # Crop bagian tengah agar jadi 1080
            clip = clip.crop(x1=clip.w/2 - 540, y1=0, width=1080, height=1920)
        else:
            # Video sudah cukup kurus -> Resize lebar ke 1080
            clip = clip.resize(width=1080)
            # Crop tinggi jika perlu (biasanya tidak perlu kalau sudah portrait)
            
        # 3. Text Overlay (Simple Title)
        # Menggunakan TextClip
        try:
            # Stroke hitam agar tulisan putih terbaca di background terang
            txt = TextClip(topic, fontsize=50, color='white', font='Arial-Bold', stroke_color='black', stroke_width=2, method='caption', size=(900, None))
            txt = txt.set_position(('center', 1400)).set_duration(duration)
            final = CompositeVideoClip([clip, txt])
        except Exception as e:
            print(f"Text error (skip text): {e}")
            final = clip
        
        final = final.set_audio(audio)
        
        print("   Rendering final video...")
        # Preset ultrafast agar hemat waktu GitHub Actions
        final.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", verbose=False, logger=None)
        
        # Cleanup
        audio.close()
        clip.close()
        return output_file
        
    except Exception as e:
        print(f"Error render details: {e}")
        import traceback
        traceback.print_exc() # Print full error log untuk debug
        return None
