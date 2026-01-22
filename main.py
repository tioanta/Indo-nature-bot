import generate_video
import upload_youtube
import random

def main():
    # Daftar topik agar konten tidak monoton
    topics = [
        "Saudi Arabia Al Ula Desert",
        "Red Sea Saudi Arabia Beach",
        "Makkah Clock Tower View",
        "Madinah Green Dome",
        "Saudi Arabia Oasis Nature",
        "Tabuk Mountains Snow Saudi",
        "Riyadh Cityscape Night",
        "Jeddah Corniche Waterfront"
    ]
    
    # Pilih 1 topik acak untuk hari ini
    today_topic = random.choice(topics)
    print(f"=== TEMA HARI INI: {today_topic} ===")

    print("1. Mencari Video...")
    raw_video = generate_video.get_pexels_video(topic=today_topic)
    
    if raw_video:
        print("2. Memproses Video...")
        final_video = generate_video.process_video(raw_video)
        
        print("3. Mengupload ke YouTube dengan AI Caption...")
        # Kirim file video DAN topiknya agar caption nyambung
        upload_youtube.upload_video(final_video, topic=today_topic)
        
        print("Selesai! Misi sukses.")
    else:
        print("Gagal mendapatkan video.")

if __name__ == "__main__":
    main()
