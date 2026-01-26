import generate_shorts
import upload_shorts
import random

def main():
    # DAFTAR TOPIK
    topics = [
        "Manchester United Old Trafford Atmosphere",
        "Keindahan Masjidil Haram Makkah",
        "Japan City Night Vibes Tokyo",
        "Semangat Fans Manchester United",
        "Suasana Hujan di Kyoto Jepang"
    ]
    
    today_topic = random.choice(topics)
    print(f"=== SHORTS TOPIC: {today_topic} ===")

    print("1. Memulai Generasi Video dengan Voice Over...")
    # Panggil fungsi create_short_video dengan parameter use_vo=True
    final_video = generate_shorts.create_short_video(topic=today_topic, use_vo=True, duration=58)
    
    if final_video:
        print("2. Upload Shorts ke YouTube...")
        upload_shorts.upload_video(final_video, topic=today_topic)
        print("✅ Misi Selesai!")
    else:
        print("❌ Gagal membuat video.")

if __name__ == "__main__":
    main()