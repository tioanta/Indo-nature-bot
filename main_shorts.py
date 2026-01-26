import generate_shorts
import upload_shorts
import random

def main():
    # DAFTAR TOPIK SHORTS (Rotasi 3 Topik)
    topics = [
        # 1. Manchester United
        "Manchester United Old Trafford Atmosphere",
        "Red Devils Football Passion",
        "Manchester United Glory",
        
        # 2. Masjidil Haram / Makkah
        "Masjidil Haram Kaaba Peace",
        "Makkah Clock Tower Night",
        "Islamic Architecture Makkah",
        
        # 3. Japan City Vibes
        "Tokyo Night Walk Vibes",
        "Japan City Rainy Aesthetic",
        "Kyoto Street Traditional",
        "Shibuya Crossing Timelapse"
    ]
    
    # Pilih 1 topik acak
    today_topic = random.choice(topics)
    print(f"=== SHORTS TOPIC: {today_topic} ===")

    print("1. Mencari Konten Vertical & Audio...")
    # Durasi Shorts aman di 58 detik (agar tidak lebih dari 60s)
    music_path = generate_shorts.get_music(topic=today_topic)
    
    if music_path:
        print("2. Render Video Vertical (9:16)...")
        final_video = generate_shorts.create_short_video(music_path, topic=today_topic, duration=58)
        
        if final_video:
            print(f"3. Upload Shorts ke YouTube...")
            upload_shorts.upload_video(final_video, topic=today_topic)
            print("Done! Shorts uploaded.")
        else:
            print("Gagal render video.")
    else:
        print("Gagal download musik.")

if __name__ == "__main__":
    main()
