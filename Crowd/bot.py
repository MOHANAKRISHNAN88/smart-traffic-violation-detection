import requests
import telebot

TOKEN = "7695804495:AAGjeDcJRGaiTyWgAW-gtDUrozNAcqS596A"
CHAT_ID = "2132444686"
SERVER_URL = "http://localhost:5000"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome to TrafficAI! Send 'Which route is best?', 'I'm in Zone X', or 'Show road details'.")

@bot.message_handler(func=lambda message: message.text.lower() == "which route is best?")
def suggest_best_route(message):
    response = requests.get(f"{SERVER_URL}/get_traffic_data").json()
    if "vehicles_per_zone" in response:
        best_zone = min(response["vehicles_per_zone"], key=response["vehicles_per_zone"].get)
        bot.reply_to(message, f"The best route is via {best_zone}.")
    else:
        bot.reply_to(message, "Unable to retrieve traffic data.")

@bot.message_handler(func=lambda message: message.text.lower().startswith("i'm in zone"))
def suggest_alternate_route(message):
    user_zone = message.text.lower().split()[-1]
    response = requests.get(f"{SERVER_URL}/get_traffic_data").json()
    if "vehicles_per_zone" in response:
        congestion_level = response["vehicles_per_zone"].get(user_zone, None)
        if congestion_level is not None and congestion_level > 10:
            best_zone = min(response["vehicles_per_zone"], key=response["vehicles_per_zone"].get)
            bot.reply_to(message, f"Traffic is high in {user_zone}. Consider moving to {best_zone}.")
        else:
            bot.reply_to(message, f"Traffic is normal in {user_zone}.")
    else:
        bot.reply_to(message, "Unable to retrieve traffic data.")

@bot.message_handler(func=lambda message: message.text.lower() == "show highest speed")
def show_highest_speed(message):
    response = requests.get(f"{SERVER_URL}/get_traffic_data").json()
    if "highest_speed" in response:
        bot.reply_to(message, f"The highest recorded speed is {response['highest_speed']} km/h.")
    else:
        bot.reply_to(message, "Speed data is unavailable.")

@bot.message_handler(func=lambda message: message.text.lower() == "show road details")
def show_road_details(message):
    response = requests.get(f"{SERVER_URL}/get_traffic_data").json()
    if "road_conditions" in response:
        bot.reply_to(message, f"Current road conditions: {response['road_conditions']}.")
    else:
        bot.reply_to(message, "Road condition data is unavailable.")

@bot.message_handler(func=lambda message: message.text.lower() == "live traffic update")
def live_traffic_update(message):
    response = requests.get(f"{SERVER_URL}/get_traffic_data").json()
    if "vehicles_per_zone" in response:
        congested_zones = [zone for zone, count in response["vehicles_per_zone"].items() if count > 10]
        if congested_zones:
            bot.reply_to(message, f"🚦 Heavy traffic in {', '.join(congested_zones)}. Consider alternate routes.")
        else:
            bot.reply_to(message, "✅ Traffic is normal across all zones.")
    else:
        bot.reply_to(message, "Traffic data is unavailable.")

bot.polling()
