#!/usr/bin/env python3
"""
Step 4: Telegram Bot သုံးပြီး Video ပို့မည်
"""

import argparse
import asyncio
import json
import os
import sys
import requests


def send_video_telegram(
    bot_token: str,
    chat_id: str,
    video_path: str,
    caption: str,
    topic: str
) -> bool:
    """Telegram Bot API သုံးပြီး video ပို့မည် (requests library - simple)"""
    
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"📤 Telegram ပို့နေသည်... ({file_size_mb:.1f} MB)")
    
    # Telegram file size limit: 50MB for bots
    if file_size_mb > 50:
        print(f"⚠️ File size {file_size_mb:.1f}MB > 50MB limit!")
        print("📝 Caption only mode...")
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": f"🎬 Video ထုတ်ပြီးပါပြီ!\n\n{caption}\n\n⚠️ File size {file_size_mb:.1f}MB - GitHub Artifacts မှ download လုပ်ပါ",
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data, timeout=30)
        return response.status_code == 200
    
    # Send video
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    
    with open(video_path, 'rb') as video_file:
        files = {'video': (os.path.basename(video_path), video_file, 'video/mp4')}
        data = {
            'chat_id': chat_id,
            'caption': caption,
            'parse_mode': 'HTML',
            'supports_streaming': 'true'
        }
        
        response = requests.post(
            url, 
            files=files, 
            data=data, 
            timeout=300  # 5 min timeout for large files
        )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('ok'):
            print(f"✅ Telegram တွင် video ပို့ပြီး!")
            return True
        else:
            print(f"❌ Telegram API error: {result.get('description')}")
            return False
    else:
        print(f"❌ HTTP error: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False


def format_caption(script_data: dict, topic: str, video_info: dict) -> str:
    """Telegram caption ရေးမည်"""
    title = script_data.get("title", topic)
    tags = script_data.get("tags", [])
    duration = video_info.get("duration", 0)
    
    # Format tags
    tag_str = " ".join([f"#{t.replace(' ', '_')}" for t in tags[:5]])
    
    caption = f"""🎬 <b>{title}</b>

⏱ Duration: {int(duration // 60)}:{int(duration % 60):02d} minutes
🤖 Auto-generated with AI

━━━━━━━━━━━━━━━
{tag_str}
#AutoVideo #MyanmarContent #AI"""
    
    return caption


def send_status_message(bot_token: str, chat_id: str, message: str) -> None:
    """Status message ပို့မည်"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data, timeout=30)
    except:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="", help="Video topic")
    args = parser.parse_args()
    
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set!")
        sys.exit(1)
    
    # Load data
    with open("output/script_data.json", "r", encoding="utf-8") as f:
        script_data = json.load(f)
    
    with open("output/video_info.json", "r") as f:
        video_info = json.load(f)
    
    video_path = video_info["path"]
    
    if not os.path.exists(video_path):
        print(f"❌ Video file မတွေ့ပါ: {video_path}")
        sys.exit(1)
    
    # Send "generating" status
    send_status_message(
        bot_token, chat_id,
        f"🎬 Video ထုတ်ပြီးပါပြီ!\n📤 Upload လုပ်နေသည်..."
    )
    
    # Format caption
    caption = format_caption(script_data, args.topic, video_info)
    
    # Send video
    success = send_video_telegram(
        bot_token=bot_token,
        chat_id=chat_id,
        video_path=video_path,
        caption=caption,
        topic=args.topic
    )
    
    if success:
        print("🎉 အားလုံး အောင်မြင်ပါတယ်!")
    else:
        # Fallback: send as document
        print("⚠️ Video ပို့မရ၊ document အနေနဲ့ ကြိုးစားမည်...")
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        with open(video_path, 'rb') as f:
            files = {'document': (os.path.basename(video_path), f, 'video/mp4')}
            data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'}
            response = requests.post(url, files=files, data=data, timeout=300)
        
        if response.status_code == 200:
            print("✅ Document အနေနဲ့ ပို့ပြီး!")
        else:
            print(f"❌ Final error: {response.text[:200]}")
            sys.exit(1)


if __name__ == "__main__":
    main()
          
