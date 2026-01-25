import os
import requests
import random
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, ColorClip, TextClip, CompositeVideoClip, concatenate_audioclips, ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import VideoClip
from PIL import Image, ImageDraw
import io

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def get_wikimedia_search_url(query):
    """Mencari URL Audio via Fitur Pencarian Wikimedia"""
    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": query, "gsrnamespace": 6, "gsrlimit": 3,
        "prop": "imageinfo", "iiprop": "url"
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}

    try:
        response = requests.get(api_url, params=params, headers=headers)
        data = response.json()
        if "query" in data and "pages" in data["query"]:
            pages = list(data["query"]["pages"].values())
            if pages:
                return random.choice(pages)["imageinfo"][0]["url"]
    except Exception as e:
        print(f"   Gagal mencari API untuk {query}: {e}")
    return None

def get_relaxing_music(topic):
    print(f"   Mencari musik relaxing/focusing untuk: {topic}...")
    
    # --- LOGIKA PEMILIHAN MUSIK RELAXING ---
    topic_lower = topic.lower()
    
    if "lofi" in topic_lower or "study" in topic_lower or "focus" in topic_lower or "work" in topic_lower:
        keywords = ["Lofi music ogg", "Chill beats ogg", "Study music ogg", "Hip hop beats ogg"]
        print("   -> Mode: LOFI / STUDY")
        
    elif "meditation" in topic_lower or "sleep" in topic_lower or "zen" in topic_lower or "stress" in topic_lower:
        keywords = ["Meditation music ogg", "Relaxing ambient ogg", "Calm music ogg", "Piano relaxing ogg"]
        print("   -> Mode: MEDITATION / RELAXATION")
        
    else: # Default (Nature Sounds)
        keywords = ["Rain sounds ogg", "Ocean waves ogg", "Nature ambient ogg", "Forest sounds ogg"]
        print("   -> Mode: NATURE SOUNDS")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
    
    # Coba cari lagu
    for keyword in random.sample(keywords, len(keywords)):
        print(f"   Mencari: '{keyword}'")
        music_url = get_wikimedia_search_url(keyword)
        if music_url:
            try:
                r = requests.get(music_url, headers=headers, stream=True, timeout=10)
                if r.status_code == 200:
                    with open("bg_music.ogg", 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024): f.write(chunk)
                    if os.path.getsize("bg_music.ogg") > 100000: return "bg_music.ogg"
            except:
                continue
    return None

def make_animated_background(duration, topic, width=1920, height=1080, fps=12):
    """Buat animated background visual untuk musik (optimized untuk speed)"""
    topic_lower = topic.lower()
    
    # Tentukan color palette berdasarkan genre
    if "lofi" in topic_lower or "study" in topic_lower:
        base_color = np.array([26, 26, 46], dtype=np.uint8)  # Dark blue
        accent_colors = [np.array([70, 130, 180], dtype=np.uint8), np.array([100, 149, 237], dtype=np.uint8)]
    elif "meditation" in topic_lower or "sleep" in topic_lower:
        base_color = np.array([20, 40, 50], dtype=np.uint8)  # Dark teal
        accent_colors = [np.array([70, 130, 150], dtype=np.uint8), np.array([100, 150, 180], dtype=np.uint8)]
    else:  # Nature sounds
        base_color = np.array([15, 35, 60], dtype=np.uint8)  # Deep blue
        accent_colors = [np.array([60, 120, 140], dtype=np.uint8), np.array([80, 150, 170], dtype=np.uint8)]
    
    def make_frame(t):
        """Generate frame dengan animasi (simplified & optimized)"""
        frame = np.ones((height, width, 3), dtype=np.uint8) * base_color
        
        # Simplified gradient background (reduced loops)
        for y in range(0, height, 5):  # Step 5 untuk faster processing
            ratio = y / height
            color = (base_color.astype(float) + 
                    (accent_colors[0].astype(float) - base_color.astype(float)) * ratio * 0.3)
            color_int = np.clip(color, 0, 255).astype(np.uint8)
            frame[y:y+5, :] = color_int
        
        # Simplified orbs - fewer dan lebih kecil
        num_orbs = 2  # Reduce dari 4 ke 2
        for i in range(num_orbs):
            phase = (t * 0.3 + i * np.pi / num_orbs)
            x = int(width / 2 + 250 * np.cos(phase))
            y = int(height / 2 + 150 * np.sin(phase * 0.7))
            
            # Clamp position
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            
            # Simpler radius dan opacity
            radius = int(60 + 30 * np.sin(t * 0.5 + i))
            radius = max(5, min(radius, 150))
            
            color = accent_colors[i % len(accent_colors)]
            
            # Draw circle lebih efisien dengan step
            for dx in range(-radius, radius+1, 2):  # Step 2 untuk faster
                for dy in range(-radius, radius+1, 2):
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        dist_val = np.sqrt(dx**2 + dy**2)
                        if dist_val < radius:
                            fade = max(0, 1 - dist_val / radius)
                            frame[ny, nx] = (
                                frame[ny, nx].astype(float) * (1 - fade * 0.5) +
                                color.astype(float) * fade * 0.5
                            ).astype(np.uint8)
        
        # Simplified wave effect - reduce frequency
        if int(t) % 2 == 0:  # Only update every 2 seconds
            wave_speed = t * 1.5
            for x in range(0, width, 150):  # Wider spacing
                y_offset = int(80 * np.sin((x / width) * np.pi * 2 + wave_speed))
                y = int(height / 2 + y_offset)
                
                if 0 <= y < height:
                    cv = accent_colors[0]
                    for dy in range(-1, 2):  # Thinner line
                        ny = y + dy
                        if 0 <= ny < height:
                            frame[ny, x] = (
                                frame[ny, x].astype(float) * 0.7 +
                                cv.astype(float) * 0.3
                            ).astype(np.uint8)
        
        return frame
    
    return VideoClip(make_frame, duration=duration)

def create_music_video(music_path, topic, duration=600):
    """Membuat video musik 10 menit (600 detik) dengan background visual minimal"""
    output_file = "final_music_video.mp4"
    
    try:
        # Load musik
        audio_clip = AudioFileClip(music_path)
        actual_duration = duration  # Always 600 detik (10 menit)
        
        print(f"   Target durasi video: {actual_duration//60:.1f} menit")
        print(f"   Durasi musik asli: {audio_clip.duration//60:.1f} menit")
        
        # Jika musik lebih pendek dari 10 menit, loop-kan
        if audio_clip.duration < actual_duration:
            print(f"   Musik lebih pendek, melakukan looping...")
            loops = int(actual_duration / audio_clip.duration) + 1
            audio_list = [audio_clip] * loops
            audio_clip = concatenate_audioclips(audio_list).subclip(0, actual_duration)
        else:
            print(f"   Musik cukup panjang, memotong ke 10 menit...")
            audio_clip = audio_clip.subclip(0, actual_duration)
        
        # Buat animated background
        print("   Membuat animated background (optimized)...")
        animated_bg = make_animated_background(actual_duration, topic, width=1920, height=1080, fps=12)
        
        # Tambahkan text judul di tengah dengan semi-transparent background
        try:
            title_text = TextClip(topic, fontsize=80, color='white', font='Arial-Bold')
            title_text = title_text.set_position('center').set_duration(actual_duration)
            final_clip = CompositeVideoClip([animated_bg, title_text])
        except:
            final_clip = animated_bg
        
        # Set audio
        final_clip = final_clip.set_audio(audio_clip.volumex(0.9))
        
        print("   Rendering musik video (10 menit, ini akan memakan waktu beberapa menit)...")
        final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", 
                                   preset="ultrafast", fps=12, verbose=False, logger=None)
        
        # Cleanup
        try:
            audio_clip.close()
            if os.path.exists(music_path):
                os.remove(music_path)
        except:
            pass
        
        return output_file
        
    except Exception as e:
        print(f"   ❌ Error membuat musik video: {e}")
        return None




