from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse

app = FastAPI()

@app.get("/")
def home():
    return {"message": "AI IVR System is running ✅"}

# Step 1: Entry point for the IVR
@app.post("/ivr")
async def ivr_start(request: Request):
    response = VoiceResponse()
    response.say("Welcome to the Railway Inquiry System. Please enter your P N R number followed by the pound key.")
    response.gather(num_digits=6, action="/handle-key", method="POST")
    return Response(content=str(response), media_type="application/xml")

# Step 2: Handle user input (like PNR)
@app.post("/handle-key")
async def handle_key(request: Request):
    form = await request.form()
    digits = form.get("Digits")

    response = VoiceResponse()
    if digits:
        # Example logic: Fake database check
        response.say(f"Your entered P N R number is {digits}. Your status is Waiting 25.")
    else:
        response.say("Sorry, no input detected. Please try again.")
        response.redirect("/ivr")

    return Response(content=str(response), media_type="application/xml")

# Step 3: Test endpoint for GET request (manual testing)
@app.get("/test/pnr")
def test_pnr(pnr: str):
    return {"PNR": pnr, "Status": "Waiting 25"}
