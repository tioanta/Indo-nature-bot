import os
import requests
import random
from moviepy.editor import VideoFileClip, AudioFileClip

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

# Daftar Nama File Resmi di Wikimedia (Sudah diperbaiki dari typo)
MUSIC_TITLES = [
    "File:Erik_Satie_-_Gymnopedie_No_1.ogg",
    "File:Frederic_Chopin_-_Nocturne_in_E_flat_major,_Op._9,_No._2.ogg", 
    "File:Claude_Debussy_-_Clair_de_lune.ogg"
]

def get_wikimedia_direct_url(title):
    """Mendapatkan Link Download Asli via API Wikimedia dengan Penyamaran Browser"""
    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "iiprop": "url",
        "titles": title
    }
    
    # Header Browser Chrome Asli (Agar tidak diblokir 403)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' 
    }

    try:
        response = requests.get(api_url, params=params, headers=headers)
        data = response.json()
        pages = data['query']['pages']
        for page_id in pages:
            if 'imageinfo' in pages[page_id]:
                return pages[page_id]['imageinfo'][0]['url']
    except Exception as e:
        print(f"   Gagal mengambil API untuk {title}: {e}")
    
    return None

def get_pexels_video(topic="Nature Scenery", orientation="portrait"):
    headers = {"Authorization": PEXELS_API_KEY}
    
    print(f"1. Searching Pexels for: {topic}")
    url = f"https://api.pexels.com/videos/search?query={topic}&per_page=15&orientation={orientation}"
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except Exception as e:
        print(f"Error connecting to Pexels: {e}")
        return None
    
    if not data.get('videos'):
        print(f"Video tidak ditemukan untuk: {topic}")
        return None

    video_data = random.choice(data['videos'])
    video_files = video_data['video_files']
    
    valid_files = [v for v in video_files if v['width'] >= 720]
    if not valid_files:
        valid_files = video_files 
        
    chosen_file = valid_files[0]
    download_url = chosen_file['link']
    
    print(f"   Downloading video...")
    r = requests.get(download_url)
    video_filename = "input_video.mp4"
    with open(video_filename, 'wb') as f:
        f.write(r.content)
        
    return video_filename

def get_background_music():
    print("2. Mencari & Download Musik Latar (via API)...")
    
    # Gunakan Header Chrome yang sama untuk proses download file
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # Loop percobaan: Jika lagu pertama gagal, coba lagu lain
        # Kita acak urutannya, lalu coba satu per satu sampai berhasil
        shuffled_titles = random.sample(MUSIC_TITLES, len(MUSIC_TITLES))
        
        for title in shuffled_titles:
            print(f"   Mencoba lagu: {title}")
            music_url = get_wikimedia_direct_url(title)
            
            if not music_url:
                print("   Link tidak ditemukan, coba lagu berikutnya...")
                continue # Coba judul berikutnya

            print(f"   URL didapat, mulai download...")
            r = requests.get(music_url, headers=headers, stream=True)
            
            if r.status_code == 200:
                audio_filename = "bg_music.ogg"
                with open(audio_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                
                if os.path.getsize(audio_filename) > 10000:
                    print("   Download Sukses!")
                    return audio_filename # Berhasil, keluar dari loop
            
            print(f"   Gagal download (Status {r.status_code}), mencoba lagu lain...")
            
        return None # Jika semua lagu gagal

    except Exception as e:
        print(f"   Error sistem download musik: {e}")
        return None

def process_video(input_video_path):
    output_file = "final_short.mp4"
    
    try:
        video_clip = VideoFileClip(input_video_path)
    except Exception as e:
        print(f"Error membaca video: {e}")
        return None
    
    duration = min(video_clip.duration, 15) 
    video_clip = video_clip.subclip(0, duration)
    
    if video_clip.w > video_clip.h:
        new_width = video_clip.h * 9 / 16
        x1 = (video_clip.w / 2) - (new_width / 2)
        video_clip = video_clip.crop(x1=x1, width=new_width, height=video_clip.h)
    
    audio_path = get_background_music()
    final_clip = video_clip
    
    if audio_path:
        try:
            audio_clip = AudioFileClip(audio_path)
            
            if audio_clip.duration < duration:
                from moviepy.audio.AudioClip import CompositeAudioClip
                loops = int(duration / audio_clip.duration) + 1
                audio_clip = CompositeAudioClip([audio_clip.set_start(i * audio_clip.duration) for i in range(loops)])
            
            audio_clip = audio_clip.subclip(0, duration)
            audio_clip = audio_clip.volumex(0.8)
            
            final_clip = video_clip.set_audio(audio_clip)
            print("   Sukses menggabungkan Audio + Video.")
            
        except Exception as e:
            print(f"   Error saat merging audio: {e}. Video akan bisu.")
    else:
        print("   Audio tidak tersedia (semua download gagal). Video akan bisu.")

    print("3. Rendering Final Video...")
    # Preset ultrafast & codec aac
    final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", preset="ultrafast")
    
    try:
        video_clip.close()
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
    except:
        pass
        
    return output_file
