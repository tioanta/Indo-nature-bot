import generate_video
import upload_youtube
import random

def main():
    # DAFTAR TOPIK MUSIK RELAXING & FOCUSING (untuk konten YouTube 20 menit)
    # Setiap topik akan dipasangkan dengan musik dan visual yang sesuai
    topics = [
        # --- GENRE 1: LOFI & STUDY (Fokus & Belajar) ---
        "Lofi Hip Hop Beats for Study",
        "Chill Lo-fi Music for Studying",
        "Deep Focus Ambient Music",
        "Productive Work Music",
        
        # --- GENRE 2: MEDITATION & RELAXATION ---
        "Calm Meditation Music",
        "Sleep Relaxation Sounds",
        "Peaceful Zen Music",
        "Stress Relief Ambient",
        
        # --- GENRE 3: NATURE SOUNDS & RAIN ---
        "Forest Rain Sounds",
        "Ocean Waves Relaxing",
        "Rain and Thunder",
        "Nature Ambient Sounds"
    ]
    
    # Pilih 1 topik acak
    today_topic = random.choice(topics)
    print(f"=== TEMA HARI INI: {today_topic} ===")

    print("1. Mengumpulkan Musik (20 menit)...")
    music_path = generate_video.get_relaxing_music(topic=today_topic)
    
    if music_path:
        print("2. Membuat Video dengan Background Visual (20 menit)...")
        # PENTING: Kita kirim 'today_topic' agar visualnya nyambung!
        final_video = generate_video.create_music_video(music_path, topic=today_topic)
        
        if final_video:
            print(f"3. Mengupload ke YouTube (Topic: {today_topic})...")
            upload_youtube.upload_video(final_video, topic=today_topic)
            
            print("Selesai! Misi sukses.")
        else:
            print("Gagal membuat video dengan musik.")
    else:
        print("Gagal mengumpulkan musik berkualitas.")

if __name__ == "__main__":
    main()
