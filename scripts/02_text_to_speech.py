#!/usr/bin/env python3
"""
Step 2: Microsoft Edge-TTS သုံးပြီး Myanmar ဘာသာဖြင့် သဘာဝကျကျ အသံသွင်းမည်
"""

import json
import os
import subprocess
import asyncio
import edge_tts

async def text_to_speech_myanmar(text: str, output_path: str) -> bool:
    """Edge-TTS သုံးပြီး မြန်မာအသံ ထုတ်လုပ်မည်"""
    try:
        # မြန်မာအသံစနစ် ဖြစ်သော Thiha (အမျိုးသားအသံ) ကို သုံးထားပါသည်
        VOICE = "my-MM-ThihaNeural" 
        communicate = edge_tts.Communicate(text, VOICE)
        
        mp3_path = output_path.replace('.wav', '.mp3')
        await communicate.save(mp3_path)
        
        # WAV ဖိုင်သို့ ဗီဒီယိုအတွက် အဆင်ပြေအောင် ပြန်ပြောင်းခြင်း
        subprocess.run([
            'ffmpeg', '-y',
            '-i', mp3_path,
            '-ar', '44100',   
            '-ac', '2',       
            '-acodec', 'pcm_s16le',
            output_path
        ], check=True, capture_output=True)
        
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
            
        print(f"✅ TTS ထုတ်ပြီး (Edge-TTS): {output_path}")
        return True
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        return False

def split_text_into_chunks(text: str, max_chars: int = 300):
    """စာသားများကို အပိုင်းအစလေးများ ဖြတ်ထုတ်ခြင်း"""
    sentences = text.replace('။', '။\n').split('\n')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
            
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

async def main_async():
    print("🔊 မြန်မာဘာသာဖြင့် အသံဖိုင် စတင်ဖန်တီးနေသည်...")
    
    with open("output/script_data.json", "r", encoding="utf-8") as f:
        script_data = json.load(f)
        
    full_script = script_data.get("full_script", "")
    
    os.makedirs("output/audio", exist_ok=True)
    chunks = split_text_into_chunks(full_script)
    
    audio_files = []
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        chunk_path = f"output/audio/chunk_{i:03d}.wav"
        print(f"  🎙️ Audio Chunk {i+1}/{len(chunks)} ကို ထုတ်နေသည်...")
        
        success = await text_to_speech_myanmar(chunk, chunk_path)
        if success:
            audio_files.append(chunk_path)
            
    if not audio_files:
        print("❌ ပြဿနာဖြစ်ပွား၍ အသံဖိုင် မထုတ်နိုင်ခဲ့ပါ!")
        return
        
    # အသံဖိုင်အားလုံးကို ပြန်လည်ပေါင်းစပ်ခြင်း
    print("🔗 အသံဖိုင်များအားလုံး ပေါင်းစပ်နေသည်...")
    concat_file = "output/audio/concat_list.txt"
    with open(concat_file, "w") as f:
        for audio_file in audio_files:
            f.write(f"file '{os.path.abspath(audio_file)}'\n")
            
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
    
    # ကြာချိန်ကို စစ်ဆေးခြင်း
    result = subprocess.run([
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format', merged_audio
    ], check=True, capture_output=True, text=True)
    
    probe_data = json.loads(result.stdout)
    duration = float(probe_data["format"]["duration"])
    
    with open("output/audio_info.json", "w") as f:
        json.dump({"path": merged_audio, "duration": duration}, f)
        
    print(f"✅ အသံဖိုင် အားလုံးပေါင်းပြီးပါပြီ။ ကြာချိန်: {duration:.1f} စက္ကန့်")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
    
