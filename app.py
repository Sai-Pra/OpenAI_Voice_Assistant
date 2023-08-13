import os
import openai
import speech_recognition
import time
import pyaudio
import wave
from flask import Flask, redirect, render_template, request, url_for, request, make_response
from werkzeug.wrappers import Request, Response
import pyttsx3
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 512
RECORD_SECONDS = 3
WAVE_OUTPUT_FILENAME = "recordedFile.wav"
device_index = 0


app = Flask(__name__)
app.debug = True
app.run(host='0.0.0.0',port=5000)
openai.api_key = os.getenv("OPENAI_API_KEY")

UserVoiceInput_converted_to_Text = "Respond with 'No question entered'"
UserVoiceRecognizer = speech_recognition.Recognizer()
question = ""
responseText = ""

#if request.form['submit_button'] == 'Do Something':

@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        if request.form['submit'] == 'Adjust for Ambient Sounds':
            try:
                with speech_recognition.Microphone() as UserVoiceInputSource:
                    UserVoiceRecognizer.adjust_for_ambient_noise(UserVoiceInputSource, duration=1)
                    print("LOAD AMBIENCE")
                    return render_template("listen_voice.html", waitImg='true')
            except KeyboardInterrupt:
                #print('A KeyboardInterrupt encountered; Terminating the Program !!!')
                exit(0)
            except speech_recognition.UnknownValueError:
                print("No User Voice detected OR unintelligible noises detected OR the recognized audio cannot be matched to text !!!")
        elif request.form['submit'] == 'Type Question Manually':
            return render_template("manual_question.html", waitImg='true')
    return render_template("index.html", waitImg='true') 


@app.route("/listen", methods=("GET", "POST"))
def listen():
    if request.method == "POST":
        print("Im inside listen")
        question = wav_record()
        print(question)

        #question = UserVoiceInput_converted_to_Text
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=generate_prompt(question),
            temperature=0.6,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        responseText = response.choices[0].text
        print(responseText)
    return render_template("respond.html", result=responseText)

@app.route("/manual", methods=("GET", "POST"))
def manual_type():
    if request.method == "POST":
        question = request.form["Your Question"]
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=generate_prompt(question),
            temperature=0.6,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        responseText = response.choices[0].text
        print(responseText)
    return render_template("respond.html", result=responseText)

@app.route("/respond", methods =("GET","POST"))
def respond():
    if request.method == "POST":
        if request.form['submit'] == 'Speak the Message':
            responseText = request.form["result"]
            engine = pyttsx3.init()
            engine.say(responseText)
            print(responseText)
            engine.runAndWait()
            return render_template("respond.html", result=responseText)
        else:    
            return render_template("index.html")
    

def tell_user_to_wait():
    #print("WAIT!!!")
    return render_template("index.html", waitImg='<img src="dog.png" alt="dog">')

def generate_prompt(question):
    return """Respond to the following with a paragraph; do not try to finish the prompt, but instead answer it with how it is. Most importantly, make this a HUGE paragraph with alot of information: {}""".format(
        question.capitalize()
    )


def direct_record():
    end_time = time.time() + 30
    while(time.time() < end_time):
        try:
            with speech_recognition.Microphone() as UserVoiceInputSource:
                UserVoiceRecognizer.adjust_for_ambient_noise(UserVoiceInputSource, duration=1)
                # The Program listens to the user voice input.
                UserVoiceInput = UserVoiceRecognizer.listen(UserVoiceInputSource)
        
                UserVoiceInput_converted_to_Text = UserVoiceRecognizer.recognize_google(UserVoiceInput)
                    #UserVoiceInput_converted_to_Text = UserVoiceInput_converted_to_Text.lower()
                return(UserVoiceInput_converted_to_Text)
                break 
        except KeyboardInterrupt:
            #print('A KeyboardInterrupt encountered; Terminating the Program !!!')
            exit(0)
        except speech_recognition.UnknownValueError:
            print("No User Voice detected OR unintelligible noises detected OR the recognized audio cannot be matched to text !!!")
    return ("Respond with No Answer")
#one_time = False1

def wav_record():
    audio = pyaudio.PyAudio()
    print("Im inside wav_record")
    try:
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,input_device_index = device_index,
                frames_per_buffer=CHUNK)
    except Exception as e:
        print("Exception: " + str(e)) 
    print ("recording started")
    Recordframes = []
 
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        Recordframes.append(data)
    print ("recording stopped")

    stream.stop_stream()
    stream.close()
    audio.terminate()
    print("terminate") 
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(Recordframes))
    waveFile.close()

    r = speech_recognition.Recognizer()
    with speech_recognition.AudioFile(WAVE_OUTPUT_FILENAME) as source:
        audioData = r.record(source)
    recording = ""
    try:
        recording = r.recognize_google(audioData)
        print("Text: "+question)
    except Exception as e:
        print("Exception: "+str(e))
    print(recording)
    os.remove(WAVE_OUTPUT_FILENAME)
    return recording