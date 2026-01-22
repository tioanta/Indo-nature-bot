import generate_video
import upload_youtube
import random

def main():
    # Daftar Destinasi Global (Bisa Anda tambah sesuka hati)
    # Format: "Negara + Kata Kunci Alam" agar hasil video Pexels akurat
    destinations = [
        "Switzerland Alps Nature",
        "Japan Kyoto Nature",
        "Indonesia Bali Rice Field",
        "Iceland Aurora Borealis",
        "New Zealand Landscape",
        "Saudi Arabia Al Ula Desert", # Tetap masukkan Saudi
        "Norway Fjords",
        "Canada Rocky Mountains",
        "Italy Amalfi Coast",
        "Vietnam Ha Long Bay",
        "Peru Machu Picchu Nature",
        "Australia Great Barrier Reef"
    ]
    
    # Pilih 1 destinasi acak untuk hari ini
    today_topic = random.choice(destinations)
    print(f"=== TEMA HARI INI: {today_topic} ===")

    print("1. Mencari Video...")
    # Script ini akan mencari video sesuai negara yang terpilih
    raw_video = generate_video.get_pexels_video(topic=today_topic)
    
    if raw_video:
        print("2. Memproses Video (Crop Vertical)...")
        final_video = generate_video.process_video(raw_video)
        
        print(f"3. Mengupload ke YouTube (Topic: {today_topic})...")
        # Kirim topiknya ke fungsi upload agar AI tahu ini negara mana
        upload_youtube.upload_video(final_video, topic=today_topic)
        
        print("Selesai! Video tayang.")
    else:
        print("Gagal mendapatkan video, coba lagi besok.")

if __name__ == "__main__":
    main()
