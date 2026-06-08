#!/usr/bin/env python3
import argparse
import json
import os
import sys
import requests

def generate_script(topic: str, duration_minutes: int) -> dict:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("❌ Error: GROQ_API_KEY environment variable is missing!")
        sys.exit(1)
        
    words_per_minute = 120
    target_words = words_per_minute * duration_minutes
    
    prompt = f"""သင်သည် မြန်မာဘာသာဖြင့် ဗီဒီယိုကြည့်ရှုသူများအတွက် engaging content ရေးသားသော expert တစ်ဦးဖြစ်သည်။
Topic: {topic}
Video Duration: {duration_minutes} မိနစ်

အောက်ပါ format အတိုင်း JSON ပုံစံဖြင့်သာ ကွက်တိ ပြန်လည်ဖြေကြားပေးပါ (အခြား စကားပြောအပိုများ လုံးဝမထည့်ပါနှင့်):
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

    # Groq API သို့ လှမ်းခေါ်ခြင်း (Llama 3 မော်ဒယ်ကို သုံးထားပါသည်)
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "response_format": {"type": "json_object"}, # 💡 JSON ကွက်တိ ထွက်စေရန် ခိုင်းခြင်း
        "messages": [
            {"role": "system", "content": "You are a chatbot that only replies in JSON format."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    print(f"🤖 Groq API (Llama 3) သို့ တိုက်ရိုက် Request ပို့နေသည်...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"❌ Groq API Error: {response.status_code} - {response.text}")
        sys.exit(1)
        
    try:
        raw_text = response.json()['choices'][0]['message']['content'].strip()
        return json.loads(raw_text)
    except Exception as e:
        print(f"❌ JSON Parse Error: {e}")
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
    print(f"✅ Groq ဖြင့် Script ထုတ်ပြီး!")

if __name__ == "__main__":
    main()
                  
