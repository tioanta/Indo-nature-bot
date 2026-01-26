import os
import requests
import random
import asyncio
import edge_tts
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips, concatenate_audioclips

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- 1. FITUR VOICE OVER & SCRIPTING ---
async def generate_voice_over(topic, output_file="voice_over.mp3"):
    """
    1. Minta Gemini buat naskah pendek (50 kata).
    2. Convert naskah ke suara pakai Edge-TTS.
    """
    print(f"   🎙️ [VO] Membuat Naskah untuk: {topic}")
    
    # A. Generate Naskah via Gemini dengan Auto-detect Model
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Auto-detect available model (priority: flash > pro > first available)
    chosen_model = None
    try:
        all_models = list(genai.list_models())
        valid_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        # Try priority: gemini-2.0-flash > gemini-1.5-flash > gemini-pro > gemini-1.0-pro
        for priority_model in ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']:
            for m in valid_models:
                if priority_model in m:
                    chosen_model = m
                    break
            if chosen_model:
                break
        
        if not chosen_model and valid_models:
            chosen_model = valid_models[0]
        
        if not chosen_model:
            print("      ⚠️ Tidak ada model Gemini tersedia, gunakan script default")
            chosen_model = None
    except Exception as e:
        print(f"      ⚠️ Error detect Gemini model: {e}")
        chosen_model = None
    
    model = genai.GenerativeModel(chosen_model) if chosen_model else None
    
    prompt = f"""
    Buatkan naskah Voice Over pendek (maksimal 40 detik/60 kata) untuk video YouTube Shorts tentang: "{topic}".
    Gaya bahasa: Santai, engaging, seperti storyteller, Bahasa Indonesia gaul/akrab.
    Langsung tulis naskahnya saja tanpa tanda kutip.
    """
    
    script = None
    if model:
        try:
            response = model.generate_content(prompt)
            script = response.text.strip()
            print(f"      📜 Naskah: {script[:50]}...")
        except Exception as e:
            print(f"      ⚠️ Gagal generate naskah: {e}")
            script = None
    
    if not script:
        # Fallback script
        script = f"Ini adalah video indah tentang {topic}. Nikmati pemandangannya."
        print(f"      📜 Naskah (fallback): {script[:50]}...")

    # B. Convert Text to Speech (Bahasa Indonesia)
    # Voice Options: id-ID-GadisNeural, id-ID-ArdiNeural
    voice = "id-ID-ArdiNeural" 
    communicate = edge_tts.Communicate(script, voice)
    
    await communicate.save(output_file)
    print("      ✅ Voice Over Audio siap.")
    return output_file

def get_voice_over_sync(topic):
    """Wrapper agar fungsi async bisa dipanggil di kode sync"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        path = loop.run_until_complete(generate_voice_over(topic))
        return path
    except Exception as e:
        print(f"      ❌ Error VO: {e}")
        return None

# --- 2. PENCARIAN MUSIK (FIXED) ---
def get_music(topic):
    print(f"   🎵 [Music] Mencari BGM untuk: {topic}")
    topic_lower = topic.lower()
    
    if "manchester" in topic_lower or "football" in topic_lower:
        keywords = ["Sport rock energy ogg", "Stomps and claps ogg", "Stadium drums ogg"]
    elif "masjid" in topic_lower or "makkah" in topic_lower:
        keywords = ["Islamic ambient ogg", "Middle east ney flute ogg"]
    elif "japan" in topic_lower:
        keywords = ["Lofi hip hop ogg", "Japan ambient ogg"]
    else:
        keywords = ["Cinematic ambient ogg"]

    # Header browser asli agar tidak diblokir Wikimedia
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    for kw in keywords:
        try:
            # 1. Cari URL file page
            search_url = "https://commons.wikimedia.org/w/api.php"
            params = {
                "action": "query", "format": "json", "generator": "search",
                "gsrsearch": kw, "gsrnamespace": 6, "gsrlimit": 3,
                "prop": "imageinfo", "iiprop": "url"
            }
            r = requests.get(search_url, params=params, headers=headers, timeout=10)
            data = r.json()
            
            pages = list(data.get("query", {}).get("pages", {}).values())
            if not pages: continue

            # 2. Ambil URL audio sebenarnya
            file_url = pages[0]["imageinfo"][0]["url"]
            
            # 3. Download dengan Stream & Validasi
            print(f"      ⬇️ Downloading: {kw}...")
            r_audio = requests.get(file_url, headers=headers, stream=True, timeout=20)
            
            temp_filename = "bg_music.ogg"
            with open(temp_filename, 'wb') as f:
                for chunk in r_audio.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Cek size (minimal 50KB agar bukan file error)
            if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 50000:
                # Validasi bahwa file bisa di-load oleh MoviePy
                try:
                    test_clip = AudioFileClip(temp_filename)
                    test_duration = test_clip.duration
                    test_clip.close()
                    print(f"      ✅ Audio OK ({os.path.getsize(temp_filename)//1024} KB, duration: {test_duration:.1f}s)")
                    return temp_filename
                except Exception as audio_err:
                    print(f"      ⚠️ Audio tidak bisa di-load MoviePy: {audio_err}")
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
                    continue
            else:
                print("      ❌ File terlalu kecil/corrupt.")
                
        except Exception as e:
            print(f"      ⚠️ Error music search: {e}")
            continue
            
    return None

# --- 3. PENCARIAN VIDEO ---
def get_vertical_video(topic):
    print(f"   🎬 [Video] Mencari Footage: {topic}")
    headers = {"Authorization": PEXELS_API_KEY}
    
    topic_lower = topic.lower()
    if "manchester" in topic_lower: query = "football fans stadium red"
    elif "masjid" in topic_lower: query = "mosque architecture"
    elif "japan" in topic_lower: query = "Tokyo street night rain"
    else: query = topic

    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=5"
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        if data.get('videos'):
            # Pilih video HD Vertical
            valid_vids = [v for v in data['videos'] if v['width'] < v['height'] and v['width'] >= 720]
            if not valid_vids: valid_vids = data['videos']
            
            target_vid = random.choice(valid_vids)
            video_file = target_vid['video_files'][0]
            
            # Cari link download kualitas terbaik
            for f in target_vid['video_files']:
                if f['width'] >= 720 and f['width'] < f['height']:
                    video_file = f
                    break
            
            link = video_file['link']
            print(f"      ⬇️ Downloading Video ID: {target_vid['id']}...")
            
            with open("raw_video.mp4", 'wb') as f:
                f.write(requests.get(link).content)
            return "raw_video.mp4"
    except Exception as e:
        print(f"Error Pexels: {e}")
    return None

# --- 4. RENDER UTAMA ---
def create_short_video(topic, use_vo=True, duration=58):
    output_file = "final_shorts.mp4"
    
    try:
        # A. Siapkan Video
        video_path = get_vertical_video(topic)
        if not video_path: return None
        clip = VideoFileClip(video_path)
        
        # Loop video jika kurang dari durasi
        if clip.duration < duration:
            loops = int(duration / clip.duration) + 1
            clip = concatenate_videoclips([clip]*loops)
        
        # Crop/Resize ke 9:16 (1080x1920)
        if clip.w / clip.h > 9/16:
            clip = clip.resize(height=1920)
            clip = clip.crop(x1=clip.w/2 - 540, y1=0, width=1080, height=1920)
        else:
            clip = clip.resize(width=1080)
        
        clip = clip.subclip(0, duration)

        # B. Audio Processing (VO + Music)
        audio_tracks = []
        
        # 1. Voice Over
        if use_vo:
            vo_path = get_voice_over_sync(topic)
            if vo_path:
                vo_clip = AudioFileClip(vo_path)
                # Jika VO lebih panjang dari video, potong VO (jarang terjadi karena limit 60 kata)
                # Jika VO lebih pendek, biarkan.
                audio_tracks.append(vo_clip.set_start(1)) # Mulai detik ke-1
        
        # 2. Background Music
        music_path = get_music(topic)
        if music_path:
            bg_music = AudioFileClip(music_path)
            # Loop music
            if bg_music.duration < duration:
                loops = int(duration / bg_music.duration) + 1
                bg_music = concatenate_audioclips([bg_music]*loops)
            bg_music = bg_music.subclip(0, duration)
            
            # **DUCKING**: Jika ada VO, kecilkan volume musik
            if use_vo and len(audio_tracks) > 0:
                bg_music = bg_music.volumex(0.15) # Volume 15% kalau ada VO
            else:
                bg_music = bg_music.volumex(0.8) # Volume 80% kalau instrumental
                
            audio_tracks.append(bg_music)
        
        # Gabungkan Audio
        if audio_tracks:
            final_audio = CompositeAudioClip(audio_tracks)
            clip = clip.set_audio(final_audio)

        # C. Text Title (Opsional, Simple)
        try:
            # Menggunakan TextClip standard MoviePy 1.0.3
            txt = TextClip(topic.upper(), fontsize=60, color='white', font='Arial-Bold', 
                          stroke_color='black', stroke_width=3, method='caption', 
                          size=(900, None), align='center')
            txt = txt.set_position(('center', 1500)).set_duration(duration)
            final_video = CompositeVideoClip([clip, txt])
        except:
            print("   ⚠️ Text render skip")
            final_video = clip
        
        # D. Write File
        print("   🚀 Rendering Final Video...")
        final_video.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac", 
                                    preset="ultrafast", verbose=False, logger=None)
        
        # Cleanup
        clip.close()
        if 'vo_clip' in locals(): vo_clip.close()
        if 'bg_music' in locals(): bg_music.close()
        
        return output_file

    except Exception as e:
        print(f"   ❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None