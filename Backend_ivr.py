from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
import time
import logging

app = FastAPI(title="AI-Enabled Conversational IVR Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------
#                 LANGUAGE VOICE MESSAGES
# ---------------------------------------------------------

LANG = {
    "en": {
        "welcome": "Welcome to the Indian Railway Smart Voice System.",
        "menu": "You can say: where is my train, seat availability, book ticket, cancel ticket, refund status, train status, or station enquiry.",
        "ask_train_number": "Please enter your 5 digit train number.",
        "train_location": "Your train number {num} is currently at Pune Junction.",
        "seat_available": "Seats are available for train number {num}.",
        "ticket_booked": "Your ticket for train number {num} has been booked successfully.",
        "ticket_cancelled": "Your ticket with P N R number {num} has been cancelled successfully.",
        "refund_status": "The refund for P N R number {num} is being processed.",
        "invalid": "I did not understand. Please try again.",
        "goodbye": "Thank you for using the Indian Railway Smart Voice System."
    },
    "hi": {
        "welcome": "भारतीय रेलवे स्मार्ट वॉइस सिस्टम में आपका स्वागत है।",
        "menu": "आप कह सकते हैं: मेरी ट्रेन कहाँ है, सीट उपलब्धता, टिकट बुक करो, टिकट रद्द करो, रिफंड स्टेटस, ट्रेन स्टेटस या स्टेशन जानकारी।",
        "ask_train_number": "कृपया अपना पाँच अंकों का ट्रेन नंबर दर्ज करें।",
        "train_location": "आपकी ट्रेन नंबर {num} इस समय पुणे जंक्शन पर है।",
        "seat_available": "ट्रेन नंबर {num} के लिए सीट उपलब्ध हैं।",
        "ticket_booked": "आपका टिकट ट्रेन नंबर {num} के लिए सफलतापूर्वक बुक हो गया है।",
        "ticket_cancelled": "पी एन आर नंबर {num} वाला आपका टिकट रद्द कर दिया गया है।",
        "refund_status": "पी एन आर नंबर {num} का रिफंड प्रोसेस में है।",
        "invalid": "मैं समझ नहीं पाया। कृपया दोबारा बोलें।",
        "goodbye": "भारतीय रेलवे स्मार्ट वॉइस सिस्टम का उपयोग करने के लिए धन्यवाद।"
    },
    "mr": {
        "welcome": "भारतीय रेल्वे स्मार्ट व्हॉइस सिस्टममध्ये आपले स्वागत आहे.",
        "menu": "आपण असे बोलू शकता: माझी ट्रेन कुठे आहे, आसन उपलब्धता, तिकीट बुक करा, तिकीट रद्द करा, परतावा स्थिती, ट्रेन स्थिती किंवा स्टेशन माहिती.",
        "ask_train_number": "कृपया पाच अंकी गाडी क्रमांक टाका.",
        "train_location": "आपली गाडी क्रमांक {num} सध्या पुणे जंक्शनवर आहे.",
        "seat_available": "गाडी क्रमांक {num} साठी आसन उपलब्ध आहेत.",
        "ticket_booked": "गाडी क्रमांक {num} साठी आपले तिकीट यशस्वीरीत्या बुक केले गेले आहे.",
        "ticket_cancelled": "पी एन आर क्रमांक {num} चे तिकीट रद्द करण्यात आले आहे.",
        "refund_status": "पी एन आर क्रमांक {num} चा परतावा प्रक्रियेत आहे.",
        "invalid": "मला समजले नाही. कृपया पुन्हा बोला.",
        "goodbye": "भारतीय रेल्वे स्मार्ट व्हॉइस सिस्टम वापरल्याबद्दल धन्यवाद."
    }
}

# ---------------------------------------------------------
#                 DETECT INTENT
# ---------------------------------------------------------

def detect_intent(text):
    text = text.lower()

    if "where is my train" in text or "train location" in text or "track my train" in text:
        return "train_location"

    if "seat" in text or "availability" in text:
        return "seat_availability"

    if "book" in text and "ticket" in text:
        return "book_ticket"

    if "cancel" in text and "ticket" in text:
        return "cancel_ticket"

    if "refund" in text:
        return "refund_status"

    if "train status" in text:
        return "train_status"

    return "unknown"


# ---------------------------------------------------------
#        STEP 1 — LANGUAGE SELECTION (Speech + DTMF)
# ---------------------------------------------------------

@app.api_route("/ivr", methods=["GET", "POST"])
async def ivr_language():
    vr = VoiceResponse()
    gather = vr.gather(
        input="speech dtmf",
        num_digits=1,
        action="/ivr/set-language",
        method="POST",
        timeout=6
    )

    gather.say("Please select your language. For English press 1 or say English. For Hindi press 2 or say Hindi. For Marathi press 3 or say Marathi.", voice="alice")

    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
#    Store Language + Go to next conversational menu
# ---------------------------------------------------------

@app.post("/ivr/set-language")
async def set_language(request: Request):
    form = await request.form()
    digit = form.get("Digits")
    speech = form.get("SpeechResult", "").lower()

    lang = "en"

    if digit == "1" or "english" in speech:
        lang = "en"
    elif digit == "2" or "hindi" in speech:
        lang = "hi"
    elif digit == "3" or "marathi" in speech:
        lang = "mr"

    vr = VoiceResponse()

    # Store language in redirect URL
    vr.redirect(f"/ivr/main-menu?lang={lang}")

    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
#               MAIN MENU (Based on Language)
# ---------------------------------------------------------

@app.get("/ivr/main-menu")
async def main_menu(lang: str = "en"):
    vr = VoiceResponse()
    gather = vr.gather(
        input="speech",
        action=f"/ivr/handle-speech?lang={lang}",
        method="POST",
        timeout=6
    )

    gather.say(LANG[lang]["welcome"], voice="alice")
    gather.say(LANG[lang]["menu"], voice="alice")

    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
#     Handle Caller Speech After Language Selection
# ---------------------------------------------------------

@app.post("/ivr/handle-speech")
async def handle_speech(request: Request, lang: str = "en"):
    form = await request.form()
    speech = form.get("SpeechResult", "")

    intent = detect_intent(speech)

    vr = VoiceResponse()

    # --------------- Train Location ---------------
    if intent == "train_location":
        gather = vr.gather(
            input="dtmf",
            num_digits=5,
            action=f"/ivr/train-location?lang={lang}",
            method="POST"
        )
        gather.say(LANG[lang]["ask_train_number"], voice="alice")
        return Response(str(vr), media_type="application/xml")

    # --------------- Seat Availability ---------------
    if intent == "seat_availability":
        gather = vr.gather(
            input="dtmf",
            num_digits=5,
            action=f"/ivr/seat?lang={lang}",
            method="POST"
        )
        gather.say(LANG[lang]["ask_train_number"], voice="alice")
        return Response(str(vr), media_type="application/xml")

    # --------------- Book Ticket ---------------
    if intent == "book_ticket":
        gather = vr.gather(
            input="dtmf",
            num_digits=5,
            action=f"/ivr/book?lang={lang}",
            method="POST"
        )
        gather.say(LANG[lang]["ask_train_number"], voice="alice")
        return Response(str(vr), media_type="application/xml")

    # --------------- Cancel Ticket ---------------
    if intent == "cancel_ticket":
        gather = vr.gather(
            input="dtmf",
            num_digits=10,
            action=f"/ivr/cancel?lang={lang}",
            method="POST"
        )
        gather.say("Please enter your PNR number.", voice="alice")
        return Response(str(vr), media_type="application/xml")

    # --------------- Refund Status ---------------
    if intent == "refund_status":
        gather = vr.gather(
            input="dtmf",
            num_digits=10,
            action=f"/ivr/refund?lang={lang}",
            method="POST"
        )
        gather.say("Please enter your PNR number.", voice="alice")
        return Response(str(vr), media_type="application/xml")

    # Unknown
    vr.say(LANG[lang]["invalid"], voice="alice")
    vr.redirect(f"/ivr/main-menu?lang={lang}")
    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
#            Train Location Result
# ---------------------------------------------------------

@app.post("/ivr/train-location")
async def train_location(request: Request, lang: str = "en"):
    form = await request.form()
    num = form.get("Digits")

    vr = VoiceResponse()
    vr.say(LANG[lang]["train_location"].format(num=num), voice="alice")
    vr.say(LANG[lang]["goodbye"], voice="alice")
    vr.hangup()

    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
#            Seat Availability Result
# ---------------------------------------------------------

@app.post("/ivr/seat")
async def seat_result(request: Request, lang: str = "en"):
    form = await request.form()
    num = form.get("Digits")

    vr = VoiceResponse()
    vr.say(LANG[lang]["seat_available"].format(num=num), voice="alice")
    vr.say(LANG[lang]["goodbye"], voice="alice")
    vr.hangup()

    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
#            Book Ticket Result
# ---------------------------------------------------------

@app.post("/ivr/book")
async def book_result(request: Request, lang: str = "en"):
    form = await request.form()
    num = form.get("Digits")

    vr = VoiceResponse()
    vr.say(LANG[lang]["ticket_booked"].format(num=num), voice="alice")
    vr.say(LANG[lang]["goodbye"], voice="alice")
    vr.hangup()

    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
#            Cancel Ticket Result
# ---------------------------------------------------------

@app.post("/ivr/cancel")
async def cancel_result(request: Request, lang: str = "en"):
    form = await request.form()
    num = form.get("Digits")

    vr = VoiceResponse()
    vr.say(LANG[lang]["ticket_cancelled"].format(num=num), voice="alice")
    vr.say(LANG[lang]["goodbye"], voice="alice")
    vr.hangup()

    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
#            Refund Status Result
# ---------------------------------------------------------

@app.post("/ivr/refund")
async def refund_result(request: Request, lang: str = "en"):
    form = await request.form()
    num = form.get("Digits")

    vr = VoiceResponse()
    vr.say(LANG[lang]["refund_status"].format(num=num), voice="alice")
    vr.say(LANG[lang]["goodbye"], voice="alice")
    vr.hangup()

    return Response(str(vr), media_type="application/xml")


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
