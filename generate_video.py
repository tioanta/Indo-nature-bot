import os
import requests
import random
from moviepy.editor import VideoFileClip, AudioFileClip, ColorClip, TextClip, CompositeVideoClip, concatenate_audioclips
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
        
        # Buat warna background menggunakan topic
        topic_lower = topic.lower()
        if "lofi" in topic_lower or "study" in topic_lower:
            bg_color = (26, 26, 46)  # Dark blue
        elif "meditation" in topic_lower or "sleep" in topic_lower:
            bg_color = (20, 40, 50)  # Dark teal
        else:
            bg_color = (15, 35, 60)  # Deep blue
        
        # Buat background video (warna solid dengan subtitle)
        background = ColorClip(size=(1920, 1080), color=bg_color).set_duration(actual_duration)
        
        # Tambahkan text judul di tengah
        try:
            title_text = TextClip(topic, fontsize=80, color='white', font='Arial')
            title_text = title_text.set_position('center').set_duration(actual_duration)
            final_clip = CompositeVideoClip([background, title_text])
        except:
            final_clip = background
        
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




