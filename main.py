import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import subprocess
import os
import sys
import time
import wikipedia

try:
    import pywhatkit
except Exception:
    pywhatkit = None

try:
    import openai
except Exception:
    openai = None

ASSISTANT_NAME = "Jarvis"
WAKE_WORDS = ["jarvis", "hey jarvis", "ok jarvis"]
EXIT_COMMANDS = ["exit", "stop", "bye", "bye jarvis", "goodbye", "quit"]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if OPENAI_API_KEY:
    if openai:
        openai.api_key = OPENAI_API_KEY
    else:
        print("OpenAI library not installed. AI responses won't work.")

engine = pyttsx3.init()
engine.setProperty('rate', 170)
voices = engine.getProperty('voices')
if voices:
    try:
        engine.setProperty('voice', voices[0].id)
    except Exception:
        pass

def speak(text: str):
    print(f"{ASSISTANT_NAME}: {text}")
    engine.say(text)
    engine.runAndWait()

recognizer = sr.Recognizer()

def take_command(timeout: int = 6, phrase_time_limit: int = 8) -> str:
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.6)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for phrase to start")
            return ""
    try:
        print("Recognizing...")
        query = recognizer.recognize_google(audio, language='en-IN')
        print(f"You: {query}")
        return query.lower()
    except sr.UnknownValueError:
        print("Could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from recognition service; {e}")
        return ""

def wish_me():
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        speak("Good morning!")
    elif 12 <= hour < 18:
        speak("Good afternoon!")
    else:
        speak("Good evening!")
    speak(f"Hello, I am {ASSISTANT_NAME}. How can I help you today?")

def tell_time():
    now = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The current time is {now}")

def tell_date():
    today = datetime.datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today is {today}")

def open_website(domain_or_name: str):
    if not domain_or_name.startswith("http"):
        if "." in domain_or_name:
            url = f"https://{domain_or_name}"
        else:
            url = f"https://www.{domain_or_name}.com"
    else:
        url = domain_or_name
    speak(f"Opening {url}")
    webbrowser.open(url)

def search_wikipedia(topic: str, sentences: int = 2):
    try:
        speak(f"Searching Wikipedia for {topic}")
        summary = wikipedia.summary(topic, sentences=sentences, auto_suggest=True, redirect=True)
        speak(summary)
    except wikipedia.DisambiguationError as e:
        speak("There are multiple results for that topic. Please be more specific.")
        print(e)
    except wikipedia.PageError:
        speak("Sorry, I couldn't find a Wikipedia page for that topic.")
    except Exception as e:
        speak("An error occurred while searching Wikipedia.")
        print(e)

def play_song(song_name: str):
    if pywhatkit:
        speak(f"Playing {song_name} on YouTube")
        try:
            pywhatkit.playonyt(song_name)
        except Exception as e:
            speak("Sorry, I couldn't play the song.")
            print(e)
    else:
        speak("pywhatkit is not installed. Install it to play songs automatically.")

def google_search(query: str):
    speak(f"Searching Google for {query}")
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)

def open_app(app_path_or_name: str):
    try:
        if sys.platform.startswith("win"):
            try:
                os.startfile(app_path_or_name)
                speak(f"Opening {app_path_or_name}")
                return
            except Exception:
                pass
            subprocess.Popen(app_path_or_name)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", app_path_or_name])
        else:
            subprocess.Popen([app_path_or_name])
        speak(f"Opening {app_path_or_name}")
    except Exception as e:
        speak("Sorry, I couldn't open that application.")
        print(e)

def ai_answer(prompt: str) -> str:
    if not OPENAI_API_KEY or not openai:
        return ""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.6
        )
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        print("OpenAI request failed:", e)
        return ""

def process_command(query: str) -> bool:
    if not query:
        return True
    if any(cmd in query for cmd in EXIT_COMMANDS):
        speak("Goodbye. Have a nice day!")
        return False
    if "hello" in query or "hi" in query or "hey" in query:
        speak("Hello! How can I help you?")
        return True
    if ("time" in query and "what" in query) or ("current time" in query) or ("tell me the time" in query):
        tell_time()
        return True
    if "date" in query and ("today" in query or "what" in query):
        tell_date()
        return True
    if query.startswith("open "):
        target = query.replace("open ", "").strip()
        common = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "github": "https://github.com",
            "stackoverflow": "https://stackoverflow.com",
            "gmail": "https://mail.google.com",
        }
        if target in common:
            open_website(common[target])
        else:
            open_website(target)
        return True
    if query.startswith("wikipedia") or "wikipedia" in query and "search" in query:
        topic = query.replace("wikipedia", "").replace("search", "").replace("for", "").strip()
        if not topic:
            speak("What should I search on Wikipedia?")
            return True
        search_wikipedia(topic)
        return True
    if "search wikipedia for" in query:
        topic = query.split("search wikipedia for", 1)[1].strip()
        if topic:
            search_wikipedia(topic)
            return True
    if query.startswith("play ") or query.startswith("play song ") or "play me" in query:
        song = query.replace("play", "").replace("song", "").replace("play me", "").strip()
        if song:
            play_song(song)
        else:
            speak("Which song would you like me to play?")
        return True
    if query.startswith("search ") or query.startswith("google "):
        search_query = query.replace("search", "").replace("google", "").strip()
        if search_query:
            google_search(search_query)
        else:
            speak("What should I search for?")
        return True
    if query.startswith("open app ") or query.startswith("open application "):
        name = query.replace("open app", "").replace("open application", "").strip()
        if name:
            open_app(name)
        else:
            speak("Which application do you want to open?")
        return True
    if "shutdown" in query and "computer" in query:
        speak("Shutting down the computer. Goodbye.")
        if sys.platform.startswith("win"):
            os.system("shutdown /s /t 5")
        elif sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
            os.system("sudo shutdown -h now")
        return False
    if OPENAI_API_KEY and openai:
        speak("Let me think...")
        answer = ai_answer(query)
        if answer:
            speak(answer)
        else:
            speak("Sorry, I couldn't fetch an AI response.")
        return True
    speak("Sorry, I didn't understand that. I can search Google or Wikipedia, open websites, tell the time, or play songs. Would you like me to search the web for that?")
    return True

def main():
    speak(f"Starting {ASSISTANT_NAME}...")
    wish_me()
    running = True
    try:
        while running:
            query = take_command()
            if not query:
                time.sleep(0.6)
                continue
            running = process_command(query)
            time.sleep(0.5)
    except KeyboardInterrupt:
        speak("Keyboard interrupt received. Shutting down.")
    except Exception as e:
        print("Unexpected error:", e)
        speak("An unexpected error occurred. Shutting down.")

if __name__ == "__main__":
    main()
