import requests

def send_telegram_message(message):
    token = "8244029092:AAFzkl2-EWbhmntkzkLW_gQh1c9EThxLqyU"  # replace with your bot token
    chat_id = "7073228896"  # replace with your chat ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={'chat_id': chat_id, 'text': message})
