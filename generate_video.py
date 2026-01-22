import os
import requests
import random
from moviepy.editor import VideoFileClip, AudioFileClip

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

def get_pexels_video(topic="Nature Scenery", orientation="portrait"):
    headers = {"Authorization": PEXELS_API_KEY}
    print(f"1. Searching Pexels for: {topic}")
    url = f"https://api.pexels.com/videos/search?query={topic}&per_page=15&orientation={orientation}"
    
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        if not data.get('videos'): return None
        
        # Pilih video random & utamakan HD
        video_files = random.choice(data['videos'])['video_files']
        valid_files = [v for v in video_files if v['width'] >= 720] or video_files
        download_url = valid_files[0]['link']
        
        print(f"   Downloading video...")
        with open("input_video.mp4", 'wb') as f:
            f.write(requests.get(download_url).content)
        return "input_video.mp4"
    except Exception as e:
        print(f"Error Pexels: {e}")
        return None

def get_background_music(topic):
    print(f"2. Mencari Musik yang cocok untuk: {topic}...")
    
    # --- LOGIKA PEMILIHAN MUSIK ---
    topic_lower = topic.lower()
    
    if "soccer" in topic_lower or "football" in topic_lower or "futsal" in topic_lower:
        keywords = ["Energetic Rock ogg", "Sport action music ogg", "Upbeat drum ogg"]
        print("   -> Mode: SPORT / SEMANGAT")
        
    elif "anime" in topic_lower or "japan" in topic_lower or "tokyo" in topic_lower:
        keywords = ["Electronic upbeat ogg", "Techno music ogg", "Synthesizer pop ogg"]
        print("   -> Mode: ANIME / JEPANG")
        
    else: # Default (Nature)
        keywords = ["Erik Satie Gymnopedie ogg", "Piano relaxing ogg", "Nature ambient ogg"]
        print("   -> Mode: SANTAI / ALAM")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
    
    # Coba cari lagu
    for keyword in random.sample(keywords, len(keywords)):
        print(f"   Mencari lagu: '{keyword}'")
        music_url = get_wikimedia_search_url(keyword)
        if music_url:
            r = requests.get(music_url, headers=headers, stream=True)
            if r.status_code == 200:
                with open("bg_music.ogg", 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024): f.write(chunk)
                if os.path.getsize("bg_music.ogg") > 20000: return "bg_music.ogg"
    return None

def process_video(input_video_path, topic):
    output_file = "final_short.mp4"
    try:
        video_clip = VideoFileClip(input_video_path)
    except: return None
    
    # Potong 15 detik & Crop Vertikal
    duration = min(video_clip.duration, 15)
    video_clip = video_clip.subclip(0, duration)
    if video_clip.w > video_clip.h:
        video_clip = video_clip.crop(x1=video_clip.w/2 - video_clip.h*9/32, width=video_clip.h*9/16, height=video_clip.h)
    
    # Tambah Audio Sesuai Topik
    audio_path = get_background_music(topic)
    final_clip = video_clip
    
    if audio_path:
        try:
            audio_clip = AudioFileClip(audio_path)
            if audio_clip.duration < duration:
                from moviepy.audio.AudioClip import CompositeAudioClip
                loops = int(duration / audio_clip.duration) + 1
                audio_clip = CompositeAudioClip([audio_clip.set_start(i*audio_clip.duration) for i in range(loops)])
            
            final_clip = video_clip.set_audio(audio_clip.subclip(0, duration).volumex(0.8))
        except: pass

    print("3. Rendering Final Video...")
    final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", preset="ultrafast")
    
    try:
        video_clip.close()
        if audio_path: os.remove(audio_path)
    except: pass
    return output_file
