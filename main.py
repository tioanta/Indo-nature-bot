import generate_video
import upload_youtube
import random

def main():
    # DAFTAR TOPIK CAMPURAN (Alam, Anime/Jepang, Sepakbola)
    # Kita gunakan kata kunci yang "Pexels-Friendly"
    topics = [
        # --- GENRE 1: NATURE (ALAM) ---
        "Switzerland Alps Nature",
        "Indonesia Bali Rice Field",
        "Iceland Aurora Borealis",
        "Raja Ampat Ocean",
        
        # --- GENRE 2: ANIME VIBES & JAPAN (Cosplay/City) ---
        "Cosplay Anime Japan",      # Akan cari video orang kostum
        "Tokyo Akihabara Night",    # Vibes kota anime
        "Japan Cyberpunk Neon",     # Vibes futuristik
        "Samurai Sword Fight",      # Vibes aksi
        
        # --- GENRE 3: FOOTBALL (SEPAKBOLA) ---
        "Soccer Football Match",    # Pertandingan umum
        "Football Player Training", # Latihan skill
        "Soccer Stadium Atmosphere",# Suasana stadion
        "Futsal Skills"             # Skill bola
    ]
    
    # Pilih 1 topik acak
    today_topic = random.choice(topics)
    print(f"=== TEMA HARI INI: {today_topic} ===")

    print("1. Mencari Video...")
    raw_video = generate_video.get_pexels_video(topic=today_topic)
    
    if raw_video:
        print("2. Memproses Video (Edit + Musik)...")
        # PENTING: Kita kirim 'today_topic' agar musiknya nyambung!
        final_video = generate_video.process_video(raw_video, topic=today_topic)
        
        print(f"3. Mengupload ke YouTube (Topic: {today_topic})...")
        upload_youtube.upload_video(final_video, topic=today_topic)
        
        print("Selesai! Misi sukses.")
    else:
        print("Gagal mendapatkan video.")

if __name__ == "__main__":
    main()
