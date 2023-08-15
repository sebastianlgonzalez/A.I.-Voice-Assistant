#Libraries used
import uuid
import secrets
import datetime
import re
import json
import asyncio
import websockets
import requests

import RPi.GPIO as GPIO
import speech_recognition
import emoji
import pyttsx3

# LED pins
LED_1 = 21 # LED pin that indicates that the program is listening 
LED_2 = 18 # LED pin that indicates that the program heard
LED_3 = 19 # LED pin that indicates that the program is processing/speaking
LED_ERR = 20 #LED pin that indicates whether or not an error has a occurred

GPIO.setwarnings (False) # Disables warnings for GPIO
GPIO.setmode (GPIO.BCM) # Set the GPIO mode to use the BCM numbering scheme

# Setup GPIO pins
GPIO.setup (LED_1, GPIO.OUT)
GPIO.setup (LED_2, GPIO.OUT)
GPIO.setup (LED_3, GPIO.OUT)
GPIO.setup (LED_ERR, GPIO.OUT)

# Function to create a conversation with Bing Chat
async def create_conversation():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"} # Header containing User-Agent key and value neccessary for proper response
    response = requests.get("https://www.bing.com/turing/conversation/create", headers=headers) # Make an HTTP request to Bing Chat API to create a conversation

    # Check if the response is successful
    if response.ok:
        data = response.json() # Turn response into JSON for analyzing
        if (data["result"]["value"] == "Success" and data['conversationSignature']): # Acquire neccessary conversation details 
            conversationId = data['conversationId']
            clientId = data['clientId']
            conversationSignature = data['conversationSignature']
            print("Successfully created conversation.")
    else:
        response.raise_for_status() # Throws HTTPError exception if error occurs in process
    
    return {"conversationId":conversationId, "clientId":clientId, "conversationSignature":conversationSignature} # Return neccessary details as a dictionary

# Function to send a request to Bing Chat
async def send_request(question):
    # Generate unique information for message request
    # Randomly generating using the uuid and secrets library works with the request
    requestId = uuid.uuid4()
    traceId = secrets.token_hex(32)
    formattedTime = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z') #This particular formatting for the current timestamp is also required
    # This was figured out using trial and error and viewing Bing Chat's inspect element network tab

    data = await create_conversation() #Awaits for the create_conversation function to get conversation details
        
    async with websockets.connect("wss://sydney.bing.com/sydney/ChatHub") as ws: # Uses the websockets library to connect to Bing Chat
        # This was also discovered by viewing Bing Chat's inspect element network tab 
        await ws.send('{"protocol":"json","version":1}') # Sends a fixed packet neccesary to use the websocket
        print("Sending packet 1")
        await ws.send('{"type":6}') # Sends another fixed packet neccesary to use the websocket
        print("Sending packet 2")
        # Prepare the message request to be sent to Bing Chat with all the data that was collected before this point
        messageRequest = {
            "arguments" : [
                {
                    "source":"cib",
                    "optionsSets":["nlu_direct_response_filter","deepleo","disable_emoji_spoken_text","responsible_ai_policy_235","enablemm","enuaug","dagslnv1","dv3sugg","galileo","saharagenconv5"],
                    "allowedMessageTypes":["ActionRequest","Chat","InternalSearchQuery","InternalSearchResult"],
                    "sliceIds":[],
                    "traceId": traceId,
                    "isStartOfSession":True,
                    "requestId": str(requestId),
                    "message": {
                        "locale":"en-US",
                        "market":"en-US",
                        "region":"US",
                        "timestamp": formattedTime,
                        "author":"user",
                        "inputMethod":"Keyboard",
                        "messageType":"SearchQuery",
                        "text": question
                    },
                    "conversationSignature" : data['conversationSignature'],
                    "participant":{"id": data["clientId"]},
                    "conversationId":data["conversationId"]
                }
            ],
            "invocationId": "2",
            "target" : "chat",
            "type": 4
        }

        await ws.send(json.dumps(messageRequest) + '') # Send the message request to Bing Chat
        print("Sending packet 3")
        # Continually loops until responses from websocket stop
        while (True):
            print("Thinking...")
            
            # Bing Chat sends response in a weird way
            # It sends packets building up to the complete message, like "h" -> "he" -> "hel" -> "hell" -> "hello"
            GPIO.output(LED_2, False) # Turns off heard LED 
            GPIO.output(LED_3, True) # Turns on thinking LED as it is now thinking
            
            # Receive data from the WebSocket
            data = await asyncio.wait_for(ws.recv(), timeout=30) # Throws Exception if data is not received for longer than 30 seconds
            data = data.split('') # Separates data from the termination character
            
            dict = json.loads(data[0]) # Loads JSON for analyzing
            
            # Make sure that the packet from the websocket is the final packet containing the full message
            if (dict.get('type') == 2): # The final packet contains a key of type with a value of 2
                for message in dict['item']['messages']: # Bing Chat also separates its responses into images, links, and other types of responses
                    if 'text' in message and 'messageType' not in message: # By performing these checks, we can obtain the text response
                        return message['text'] #Returns the message if it exists

async def main():
    tts = pyttsx3.init() # Initializes the text-to-speech library object
    recognizer = speech_recognition.Recognizer() # Initializes the speech recognition recongizer object
    retry = 0 # Initializes retry counter to 0
    while True:
        # Turns off all LEDs to start up
        GPIO.output(LED_1, False)
        GPIO.output(LED_2, False)
        GPIO.output(LED_3, False)
        GPIO.output(LED_ERR, False)
        with speech_recognition.Microphone() as mic: # Acquires the microphone that is plugged in 
            recognizer.adjust_for_ambient_noise(mic,duration=0.2) # Adjusts the microphone for ambient noise
            # Tries to become accustom to any ambient noise in 0.2 seconds
            print("Listening...")
            GPIO.output(LED_1, True) #Turns first LED on as it is now listening 
            try:
                
                try: # Tries to listen for words
                    audio = recognizer.listen(mic)
                    text = recognizer.recognize_google(audio)
                    text = text.lower() # If the words are recognized, they are put in lowercase for handling
                except Exception: # If words can't be recognized and exception is thrown
                    text = "" # Just set the interpreted words to nothing

                if text.startswith("bing"): # Checks if message begins with the word bing
                        
                        GPIO.output(LED_1, False) # Turns first LED off since it is no longer listening 
                
                        print(f"Heard: {text}")
                        
                        for i in range(0, 1): # A brief wait interval
                            GPIO.output(LED_2, True) # Before turning on the second LED
                        
                        response = await send_request(text) # Sends request to Bing Chat
                        
                        response = re.sub(r'\[\^(\d+)\^\]', '', response) # Removes any Markdown language links that might be present in response
                        response = emoji.replace_emoji(response, replace='') # Removes any emojis that might be present in the response
                        response = response.replace("*", "") # Removes any asteriks that might be present in the response (The text-to-speech voice sometimes pronounces asteriks when reading one)
                        print(response)
                        tts.say(response) # Say the response using text-to-speech library
                        tts.runAndWait() # Wait for response to end
                        retry = 0 # Set retry to 0 since execution was successful
                        
            except Exception as e2: # If any exception is caught throughout the program
                if retry < 3: # And retry is less than three
                    retry += 1 # Then increment retry
                    print(f"Error occurred: {str(e2)} x{retry}") # And retry the loop
                else: # If retry is larger than 3
                    tts = pyttsx3.init() # Reinitialize everything
                    recognizer = speech_recognition.Recognizer()
                    
                    GPIO.output(LED_ERR, True) # Turn error LED on
                    
                    print(f"Error occurred: {str(e2)}. Reinitializing...")
                    tts.say("Sorry, can you repeat that?") # Say this message
                    tts.runAndWait() # Wait until execution
                    
                    GPIO.output(LED_ERR, False) # Turn off error LED
                    # And try to intercept a prompt again
                
if __name__ == "__main__": # On code execution
    try:
        asyncio.run(main()) # Run main
    except SystemExit:
        GPIO.cleanup() # Cleans GPIO on system exit

