from flask import Flask, render_template, request, jsonify
import numpy as np
import pandas as pd
from transformers import pipeline
import speech_recognition as sr
from datetime import datetime
import os

app = Flask(__name__)

# Load AI models
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
emotion_classifier = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")

# Mock behavioral data storage
user_data = {
    "mood_history": [],
    "sleep_patterns": [],
    "activity_levels": []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    text = request.json['text']
    
    # Sentiment analysis
    sentiment = sentiment_analyzer(text)[0]
    
    # Emotion classification
    emotion = emotion_classifier(text)[0]
    
    # Store data
    timestamp = datetime.now().isoformat()
    user_data["mood_history"].append({
        "timestamp": timestamp,
        "text": text,
        "sentiment": sentiment,
        "emotion": emotion
    })
    
    # Simple risk assessment
    risk_level = "low"
    if emotion['label'] in ['sadness', 'fear', 'anger'] and emotion['score'] > 0.9:
        risk_level = "medium"
    if "suicide" in text.lower() or "kill myself" in text.lower():
        risk_level = "high"
    
    # Generate response
    responses = {
        "low": ["Here's a calming exercise to try...", "You might enjoy this mindfulness activity..."],
        "medium": ["I notice you're feeling strong emotions. Would you like to try a grounding exercise?", 
                  "It might help to talk to someone about this."],
        "high": ["I'm concerned about what you're sharing. Would you like me to connect you with help?", 
                 "Please consider reaching out to a crisis line: 1-800-273-8255"]
    }
    
    return jsonify({
        "sentiment": sentiment,
        "emotion": emotion,
        "risk_level": risk_level,
        "response": np.random.choice(responses[risk_level]),
        "resources": get_resources(emotion['label'])
    })

def get_resources(emotion):
    resources = {
        "sadness": ["Guided meditation for sadness", "Journaling prompts for difficult emotions"],
        "anger": ["Anger management techniques", "Breathing exercises for frustration"],
        "fear": ["Anxiety reduction strategies", "Grounding techniques for panic"],
        "joy": ["Maintaining positive habits", "Gratitude exercises"],
        "love": ["Building healthy relationships", "Communication skills"],
        "surprise": ["Coping with unexpected events", "Adapting to change"]
    }
    return resources.get(emotion, ["General wellness tips"])

@app.route('/analyze_audio', methods=['POST'])
def analyze_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            
            # Analyze the transcribed text
            return analyze_text(text)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)