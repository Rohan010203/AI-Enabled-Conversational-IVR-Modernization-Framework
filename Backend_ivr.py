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


# ==========================================================
# 1️⃣ MAIN IVR ENTRY (DTMF + SPEECH)
# ==========================================================
@app.api_route("/ivr", methods=["GET", "POST"])
async def ivr_entry():
    """Main IVR menu — welcomes and allows both DTMF and speech"""

    response = VoiceResponse()

    gather = Gather(
        input="speech dtmf",
        timeout=5,
        num_digits=1,
        action="/ivr/router",
        method="POST"
    )

    gather.say(
        """
        Welcome to Indian Railway Booking System.

        Say or Press:
        1 for Train Availability.
        2 for P N R Status.
        3 for Customer Agent.
        4 for Ticket Cancellation.
        5 for Refund Status.
        6 for Train Running Status.
        7 for Seat Availability.
        8 for Station Enquiry.
        9 for Main Menu again.
        """,
        voice="alice"
    )

    response.append(gather)

    return Response(str(response), media_type="application/xml")


# ==========================================================
# 2️⃣ ROUTING BASED ON USER INPUT (Speech or DTMF)
# ==========================================================
@app.post("/ivr/router")
async def ivr_router(request: Request):

    form = await request.form()
    digit = form.get("Digits")          # DTMF
    speech = form.get("SpeechResult")   # Speech

    logging.info(f"DTMF: {digit}, SPEECH: {speech}")

    # DTMF routing
    if digit:
        return await route_dtmf(digit)

    # Speech routing
    if speech:
        return await route_speech(speech)

    # No input fallback
    vr = VoiceResponse()
    vr.say("I did not hear anything. Redirecting to main menu.")
    vr.redirect("/ivr")
    return Response(str(vr), media_type="application/xml")


# ==========================================================
# 3️⃣ DTMF HANDLER
# ==========================================================
async def route_dtmf(digit):
    messages = {
        "1": "Train Availability can be checked on IRCTC website.",
        "2": "Please enter your 10 digit PNR on IRCTC App.",
        "3": "Connecting you to a Railway customer agent.",
        "4": "Login to IRCTC account to cancel tickets.",
        "5": "Refund is processed within 7 working days.",
        "6": "Train is running on time.",
        "7": "Seats are available for your selected route.",
        "8": "Please say the station name for enquiry.",
    }

    vr = VoiceResponse()

    if digit == "9":
        vr.redirect("/ivr")
        return Response(str(vr), media_type="application/xml")

    msg = messages.get(digit, "Invalid choice. Please press a number between 1 and 9.")

    vr.say(msg, voice="alice")
    vr.hangup()

    return Response(str(vr), media_type="application/xml")


# ==========================================================
# 4️⃣ SPEECH HANDLER (Conversational IVR)
# ==========================================================
def detect_intent(speech: str):
    text = speech.lower()
    if "book" in text:
        return "book"
    if "cancel" in text:
        return "cancel"
    if "refund" in text:
        return "refund"
    if "train" in text and "status" in text:
        return "train_status"
    if "seat" in text:
        return "seat_availability"
    if "station" in text:
        return "station_enquiry"
    return "unknown"


async def route_speech(speech_text):
    intent = detect_intent(speech_text)

    vr = VoiceResponse()

    responses = {
        "book": "Your ticket has been booked successfully.",
        "cancel": "Your booking has been cancelled.",
        "refund": "Your refund is under processing.",
        "train_status": "The train is currently running on time.",
        "seat_availability": "Seats are available for your route.",
        "station_enquiry": "Please mention the station name for enquiry.",
    }

    message = responses.get(intent, "Sorry, I did not understand. Please try again.")

    vr.say(message, voice="alice")
    vr.hangup()

    return Response(str(vr), media_type="application/xml")


# ==========================================================
# 5️⃣ HEALTH & TESTS
# ==========================================================
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "IVR running fine"}

@app.get("/")
async def home():
    return {
        "message": "AI Conversational IVR Framework Running 🚀",
        "routes": ["/ivr", "/health"],
    }
