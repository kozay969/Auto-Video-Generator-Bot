#!/usr/bin/env python3
"""
Step 2: gTTS သုံးပြီး Myanmar ဘာသာဖြင့် အသံသွင်းမည်
"""

import json
import os
import subprocess
from gtts import gTTS


def text_to_speech_myanmar(text: str, output_path: str) -> bool:
    """gTTS သုံးပြီး Myanmar TTS ထုတ်မည်"""
    try:
        # Myanmar language code: 'my'
        tts = gTTS(text=text, lang='my', slow=False)
        
        # Save as mp3 first
        mp3_path = output_path.replace('.wav', '.mp3')
        tts.save(mp3_path)
        
        # Convert to WAV with proper settings for video
        subprocess.run([
            'ffmpeg', '-y',
            '-i', mp3_path,
            '-ar', '44100',   # Sample rate
            '-ac', '2',       # Stereo
            '-acodec', 'pcm_s16le',
            output_path
        ], check=True, capture_output=True)
        
        # Cleanup mp3
        os.remove(mp3_path)
        
        print(f"✅ TTS ထုတ်ပြီး: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ TTS error: {e}")
        # Try English fallback
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            mp3_path = output_path.replace('.wav', '.mp3')
            tts.save(mp3_path)
            subprocess.run([
                'ffmpeg', '-y', '-i', mp3_path,
                '-ar', '44100', '-ac', '2',
                '-acodec', 'pcm_s16le', output_path
            ], check=True, capture_output=True)
            os.remove(mp3_path)
            return True
        except Exception as e2:
            print(f"❌ Fallback TTS error: {e2}")
            return False


def split_text_for_tts(text: str, max_chars: int = 500) -> list[str]:
    """Long text ကို chunks ခွဲမည် (gTTS limit ကြောင့်)"""
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    sentences = text.replace('။', '။|').replace('.', '.|').split('|')
    
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text[:max_chars]]


def main():
    print("🔊 TTS ထုတ်နေသည်...")
    
    os.makedirs("output/audio", exist_ok=True)
    
    # Load script
    with open("output/script_data.json", "r", encoding="utf-8") as f:
        script_data = json.load(f)
    
    full_script = script_data.get("full_script", "")
    
    if not full_script:
        print("❌ Script မတွေ့ပါ!")
        exit(1)
    
    print(f"📝 Script length: {len(full_script)} characters")
    
    # Split into chunks
    chunks = split_text_for_tts(full_script, max_chars=400)
    print(f"🔀 {len(chunks)} chunks ခွဲထားသည်")
    
    audio_files = []
    
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
            
        chunk_path = f"output/audio/chunk_{i:03d}.wav"
        print(f"  🎙️ Chunk {i+1}/{len(chunks)} - {len(chunk)} chars")
        
        if text_to_speech_myanmar(chunk, chunk_path):
            audio_files.append(chunk_path)
        else:
            print(f"  ⚠️ Chunk {i} failed, skipping...")
    
    if not audio_files:
        print("❌ Audio files မထုတ်နိုင်ပါ!")
        exit(1)
    
    # Merge all audio chunks
    print("🔗 Audio chunks များ ပေါင်းစပ်နေသည်...")
    
    # Create concat file
    concat_file = "output/audio/concat_list.txt"
    with open(concat_file, "w") as f:
        for audio_file in audio_files:
            f.write(f"file '{os.path.abspath(audio_file)}'\n")
    
    # Merge with FFmpeg
    merged_audio = "output/audio/full_audio.wav"
    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-ar', '44100',
        '-ac', '2',
        merged_audio
    ], check=True, capture_output=True)
    
    # Get duration
    result = subprocess.run([
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format', merged_audio
    ], capture_output=True, text=True)
    
    probe_data = json.loads(result.stdout)
    duration = float(probe_data['format']['duration'])
    
    print(f"✅ Audio ထုတ်ပြီး: {duration:.1f} seconds")
    
    # Save audio info
    with open("output/audio_info.json", "w") as f:
        json.dump({"duration": duration, "path": merged_audio}, f)


if __name__ == "__main__":
    main()
  
