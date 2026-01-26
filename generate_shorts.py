import os
import requests
import random
import numpy as np
from PIL import Image

# === FIX 1: PATCH PILLOW SEBELUM IMPORT MOVIEPY ===
# Patch ini WAJIB diletakkan sebelum 'import moviepy'
if not hasattr(Image, 'ANTIALIAS'):
    try:
        from PIL.Image import Resampling
        Image.ANTIALIAS = Resampling.LANCZOS
    except ImportError:
        Image.ANTIALIAS = Image.LANCZOS
# ==================================================

# Baru import moviepy setelah di-patch
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips
import json

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def get_music(topic):
    """Cari musik singkat yang sesuai vibe dengan Error Handling ketat"""
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
    # User-Agent unik agar tidak diblokir Wikimedia
    headers = {'User-Agent': 'IndoNatureBot/2.0 (github.com/tioanta; contact@example.com)'}
    
    for kw in keywords:
        params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": kw, "gsrnamespace": 6, "prop": "imageinfo", "iiprop": "url"}
        try:
            r = requests.get(api_url, params=params, headers=headers, timeout=10)
            data = r.json()
            
            if "query" in data and "pages" in data["query"]:
                pages = list(data["query"]["pages"].values())
                if pages:
                    # Ambil URL audio
                    url = pages[0]["imageinfo"][0]["url"]
                    print(f"      Downloading audio dari: {url[:50]}...")
                    
                    # Download dengan Stream
                    r_audio = requests.get(url, stream=True, headers=headers, timeout=20)
                    
                    if r_audio.status_code == 200:
                        temp_filename = "bg_shorts.ogg"
                        with open(temp_filename, 'wb') as f:
                            for chunk in r_audio.iter_content(chunk_size=1024): 
                                f.write(chunk)
                        
                        # === FIX 2: VALIDASI FILE AUDIO ===
                        # Cek apakah file berhasil terdownload dan ukurannya masuk akal (> 10KB)
                        if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 10000:
                            print(f"      Audio OK ({os.path.getsize(temp_filename) // 1024} KB)")
                            return temp_filename
                        else:
                            print("      ❌ File audio kosong atau corrupt, mencari keyword lain...")
                    else:
                        print(f"      ❌ Gagal download (Status: {r_audio.status_code})")
        except Exception as e:
            print(f"      ⚠️ Error saat search audio '{kw}': {e}")
            continue
            
    print("   ❌ Tidak menemukan audio yang valid.")
    return None

def get_vertical_video(topic):
    """Cari video Pexels dengan orientasi PORTRAIT"""
    print(f"   [Shorts] Mencari Video Vertical: {topic}")
    
    if not PEXELS_API_KEY:
        print("   ⚠️ PEXELS_API_KEY Missing!")
        return None
        
    headers = {"Authorization": PEXELS_API_KEY}
    
    topic_lower = topic.lower()
    if "manchester" in topic_lower:
        query = "football stadium"
    elif "masjid" in topic_lower:
        query = "mosque architecture"
    elif "japan" in topic_lower:
        query = "Tokyo street night"
    else:
        query = topic

    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=5"
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        if data.get('videos'):
            video = random.choice(data['videos'])
            files = video['video_files']
            # Prioritaskan Vertical & HD
            vertical_files = [v for v in files if v['width'] < v['height'] and v['width'] >= 720]
            target_file = vertical_files[0] if vertical_files else files[0]
            
            download_url = target_file['link']
            print(f"      Downloading video: {download_url[:50]}...")
            
            r_vid = requests.get(download_url, timeout=30)
            if r_vid.status_code == 200:
                with open("raw_shorts.mp4", 'wb') as f:
                    f.write(r_vid.content)
                return "raw_shorts.mp4"
    except Exception as e:
        print(f"Error Pexels: {e}")
    return None

def create_short_video(music_path, topic, duration=58):
    output_file = "final_shorts.mp4"
    audio = None
    clip = None
    
    try:
        # 1. AUDIO PROCESSING (Safe Mode)
        try:
            audio = AudioFileClip(music_path)
            # Cek durasi audio valid
            if audio.duration < 1:
                raise Exception("Durasi audio terlalu pendek/corrupt")
                
            if audio.duration < duration:
                loops = int(duration / audio.duration) + 1
                audio = concatenate_audioclips([audio]*loops)
            audio = audio.subclip(0, duration)
        except Exception as e:
            print(f"   ❌ Gagal memproses file audio: {e}")
            # Jika audio gagal, script akan berhenti di sini daripada crash total
            return None

        # 2. VIDEO PROCESSING
        video_path = get_vertical_video(topic)
        if not video_path: 
            print("   ❌ Video background tidak ditemukan.")
            if audio: audio.close()
            return None
        
        clip = VideoFileClip(video_path)
        
        if clip.duration < duration:
            loops = int(duration / clip.duration) + 1
            clip = concatenate_videoclips([clip]*loops)
        
        clip = clip.subclip(0, duration)
        
        # Smart Crop 9:16
        if clip.w / clip.h > 9/16: 
            clip = clip.resize(height=1920)
            clip = clip.crop(x1=clip.w/2 - 540, y1=0, width=1080, height=1920)
        else:
            clip = clip.resize(width=1080)
            
        # 3. TEXT OVERLAY
        try:
            # Menggunakan TextClip standard
            txt = TextClip(topic, fontsize=50, color='white', font='Arial-Bold', 
                          stroke_color='black', stroke_width=2, method='caption', size=(900, None))
            txt = txt.set_position(('center', 1400)).set_duration(duration)
            final = CompositeVideoClip([clip, txt])
        except Exception as e:
            print(f"   ⚠️ Text error (Skip text): {e}")
            final = clip
        
        final = final.set_audio(audio)
        
        print("   Rendering final video (Shorts)...")
        final.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac", 
                              preset="ultrafast", verbose=False, logger=None)
        
        return output_file
        
    except Exception as e:
        print(f"   ❌ CRITICAL ERROR Render: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Cleanup resource agar memory tidak bocor
        try:
            if audio: audio.close()
            if clip: clip.close()
            if os.path.exists("raw_shorts.mp4"): os.remove("raw_shorts.mp4")
            if os.path.exists("bg_shorts.ogg"): os.remove("bg_shorts.ogg")
        except:
            pass
