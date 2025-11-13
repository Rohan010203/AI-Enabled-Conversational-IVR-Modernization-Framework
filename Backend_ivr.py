from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse

app = FastAPI()

# ✅ Step 0: Root route (health + POST handler)
@app.get("/")
def home():
    return {"message": "AI IVR System is running ✅"}

@app.post("/")
def home_post():
    return {"message": "POST request received successfully"}

# ✅ Step 1: Entry point for IVR (GET + POST)
@app.api_route("/ivr", methods=["GET", "POST"])
async def ivr_start(request: Request):
    response = VoiceResponse()
    response.say(
        "Welcome to the Railway Inquiry System. "
        "Please enter your P N R number followed by the pound key."
    )
    response.gather(num_digits=6, action="/handle-key", method="POST")
    return Response(content=str(response), media_type="application/xml")

# ✅ Step 2: Handle DTMF input (PNR digits)
@app.post("/handle-key")
async def handle_key(request: Request):
    form = await request.form()
    digits = form.get("Digits")

    response = VoiceResponse()
    if digits:
        # Example logic: Mock status check
        response.say(f"Your entered P N R number is {digits}. Your current status is Waiting 25.")
        response.say("Thank you for calling Indian Railways. Have a nice day!")
        response.hangup()
    else:
        response.say("No input detected. Redirecting you to the main menu.")
        response.redirect("/ivr")

    return Response(content=str(response), media_type="application/xml")

# ✅ Step 3: Manual test endpoint (GET)
@app.get("/test/pnr")
def test_pnr(pnr: str):
    return {"PNR": pnr, "Status": "Waiting 25"}

# ✅ Step 4: Handle favicon (to avoid 404 logs)
@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)
