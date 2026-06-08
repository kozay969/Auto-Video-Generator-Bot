#!/usr/bin/env python3
import argparse
import json
import os
import sys
import requests

def generate_script(topic: str, duration_minutes: int) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY မတွေ့ပါ!")
        sys.exit(1)
        
    words_per_minute = 120
    target_words = words_per_minute * duration_minutes
    
    prompt = f"""သင်သည် မြန်မာဘာသာဖြင့် ဗီဒီယိုကြည့်ရှုသူများအတွက် engaging content ရေးသားသော expert တစ်ဦးဖြစ်သည်။
Topic: {topic}
Video Duration: {duration_minutes} မိနစ်

အောက်ပါ format အတိုင်း JSON ပုံစံဖြင့်သာ ပြန်လည်ဖြေကြားပေးပါ:
{{
  "title": "ဗီဒီယိုခေါင်းစဉ်",
  "hook": "ပထမ ၁၀ စက္ကန့်အတွင်း ဆွဲဆောင်မည့်ဝါကျ",
  "sections": [
    {{ "heading": "အပိုင်းခေါင်းစဉ်", "content": "ဤအပိုင်း၏ အသေးစိတ်ရှင်းလင်းချက် မြန်မာလို", "duration_seconds": 60 }}
  ],
  "outro": "နိဂုံးချုပ် စာသား",
  "full_script": "အပိုင်း အားလုံးပေါင်းထားသော အပြည့်အစုံ script (မြန်မာဘာသာ သီးသန့်)",
  "thumbnail_text": "Thumbnail စာသား",
  "tags": ["tag1"]
}}"""

    # 💡 Google API သို့ တိုက်ရိုက် HTTPS Request ပို့ခြင်း
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"} # JSON သီးသန့်ထုတ်ခိုင်းခြင်း
    }
    
    print(f"🤖 REST API သို့ တိုက်ရိုက် Request ပို့နေသည်...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        sys.exit(1)
        
    res_json = response.json()
    try:
        # Gemini ထံမှ ပြန်လာသော Text ကို ယူခြင်း
        raw_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        return json.loads(raw_text)
    except Exception as e:
        print(f"⚠️ JSON Parse Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--duration", type=int, default=3)
    args = parser.parse_args()
    
    script_data = generate_script(args.topic, args.duration)
    os.makedirs("output", exist_ok=True)
    with open("output/script_data.json", "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script_data.get("full_script", ""))
    print(f"✅ အောင်မြင်စွာ Script ထုတ်ပြီး!")

if __name__ == "__main__":
    main()
    
