import os
import requests
import random
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, ColorClip, TextClip, CompositeVideoClip, concatenate_audioclips, ImageClip, concatenate_videoclips
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

def get_nature_video(topic):
    """Fetch video alam/laut dari Pexels berdasarkan topic"""
    print(f"   Mencari video background untuk: {topic}...")
    
    if not PEXELS_API_KEY:
        print("   ⚠️ PEXELS_API_KEY tidak ditemukan, skip video fetch")
        return None
    
    headers = {"Authorization": PEXELS_API_KEY}
    
    # Map topic ke search query video
    topic_lower = topic.lower()
    
    if "lofi" in topic_lower or "study" in topic_lower or "focus" in topic_lower or "work" in topic_lower:
        search_queries = ["Rain window", "Forest ambient", "Peaceful nature", "Rainy day"]
        print("   -> Mode: LOFI / STUDY (Rain, Forest)")
    elif "meditation" in topic_lower or "sleep" in topic_lower or "zen" in topic_lower or "stress" in topic_lower:
        search_queries = ["Ocean waves", "Water flowing", "Meditation nature", "Sea waves", "Beach waves"]
        print("   -> Mode: MEDITATION (Water, Ocean)")
    else:
        search_queries = ["Rain forest", "Ocean nature", "Forest stream", "Waterfall", "Nature landscape"]
        print("   -> Mode: NATURE (Forest, Water)")
    
    # Try setiap search query
    for query in search_queries:
        try:
            print(f"   Mencari video: '{query}'...")
            url = f"https://api.pexels.com/videos/search?query={query}&per_page=5"
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            
            if data.get('videos'):
                videos = data['videos']
                print(f"      Ditemukan {len(videos)} video, memilih satu...")
                video_obj = random.choice(videos)
                video_files = video_obj.get('video_files', [])
                
                if not video_files:
                    print(f"      Video tidak punya file, coba query lain...")
                    continue
                
                # Prefer HD videos (720p atau lebih)
                hd_files = [v for v in video_files if v.get('width', 0) >= 720]
                video_file = hd_files[0] if hd_files else video_files[0]
                
                download_url = video_file['link']
                resolution = f"{video_file.get('width', '?')}x{video_file.get('height', '?')}"
                
                print(f"      Downloading video ({resolution})...")
                r = requests.get(download_url, timeout=30)
                if r.status_code == 200:
                    with open("background_video.mp4", 'wb') as f:
                        f.write(r.content)
                    print(f"      ✓ Video background berhasil didownload! ({len(r.content) / (1024*1024):.1f} MB)")
                    return "background_video.mp4"
                else:
                    print(f"      Download gagal (status {r.status_code}), coba query lain...")
                    continue
            else:
                print(f"      Tidak ada video, coba query lain...")
        except Exception as e:
            print(f"   ⚠️ Error: {e}, mencoba query lain...")
            continue
    
    print("   ❌ Tidak bisa fetch video alam dari Pexels, akan gunakan animated background")
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
    """Membuat video musik 10 menit (600 detik) dengan real nature video atau animated background"""
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
        
        # Try get nature video, fallback to animated background
        print("\n   === Tahap 1: Fetch Video Background ===")
        bg_video_path = get_nature_video(topic)
        
        if bg_video_path:
            print("\n   === Tahap 2: Load & Process Real Video ===")
            try:
                print(f"   Loading video dari: {bg_video_path}")
                background = VideoFileClip(bg_video_path)
                print(f"   ✓ Video loaded! Resolution: {background.size}, Duration: {background.duration:.1f}s")
                
                # Loop video jika lebih pendek dari durasi yang diinginkan
                if background.duration < actual_duration:
                    print(f"   Video background lebih pendek ({background.duration:.1f}s), melakukan looping...")
                    num_loops = int(actual_duration / background.duration) + 1
                    video_list = [background] * num_loops
                    background = concatenate_videoclips(video_list).subclip(0, actual_duration)
                    print(f"   ✓ Video setelah loop: {background.duration:.1f}s")
                else:
                    background = background.subclip(0, actual_duration)
                    print(f"   ✓ Video dipotong ke: {background.duration:.1f}s")
                
                # Resize ke 1920x1080 jika perlu
                if background.size != (1920, 1080):
                    print(f"   Resize video dari {background.size} ke 1920x1080...")
                    background = background.resize(height=1080)
                    print(f"   ✓ Resize done, size: {background.size}")
                
                # Tambahkan text overlay DI ATAS video
                print(f"   Menambahkan text overlay: {topic}")
                try:
                    title_text = TextClip(topic, fontsize=80, color='white', font='Arial-Bold')
                    title_text = title_text.set_position('center').set_duration(actual_duration)
                    final_clip = CompositeVideoClip([background, title_text])
                    print(f"   ✓ Composite video created")
                except Exception as te:
                    print(f"   ⚠️ Text error: {te}, using video without text")
                    final_clip = background
                
            except Exception as e:
                print(f"   ❌ Error loading video background: {e}")
                print("   Fallback ke animated background...")
                animated_bg = make_animated_background(actual_duration, topic, width=1920, height=1080, fps=12)
                try:
                    title_text = TextClip(topic, fontsize=80, color='white', font='Arial-Bold')
                    title_text = title_text.set_position('center').set_duration(actual_duration)
                    final_clip = CompositeVideoClip([animated_bg, title_text])
                except:
                    final_clip = animated_bg
        else:
            print("\n   === Tahap 2: Gunakan Animated Background ===")
            animated_bg = make_animated_background(actual_duration, topic, width=1920, height=1080, fps=12)
            print(f"   ✓ Animated background created")
            
            # Tambahkan text overlay
            try:
                title_text = TextClip(topic, fontsize=80, color='white', font='Arial-Bold')
                title_text = title_text.set_position('center').set_duration(actual_duration)
                final_clip = CompositeVideoClip([animated_bg, title_text])
                print(f"   ✓ Composite created with text")
            except:
                final_clip = animated_bg
        
        # Set audio
        final_clip = final_clip.set_audio(audio_clip.volumex(0.9))
        
        print("\n   === Tahap 3: Render Video Final ===")
        print(f"   Rendering musik video (10 menit, durasi sesungguhnya ~10-15 menit tergantung CPU)...")
        print(f"   Output: {output_file}")
        final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", 
                                   preset="ultrafast", fps=12, verbose=False, logger=None)
        
        print(f"\n   ✓ Video selesai! File: {output_file}")
        
        # Cleanup
        try:
            audio_clip.close()
            if os.path.exists(music_path):
                os.remove(music_path)
            if os.path.exists("background_video.mp4"):
                os.remove("background_video.mp4")
        except:
            pass
        
        return output_file
        
    except Exception as e:
        print(f"   ❌ Error membuat musik video: {e}")
        return None




