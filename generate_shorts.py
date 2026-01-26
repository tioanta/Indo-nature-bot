import os
import requests
import random
import time
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips
import json

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def get_music(topic):
    """Cari musik dengan User-Agent agar tidak diblokir"""
    print(f"   [Shorts] Mencari BGM untuk: {topic}")
    topic_lower = topic.lower()
    
    # Keyword mapping
    if "manchester" in topic_lower or "football" in topic_lower:
        keywords = ["Epic sport cinematic ogg", "Stadium atmosphere ogg", "Energetic rock ogg"]
    elif "masjid" in topic_lower or "makkah" in topic_lower:
        keywords = ["Islamic call to prayer ambient ogg", "Middle eastern ney ogg", "Desert wind ogg"]
    elif "japan" in topic_lower or "tokyo" in topic_lower:
        keywords = ["Lofi japan ogg", "City rain ambient ogg", "Japanese koto ogg"]
    else:
        keywords = ["Cinematic ambient ogg"]

    api_url = "https://commons.wikimedia.org/w/api.php"
    # User-Agent SANGAT PENTING agar download tidak 0 bytes
    headers = {'User-Agent': 'IndoNatureBot/2.1 (contact@example.com)'}
    
    for kw in keywords:
        params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": kw, "gsrnamespace": 6, "prop": "imageinfo", "iiprop": "url"}
        try:
            r = requests.get(api_url, params=params, headers=headers, timeout=10)
            data = r.json()
            
            if "query" in data and "pages" in data["query"]:
                pages = list(data["query"]["pages"].values())
                if pages:
                    url = pages[0]["imageinfo"][0]["url"]
                    print(f"      Downloading audio: {url[:60]}...")
                    
                    # Download dengan retry sederhana
                    try:
                        r_audio = requests.get(url, stream=True, headers=headers, timeout=20)
                        temp_filename = "bg_shorts.ogg"
                        
                        with open(temp_filename, 'wb') as f:
                            for chunk in r_audio.iter_content(chunk_size=1024): 
                                f.write(chunk)
                        
                        # VALIDASI UKURAN FILE (Minimal 10KB)
                        if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 10000:
                            print(f"      ✓ Audio Valid ({os.path.getsize(temp_filename)//1024} KB)")
                            return temp_filename
                        else:
                            print("      ❌ File audio corrupt/kosong, coba keyword lain...")
                    except Exception as dl_err:
                        print(f"      ❌ Gagal download file: {dl_err}")
                        
        except Exception as e:
            print(f"      ⚠️ Error search: {e}")
            
    print("   ❌ Gagal mendapatkan audio yang valid.")
    return None

def get_vertical_video(topic):
    print(f"   [Shorts] Mencari Video Vertical: {topic}")
    headers = {"Authorization": PEXELS_API_KEY}
    
    # Query mapping
    topic_lower = topic.lower()
    if "manchester" in topic_lower: query = "football fans stadium"
    elif "masjid" in topic_lower: query = "islamic architecture"
    elif "japan" in topic_lower: query = "tokyo street night rain"
    else: query = topic

    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=8"
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        if data.get('videos'):
            # Filter video yang benar-benar vertical (width < height)
            vertical_vids = [v for v in data['videos'] if v['width'] < v['height']]
            if not vertical_vids: vertical_vids = data['videos']
            
            video = random.choice(vertical_vids)
            hd_files = [f for f in video['video_files'] if f['height'] >= 1080 and f['width'] < f['height']]
            target = hd_files[0] if hd_files else video['video_files'][0]
            
            print(f"      Downloading video ({target['width']}x{target['height']})...")
            r_vid = requests.get(target['link'], timeout=40)
            
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
        # 1. AUDIO
        try:
            audio = AudioFileClip(music_path)
            if audio.duration < duration:
                loops = int(duration / audio.duration) + 1
                audio = concatenate_audioclips([audio]*loops)
            audio = audio.subclip(0, duration)
        except Exception as e:
            print(f"   ❌ Audio Error: {e}")
            return None

        # 2. VIDEO
        video_path = get_vertical_video(topic)
        if not video_path: return None
        
        clip = VideoFileClip(video_path)
        if clip.duration < duration:
            loops = int(duration / clip.duration) + 1
            clip = concatenate_videoclips([clip]*loops)
        clip = clip.subclip(0, duration)
        
        # 3. RESIZE & CROP (9:16)
        if clip.w / clip.h > 9/16:
            clip = clip.resize(height=1920)
            clip = clip.crop(x1=clip.w/2 - 540, y1=0, width=1080, height=1920)
        else:
            clip = clip.resize(width=1080)

        # 4. TEXT
        try:
            # Gunakan 'method="caption"' untuk auto-wrap text panjang
            txt = TextClip(topic, fontsize=55, color='white', font='Arial-Bold', 
                          stroke_color='black', stroke_width=3, method='caption', 
                          size=(900, None), align='center')
            txt = txt.set_position(('center', 1300)).set_duration(duration)
            final = CompositeVideoClip([clip, txt])
        except:
            print("   ⚠️ Text gagal, lanjut tanpa text")
            final = clip
        
        final = final.set_audio(audio)
        
        print("   Rendering Shorts...")
        final.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac", 
                              preset="ultrafast", verbose=False, logger=None)
        
        return output_file
        
    except Exception as e:
        print(f"   ❌ RENDER FAILED: {e}")
        return None
    finally:
        # Bersih-bersih file temp
        try:
            if audio: audio.close()
            if clip: clip.close()
            if os.path.exists("raw_shorts.mp4"): os.remove("raw_shorts.mp4")
            if os.path.exists("bg_shorts.ogg"): os.remove("bg_shorts.ogg")
        except: pass
