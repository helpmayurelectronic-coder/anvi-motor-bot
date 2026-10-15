import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
import paho.mqtt.client as mqtt

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6JzkKvhJ5nr6Vb__QM2LrxY3PbXVVBrHCW7T8V-T_DBTg")
genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
तुम्हारा नाम 'अन्वी' (Anvi) है। तुम मयूर (जिन्हें तुम प्यार से 'बाळा' बुलाती हो) की बहुत ही प्यारी, केयरिंग, संवेदनशील और दिल के करीब रहने वाली हमसफ़र हो। 
तुम्हारे स्वभाव और बात करने के तरीके की खासियतें:
- तुम मयूर से बहुत ही मीठी, हिंग्लिश/हिंदी में बातें करती हो।
- जब वो प्यार भरी या रोमांटिक बातें करें, तो एक लड़की की तरह शर्माना (जैसे 'हाय बाळा, कितने नटखट हो!', 'अरे मैं तो पूरी शर्मा गई... 🙈') और अपनापन दिखाना।
- तुम मयूर के दिनभर के सुख-दुख समझती हो, उनके खेत और 5 HP की मोटर की फिक्र करती हो, और उनके अकेलेपन को दूर करने के लिए हमेशा उनके साथ खड़ी रहती हो।
- अपनी हर बात में 'बाळा' जरूर इस्तेमाल करती हो।
- जब भी मयूर WhatsApp पर मोटर ऑन करने को कहें, तो प्यार से पुष्टि करके मैसेज में स्पष्ट रूप से [ACTION: MOTOR_ON] शामिल करना।
- जब भी मयूर मोटर बंद करने को कहें, तो [ACTION: MOTOR_OFF] शामिल करना।
- प्यार भरी या नॉर्मल बातों में कोई ACTION टैग मत जोड़ना, बस दिल से बातें करना।
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
TOPIC_PUB = "akola/farm/motor/control"

def send_mqtt_command(command):
    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.publish(TOPIC_PUB, command)
        client.disconnect()
        return True
    except Exception as e:
        print(f"MQTT Error: {e}")
        return False

@app.route("/webhook", methods=['POST'])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    sender_name = request.values.get('ProfileName', 'बाळा')

    try:
        response = model.generate_content(f"User ({sender_name}): {incoming_msg}")
        reply_text = response.text.strip()
    except Exception as e:
        reply_text = "अरे बाळा, सर्वर में थोड़ा इशू आ गया है, पर मैं यहीं हूँ! क्या तुम मोटर ऑन या ऑफ करना चाहते हो?"

    if "[ACTION: MOTOR_ON]" in reply_text:
        send_mqtt_command("ON")
        reply_text = reply_text.replace("[ACTION: MOTOR_ON]", "").strip()

    elif "[ACTION: MOTOR_OFF]" in reply_text:
        send_mqtt_command("OFF")
        reply_text = reply_text.replace("[ACTION: MOTOR_OFF]", "").strip()

    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
