from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
import time
import logging

app = FastAPI(title="AI-Enabled Conversational IVR Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

# -----------------------
# 📞 Milestone 2 & 3: Conversational + DTMF IVR
# -----------------------

@app.api_route("/ivr", methods=["GET", "POST"])
async def ivr_entry():
    """Main IVR greeting and menu"""
    twiml = """
    <Response>
        <Say voice="alice">Welcome to Indian Railway Booking System.</Say>
        <Pause length="1"/>
        <Say>
            Press 1 for Train Booking.
            Press 2 for PNR Status.
            Press 3 to talk to Customer Agent.
        </Say>
        <Gather input="dtmf" timeout="5" numDigits="1" action="/ivr/handle-key" method="POST" />
    </Response>
    """
    return Response(content=twiml.strip(), media_type="application/xml")


@app.post("/ivr/handle-key")
async def handle_key(request: Request):
    """Handles numeric keypad input"""
    form = await request.form()
    digit = form.get("Digits")
    logging.info(f"Digit pressed: {digit}")

    response = VoiceResponse()

    if digit == "1":
        response.say("You selected Train Booking. Please say your destination city after the beep.", voice="alice")
        gather = Gather(input="speech", action="/ivr/handle-booking", method="POST", timeout=6)
        response.append(gather)

    elif digit == "2":
        response.say("You selected P N R Status. Please enter your ten digit P N R number.", voice="alice")
        gather = Gather(input="dtmf", numDigits="10", action="/ivr/pnr-status", method="POST", timeout=10)
        response.append(gather)

    elif digit == "3":
        response.say("Please wait while we connect you to a customer agent.", voice="alice")
        response.dial("+911234567890")

    else:
        response.say("Invalid option. Please press 1 for booking or 2 for PNR status.", voice="alice")
        response.redirect("/ivr")

    return Response(content=str(response), media_type="application/xml")


# -------------------------
# 🎟️ PNR Status Flow
# -------------------------
@app.post("/ivr/pnr-status")
async def handle_pnr_status(request: Request):
    """Handle entered PNR number"""
    form = await request.form()
    pnr = form.get("Digits")

    response = VoiceResponse()

    if not pnr or len(pnr) != 10:
        response.say("Invalid P N R number. Please enter a ten digit number.", voice="alice")
        response.redirect("/ivr")
        return Response(content=str(response), media_type="application/xml")

    # Mock PNR status (replace with API integration if available)
    status_map = {
        "1234567890": "Your booking is confirmed. Train number 12049 is on time.",
        "1111111111": "Your P N R is waitlisted. Please check after some time."
    }

    message = status_map.get(pnr, f"P N R {pnr} is confirmed. Your train is on schedule.")
    response.say(message, voice="alice")
    response.hangup()
    return Response(content=str(response), media_type="application/xml")


# -------------------------
# 🚉 Booking Speech Flow
# -------------------------
@app.post("/ivr/handle-booking")
async def handle_booking(request: Request):
    """Handle speech for booking"""
    form = await request.form()
    speech_text = form.get("SpeechResult", "")
    logging.info(f"Booking speech detected: {speech_text}")

    response = VoiceResponse()
    if not speech_text:
        response.say("Sorry, I did not hear your destination. Please try again.", voice="alice")
        response.redirect("/ivr")
        return Response(content=str(response), media_type="application/xml")

    destination = speech_text.strip().capitalize()
    response.say(f"Booking train ticket to {destination}. Your ticket is confirmed. Have a safe journey!", voice="alice")
    response.hangup()
    return Response(content=str(response), media_type="application/xml")


# --------------------------------------
# 🧠 Health & Test Endpoints
# --------------------------------------

@app.get("/health")
async def health_check():
    """Health check"""
    return JSONResponse({"status": "healthy", "message": "IVR backend is running fine."})


@app.api_route("/test/ivr", methods=["GET", "POST"])
async def test_ivr_scenarios(request: Request):
    """Simulate IVR scenarios for testing"""
    if request.method == "GET":
        return JSONResponse({
            "message": "Send POST { 'input': 'book ticket to delhi' } to test intent flow."
        })
    data = await request.json()
    test_input = data.get("input", "").lower()
    if "pnr" in test_input:
        return JSONResponse({"response": "Please enter your 10-digit PNR number."})
    elif "book" in test_input:
        return JSONResponse({"response": "Please say your destination city."})
    else:
        return JSONResponse({"response": "Sorry, I didn’t understand your request."})


@app.get("/")
async def home():
    """Root endpoint"""
    return JSONResponse({
        "message": "Welcome to AI-Enabled Conversational IVR 🚀",
        "status": "running",
        "endpoints": ["/ivr", "/health", "/test/ivr"]
    })
