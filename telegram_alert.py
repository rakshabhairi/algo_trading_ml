import requests

def send_telegram_message(message):
    token = "your_token"  # replace with your bot token
    chat_id = "ur_chatid"  # replace with your chat ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={'chat_id': chat_id, 'text': message})
