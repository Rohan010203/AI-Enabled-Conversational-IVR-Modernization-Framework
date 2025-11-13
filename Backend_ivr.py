from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
import time
import logging

app = FastAPI(title="AI-Enabled Conversational IVR Backend")

# Enable CORS for testing via browser or API tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

# -----------------------
# 📞 Milestone 2: DTMF IVR
# -----------------------

@app.api_route("/ivr", methods=["GET", "POST"])
async def ivr_entry():
    """Main IVR greeting and menu"""
    twiml = """
    <Response>
        <Say voice="alice">Hello, welcome to Indian Railway Booking System.</Say>
        <Say>
            Press 1 for Train Availability.
            Press 2 for PNR Status.
            Press 3 to talk to a Customer Agent.
            Press 4 for Ticket Cancellation.
            Press 5 for Refund Status.
            Press 6 for Train Running Status.
            Press 7 for Seat Availability.
            Press 8 for Station Enquiry.
            Press 9 to hear the Main Menu again.
        </Say>
        <Gather input="dtmf" timeout="5" numDigits="1" action="/ivr/handle-key" method="POST" />
    </Response>
    """
    return Response(content=twiml.strip(), media_type="application/xml")


@app.post("/ivr/handle-key")
async def handle_key(request: Request):
    """Handles numeric keypad input"""
    form = await request.form()
    digit_pressed = form.get("Digits")
    logging.info(f"Digit pressed: {digit_pressed}")

    messages = {
        "1": "You selected Train Availability. Please visit Indian Railways dot gov dot in for live schedules.",
        "2": "You selected PNR Status. Please enter your ten digit PNR on the website or app.",
        "3": "Connecting you to the nearest Railway customer agent. Please wait.",
        "4": "You selected Ticket Cancellation. Please log in to your IRCTC account to cancel tickets.",
        "5": "You selected Refund Status. Refunds are processed within seven working days.",
        "6": "You selected Train Running Status. Please check live updates on Indian Railways dot gov dot in.",
        "7": "You selected Seat Availability. Please check the availability chart on the IRCTC website.",
        "8": "You selected Station Enquiry. Please contact the station help desk for more information.",
    }

    if digit_pressed == "9":
        twiml = "<Response><Redirect>/ivr</Redirect></Response>"
        return Response(content=twiml, media_type="application/xml")

    msg = messages.get(digit_pressed, "Invalid choice. Please press a number between 1 and 9 next time.")

    twiml = f"<Response><Say voice='alice'>{msg}</Say><Hangup/></Response>"
    return Response(content=twiml, media_type="application/xml")


# ----------------------------
# 🗣️ Milestone 3: Speech IVR
# ----------------------------

def book_ticket(): return "Your train ticket has been booked successfully."
def cancel_ticket(): return "Your ticket has been cancelled successfully."
def check_refund(): return "Your refund is being processed and will be credited soon."
def train_status(): return "The train is running on time as per schedule."
def seat_availability(): return "Seats are available for your selected route."
def station_enquiry(): return "Please mention the station name for more information."
def unknown_intent(): return "Sorry, I didn’t understand your request. Please try again."

def detect_intent(speech_text: str):
    text = speech_text.lower()
    if "book" in text and "ticket" in text:
        return "book"
    elif "cancel" in text:
        return "cancel"
    elif "refund" in text:
        return "refund"
    elif "train" in text and "status" in text:
        return "train_status"
    elif "seat" in text or "availability" in text:
        return "seat_availability"
    elif "station" in text or "enquiry" in text:
        return "station_enquiry"
    else:
        return "unknown"


@app.api_route("/ivr/speech", methods=["GET", "POST"])
async def ivr_speech_entry():
    """Speech IVR entry point"""
    response = VoiceResponse()
    gather = Gather(input="speech", action="/ivr/handle-speech", method="POST", timeout=6)
    gather.say(
        "Welcome to the Indian Railway Booking System. You can say book a ticket, cancel my booking, "
        "check refund, train running status, seat availability, or station enquiry."
    )
    response.append(gather)
    return Response(content=str(response), media_type="application/xml")


@app.post("/ivr/handle-speech")
async def handle_speech(request: Request):
    """Handles speech-to-text commands"""
    form = await request.form()
    speech_text = form.get("SpeechResult")
    logging.info(f"Speech recognized: {speech_text}")

    response = VoiceResponse()

    if not speech_text:
        response.say("Sorry, I didn't hear you. Please try again.", voice="alice")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    intent = detect_intent(speech_text)
    intent_map = {
        "book": book_ticket,
        "cancel": cancel_ticket,
        "refund": check_refund,
        "train_status": train_status,
        "seat_availability": seat_availability,
        "station_enquiry": station_enquiry,
    }
    message = intent_map.get(intent, unknown_intent)()
    response.say(message, voice="alice")
    response.hangup()

    return Response(content=str(response), media_type="application/xml")


# --------------------------------------
# 🧠 Milestone 4: Health, Metrics & Tests
# --------------------------------------

@app.get("/health")
async def health_check():
    """Check if backend is running"""
    return JSONResponse({"status": "healthy", "message": "IVR backend is running fine."})


@app.get("/metrics")
async def metrics():
    """Basic performance metrics"""
    uptime = round(time.process_time(), 2)
    return JSONResponse({
        "system": "AI-Enabled IVR",
        "uptime_seconds": uptime,
        "status": "operational"
    })


@app.api_route("/test/ivr", methods=["GET", "POST"])
async def test_ivr_scenarios(request: Request):
    """Simulate IVR scenarios for testing"""
    if request.method == "GET":
        return JSONResponse({
            "message": "Send a POST request with JSON { 'input': 'book ticket' } to test intent detection."
        })
    data = await request.json()
    test_input = data.get("input", "").lower()
    intent = detect_intent(test_input)
    logging.info(f"Test -> Input: {test_input}, Intent: {intent}")
    return JSONResponse({"input": test_input, "detected_intent": intent})


@app.get("/")
async def home():
    """Root endpoint for Render"""
    return JSONResponse({
        "message": "Welcome to the AI-Enabled Conversational IVR Modernization Framework 🚀",
        "status": "running",
        "available_endpoints": [
            "/ivr",
            "/ivr/speech",
            "/health",
            "/metrics",
            "/test/ivr"
        ]
    })
