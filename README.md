# A.I. Voice Assistant

Created for EEL4709 Computer Design course in Florida International University.

The main objective of the project was to create an always online voice assistant on a Raspberry Pi Model 4, like Google Home or Amazon Alexa, capable of answering questions and responding to user voice input. The focus was on providing users with a voice-activated interface to interact with the Bing Chat bot that is accessible with the Microsoft Edge browser effectively. 

Components Used:
Headphones, USB Microphone, LEDs, 220 Ohm Resistors, Raspberry Pi

The Raspberry Pi Model 4 was connected to a breadboard with 4 LEDs to display the "thinking" process of the A.I. Four LEDs are strategically assigned to signify distinct stages: the first LED illuminates when the program is actively listening, the second lights up upon successful recognition of a command, the third denotes the AI's thinking or speaking phase, while the fourth acts as an error indicator, signaling any encountered issues.

![image](https://github.com/sebastianlgonzalez/A.I.-Voice-Assistant/assets/140292588/c96a2f49-2bf1-4d71-bc5a-6e5d9f6af576)

A microphone and headset are plugged into the Raspberry Pi Model 4. via USB to handle the user input and output (the headset in the picture below is wireless).
![image](https://github.com/sebastianlgonzalez/A.I.-Voice-Assistant/assets/140292588/db17980c-c32c-4f6d-aafd-ab99bf5e025d)

The code initializes GPIO pins for LED management, defines crucial functions like "create_conversation()" and "send_request(question)" for Bing Chat interaction via HTTP requests and WebSocket communication. An overarching loop captures voice commands using speech recognition, manages the interaction flow, communicates with Bing Chat, tracks progress with LED indicators, and converts retrieved responses into audible outputs via text-to-speech using pyttsx3. This cohesive integration streamlines interaction between the Raspberry Pi and Bing Chat, facilitating a seamless conversational experience.

More info:
