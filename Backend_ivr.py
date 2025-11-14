from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
import logging
import time

app = FastAPI(title="AI-Enabled Conversational IVR Modernization Framework")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------
# LANGUAGE SELECTION → MAIN ENTRY
# ---------------------------------------------------------
@app.api_route("/ivr", methods=["GET", "POST"])
async def ivr_language():
    response = VoiceResponse()

    gather = Gather(
        input="dtmf",
        num_digits=1,
        action="/ivr/set-language",
        method="POST"
    )

    gather.say(
        "Press 1 for English. हिंदी के लिए 2 दबाएं. मराठी साठी 3 दाबा.",
        voice="alice",
        language="hi-IN"
    )

    response.append(gather)
    return Response(str(response), media_type="application/xml")


# ---------------------------------------------------------
# STORE LANGUAGE AND GO TO MAIN MENU
# ---------------------------------------------------------
@app.post("/ivr/set-language")
async def set_language(request: Request):
    form = await request.form()
    choice = form.get("Digits")

    response = VoiceResponse()

    if choice == "1":
        lang = "en"
        response.say("You selected English.", voice="alice")
    elif choice == "2":
        lang = "hi"
        response.say("आपने हिंदी चुना है।", voice="alice", language="hi-IN")
    elif choice == "3":
        lang = "mr"
        response.say("आपण मराठी निवडली आहे.", voice="alice", language="mr-IN")
    else:
        response.say("Invalid choice. Returning to main menu.", voice="alice")
        response.redirect("/ivr")
        return Response(str(response), media_type="application/xml")

    response.redirect(f"/ivr/main-menu?lang={lang}")
    return Response(str(response), media_type="application/xml")


# ---------------------------------------------------------
# MAIN MENU BASED ON LANGUAGE
# ---------------------------------------------------------
@app.get("/ivr/main-menu")
async def main_menu(lang: str):
    response = VoiceResponse()

    gather = Gather(input="speech", action=f"/ivr/handle-speech?lang={lang}", method="POST")

    if lang == "en":
        gather.say("Welcome to Indian Railway Smart Voice System. You can say: Where is my train, Ticket booking, Cancel ticket, Refund status, Seat availability.", voice="alice")
    elif lang == "hi":
        gather.say("आप भारतीय रेलवे स्मार्ट वॉइस सिस्टम में स्वागत है। बोलें: मेरी ट्रेन कहाँ है, टिकट बुक करो, टिकट रद्द करो, रिफंड स्टेटस, सीट उपलब्धता।", voice="alice", language="hi-IN")
    elif lang == "mr":
        gather.say("भारतीय रेल्वे स्मार्ट व्हॉइस सिस्टम मध्ये आपले स्वागत आहे. बोला: माझी ट्रेन कुठे आहे, तिकीट बुक करा, तिकीट रद्द करा, रिफंड स्टेटस, सीट उपलब्धता.", voice="alice", language="mr-IN")

    response.append(gather)
    return Response(str(response), media_type="application/xml")


# ---------------------------------------------------------
# INTENT DETECTION
# ---------------------------------------------------------
def detect_intent(text: str):
    text = text.lower()

    if "where is my train" in text or "train location" in text:
        return "train_location"

    if "seat" in text:
        return "seat_availability"

    if "book" in text:
        return "book_ticket"

    if "cancel" in text:
        return "cancel_ticket"

    if "refund" in text:
        return "refund_status"

    return "unknown"


# ---------------------------------------------------------
# HANDLE SPEECH BASED ON LANGUAGE
# ---------------------------------------------------------
@app.post("/ivr/handle-speech")
async def handle_speech(request: Request, lang: str):
    form = await request.form()
    speech = form.get("SpeechResult", "")

    intent = detect_intent(speech)

    response = VoiceResponse()

    # LANGUAGE CONFIG
    voice_cfg = {"voice": "alice"}
    if lang == "hi": voice_cfg["language"] = "hi-IN"
    if lang == "mr": voice_cfg["language"] = "mr-IN"

    # 1️⃣ TRAIN LOCATION
    if intent == "train_location":
        gather = response.gather(
            input="dtmf",
            num_digits=5,
            action=f"/ivr/train-location?lang={lang}",
            method="POST"
        )
        if lang == "en": gather.say("Please enter your train number.", **voice_cfg)
        if lang == "hi": gather.say("कृपया अपनी ट्रेन नंबर दर्ज करें।", **voice_cfg)
        if lang == "mr": gather.say("कृपया आपला ट्रेन क्रमांक प्रविष्ट करा.", **voice_cfg)
        return Response(str(response), media_type="application/xml")

    # 2️⃣ SEAT AVAILABILITY
    if intent == "seat_availability":
        gather = response.gather(
            input="dtmf",
            num_digits=5,
            action=f"/ivr/seat-availability?lang={lang}",
            method="POST"
        )
        if lang == "en": gather.say("Enter your train number for seat availability.", **voice_cfg)
        if lang == "hi": gather.say("सीट उपलब्धता के लिए कृपया ट्रेन नंबर दर्ज करें।", **voice_cfg)
        if lang == "mr": gather.say("सीट उपलब्धतेसाठी ट्रेन क्रमांक प्रविष्ट करा.", **voice_cfg)
        return Response(str(response), media_type="application/xml")

    # OTHER INTENTS CAN BE ADDED...

    # UNKNOWN
    if lang == "en": response.say("Sorry, I did not understand.", **voice_cfg)
    if lang == "hi": response.say("क्षमा करें, मैं समझ नहीं पाया।", **voice_cfg)
    if lang == "mr": response.say("माफ करा, मला समजले नाही.", **voice_cfg)

    response.redirect(f"/ivr/main-menu?lang={lang}")
    return Response(str(response), media_type="application/xml")


# ---------------------------------------------------------
# TRAIN LOCATION RESULT
# ---------------------------------------------------------
@app.post("/ivr/train-location")
async def train_location(request: Request, lang: str):
    form = await request.form()
    train_no = form.get("Digits")

    response = VoiceResponse()
    voice_cfg = {"voice": "alice"}
    if lang == "hi": voice_cfg["language"] = "hi-IN"
    if lang == "mr": voice_cfg["language"] = "mr-IN"

    if lang == "en": response.say(f"Train {train_no} is currently at Pune Junction.", **voice_cfg)
    if lang == "hi": response.say(f"ट्रेन {train_no} इस समय पुणे जंक्शन पर है।", **voice_cfg)
    if lang == "mr": response.say(f"ट्रेन {train_no} सध्या पुणे जंक्शनवर आहे.", **voice_cfg)

    response.hangup()
    return Response(str(response), media_type="application/xml")


# ---------------------------------------------------------
# SEAT AVAILABILITY RESULT
# ---------------------------------------------------------
@app.post("/ivr/seat-availability")
async def seat_availability(request: Request, lang: str):
    form = await request.form()
    train_no = form.get("Digits")

    response = VoiceResponse()
    voice_cfg = {"voice": "alice"}
    if lang == "hi": voice_cfg["language"] = "hi-IN"
    if lang == "mr": voice_cfg["language"] = "mr-IN"

    if lang == "en": response.say(f"Seats are available for train number {train_no}.", **voice_cfg)
    if lang == "hi": response.say(f"ट्रेन नंबर {train_no} के लिए सीट उपलब्ध हैं।", **voice_cfg)
    if lang == "mr": response.say(f"ट्रेन क्रमांक {train_no} साठी सीट उपलब्ध आहेत.", **voice_cfg)

    response.hangup()
    return Response(str(response), media_type="application/xml")



# ---------------------------------------------------------
# HEALTH + METRICS
# ---------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    return {"uptime_seconds": round(time.process_time(), 2)}

@app.get("/")
async def root():
    return {"message": "AI Enabled Conversational IVR (English + Hindi + Marathi) 🚀"}

