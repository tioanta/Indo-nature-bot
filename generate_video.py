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

def make_animated_background(duration, topic, width=1920, height=1080, fps=24):
    """Buat animated background visual untuk musik"""
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
        """Generate frame dengan animasi"""
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Base gradient background
        for y in range(height):
            ratio = y / height
            color = (base_color.astype(float) + 
                    (accent_colors[0].astype(float) - base_color.astype(float)) * ratio * 0.3)
            frame[y, :] = np.clip(color, 0, 255).astype(np.uint8)
        
        # Animated orbs/circles yang bergerak
        num_orbs = 4
        for i in range(num_orbs):
            # Hitung posisi orb berdasarkan waktu
            phase = (t * 0.3 + i * np.pi / num_orbs)
            x = int(width / 2 + 300 * np.cos(phase))
            y = int(height / 2 + 200 * np.sin(phase * 0.7))
            
            # Clamp position ke dalam bounds
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            
            # Radius dan opacity berubah-ubah
            radius = int(80 + 40 * np.sin(t * 0.5 + i))
            radius = max(1, min(radius, 300))  # Clamp radius
            alpha = int(100 + 100 * np.sin(t * 0.4 + i * 2))
            alpha = max(1, min(alpha, 200))
            
            # Draw circle dengan gradient - safer approach
            color = accent_colors[i % len(accent_colors)]
            
            # Create mesh grid untuk circle
            yy, xx = np.ogrid[-radius:radius+1, -radius:radius+1]
            dist = np.sqrt(xx**2 + yy**2)
            
            # Hanya draw bagian yang dalam bounds
            for dy in range(-radius, radius+1):
                ny = y + dy
                if 0 <= ny < height:
                    for dx in range(-radius, radius+1):
                        nx = x + dx
                        if 0 <= nx < width:
                            dist_val = np.sqrt(dx**2 + dy**2)
                            if dist_val < radius:
                                fade = max(0, 1 - dist_val / radius)
                                intensity = int(alpha * fade * 0.01)
                                intensity = max(0, min(intensity, 255))
                                frame[ny, nx] = (
                                    frame[ny, nx].astype(float) * (255 - intensity) / 255 +
                                    color.astype(float) * intensity / 255
                                ).astype(np.uint8)
        
        # Animated lines/waves effect
        wave_speed = t * 2
        for x in range(0, width, 100):
            y_offset = int(100 * np.sin((x / width) * np.pi * 2 + wave_speed))
            y = int(height / 2 + y_offset)
            
            if 0 <= y < height:
                cv = accent_colors[0]
                for dy in range(-2, 3):
                    ny = y + dy
                    if 0 <= ny < height:
                        frame[ny, x] = (
                            frame[ny, x].astype(float) * 0.6 +
                            cv.astype(float) * 0.4
                        ).astype(np.uint8)
        
        return frame
    
    return VideoClip(make_frame, duration=duration)

def create_music_video(music_path, topic, duration=1200):
    """Membuat video musik 20 menit (1200 detik) dengan background visual minimal"""
    output_file = "final_music_video.mp4"
    
    try:
        # Load musik
        audio_clip = AudioFileClip(music_path)
        actual_duration = duration  # Always 1200 detik (20 menit)
        
        print(f"   Target durasi video: {actual_duration//60:.1f} menit")
        print(f"   Durasi musik asli: {audio_clip.duration//60:.1f} menit")
        
        # Jika musik lebih pendek dari 20 menit, loop-kan
        if audio_clip.duration < actual_duration:
            print(f"   Musik lebih pendek, melakukan looping...")
            loops = int(actual_duration / audio_clip.duration) + 1
            audio_list = [audio_clip] * loops
            audio_clip = concatenate_audioclips(audio_list).subclip(0, actual_duration)
        else:
            print(f"   Musik cukup panjang, memotong ke 20 menit...")
            audio_clip = audio_clip.subclip(0, actual_duration)
        
        # Buat animated background
        print("   Membuat animated background...")
        animated_bg = make_animated_background(actual_duration, topic, width=1920, height=1080, fps=24)
        
        # Tambahkan text judul di tengah dengan semi-transparent background
        try:
            title_text = TextClip(topic, fontsize=80, color='white', font='Arial-Bold')
            title_text = title_text.set_position('center').set_duration(actual_duration)
            final_clip = CompositeVideoClip([animated_bg, title_text])
        except:
            final_clip = animated_bg
        
        # Set audio
        final_clip = final_clip.set_audio(audio_clip.volumex(0.9))
        
        print("   Rendering musik video (20 menit)...")
        final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", 
                                   preset="ultrafast", fps=24, verbose=False, logger=None)
        
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




