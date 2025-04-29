from flask import Flask, render_template, request, jsonify
import numpy as np
import pandas as pd
from transformers import pipeline
import speech_recognition as sr
from datetime import datetime
import os
import random

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

def get_response(emotion_label, emotion_score, risk_level):
    # Expanded response library
    response_library = {
        "sadness": {
            "low": [
                "I hear that you're feeling down. Would you like to share more about what's on your mind?",
                "It's okay to feel sad sometimes. Remember that emotions are temporary visitors.",
                "I'm here to listen if you'd like to talk about what's making you feel this way."
            ],
            "medium": [
                "I can sense you're feeling quite sad. Would a guided meditation help right now?",
                "When sadness feels heavy, sometimes writing about it can help. Would you like some journaling prompts?",
                "You're not alone in feeling this way. Would you like me to suggest some resources that might help?"
            ],
            "high": [
                "I'm concerned about the level of distress you're experiencing. Would you like me to connect you with professional support?",
                "What you're feeling sounds really difficult. Please know help is available - would you like me to show you how to reach it?",
                "Your feelings are important. I strongly recommend speaking with someone who can help. Can I connect you with resources?"
            ]
        },
        "anger": {
            "low": [
                "I notice you're feeling some anger. Sometimes taking three deep breaths can help create space between the feeling and reaction.",
                "Anger is a natural emotion - would you like some strategies to express it in healthy ways?",
                "What's coming up for you right now? I'm here to listen if you'd like to share."
            ],
            "medium": [
                "Anger can feel overwhelming. Try the 5-4-3-2-1 grounding technique: name 5 things you see, 4 you can touch...",
                "When anger feels intense, physical movement can help release it. Would you like some simple exercises to try?",
                "I sense strong emotions. Would it help to explore what's beneath the anger?"
            ],
            "high": [
                "This level of anger sounds very intense. Your safety is important - would you like help finding support?",
                "When emotions feel this strong, it's important to reach out. Can I help you connect with someone?",
                "I'm hearing significant distress. Please consider calling a crisis line if you need immediate support."
            ]
        },
        "fear": {
            "low": [
                "It sounds like you're feeling some anxiety. Remember - feelings are temporary, even when they feel permanent.",
                "When fear arises, sometimes naming it can help. 'I'm noticing I feel afraid about...'",
                "Would you like to try a simple breathing exercise to help with these anxious feelings?"
            ],
            "medium": [
                "Anxiety can feel overwhelming. Try placing one hand on your chest and one on your belly - breathe deeply into your hands.",
                "I hear significant worry in what you're sharing. Would you like to explore some coping strategies together?",
                "When fear feels intense, sometimes writing down the specific worries can help contain them."
            ],
            "high": [
                "This sounds like intense anxiety. Please know help is available - would you like me to connect you with resources?",
                "Panic attacks can feel terrifying but they always pass. Can I guide you through a grounding exercise?",
                "Your distress sounds significant. I strongly recommend reaching out to a professional who can help."
            ]
        },
        "joy": {
            "low": [
                "It's wonderful to hear you're feeling positive! What's contributing to these good feelings?",
                "Joy is beautiful to witness! Would you like to explore how to cultivate more of these moments?",
                "I'm glad you're experiencing positive emotions today!"
            ],
            "medium": [
                "Happiness shines through! Have you considered journaling about what's bringing you joy today?",
                "Positive emotions are worth savoring. Try taking a moment to really soak in this feeling.",
                "It's great to hear you're feeling good! Would you like some ideas for maintaining this mood?"
            ],
            "high": [
                "Your enthusiasm is contagious! What's making you feel so joyful today?",
                "This level of happiness is wonderful to see! Consider sharing these good feelings with someone you care about.",
                "Radiant joy! Remember these moments when harder days come."
            ]
        },
        "love": {
            "low": [
                "Love is a beautiful emotion to experience. Would you like to share more about what you're feeling?",
                "Connections with others can be so meaningful. What relationships are bringing you joy right now?",
                "I hear warmth in what you're sharing. Would you like to explore this feeling further?"
            ],
            "medium": [
                "Love shines through your words! Have you told the person/people how you feel?",
                "Strong feelings of connection are wonderful. Would you like some ideas for nurturing these relationships?",
                "Your capacity for love is beautiful. Remember to extend that same care to yourself too."
            ],
            "high": [
                "Your loving feelings are radiant! Consider expressing these emotions to those you care about.",
                "Deep connections are precious. Would you like to explore ways to strengthen them further?",
                "This level of loving emotion is wonderful. How might you channel this energy positively?"
            ]
        },
        "surprise": {
            "low": [
                "Surprise can be unsettling or exciting. How are you experiencing it?",
                "Unexpected events can throw us off balance. Would you like to talk through what happened?",
                "Change can be challenging. Would you like some strategies for adapting?"
            ],
            "medium": [
                "This surprise seems significant. Would it help to explore how you're feeling about it?",
                "Unexpected events can be disorienting. Try naming three things that haven't changed to ground yourself.",
                "When surprises shake us up, sometimes talking it through helps. I'm here to listen."
            ],
            "high": [
                "This sounds like a major unexpected event. Would you like help processing what happened?",
                "Significant surprises can be overwhelming. Would you like me to suggest some coping strategies?",
                "Your distress sounds significant. Please know support is available if you need it."
            ]
        },
        "default": {
            "low": [
                "Thanks for sharing how you're feeling. Would you like to explore this further?",
                "I'm here to listen if you'd like to share more about what's on your mind.",
                "All feelings are valid. Would you like some support with what you're experiencing?"
            ],
            "medium": [
                "I sense some intensity in what you're sharing. Would you like to talk more about it?",
                "This seems important to you. Would you like some resources that might help?",
                "Would it help to explore coping strategies for what you're experiencing?"
            ],
            "high": [
                "I'm hearing significant distress. Would you like me to help you find support?",
                "Your feelings matter. I strongly recommend connecting with someone who can help.",
                "Please consider reaching out to a professional about what you're experiencing."
            ]
        }
    }

    # Get responses for the detected emotion or use default
    emotion_responses = response_library.get(emotion_label, response_library["default"])
    
    # Select based on risk level
    responses = emotion_responses.get(risk_level, emotion_responses["medium"])
    
    # Add some randomization
    return random.choice(responses)

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
    
    # Enhanced risk assessment
    risk_level = "low"
    if emotion['score'] > 0.85:
        risk_level = "medium"
    if emotion['score'] > 0.95:
        risk_level = "high"
        
    # Check for crisis keywords
    crisis_keywords = ["suicide", "kill myself", "end it all", "can't go on", "don't want to live"]
    if any(keyword in text.lower() for keyword in crisis_keywords):
        risk_level = "high"
    
    # Get tailored response
    response = get_response(emotion['label'], emotion['score'], risk_level)
    resources = get_resources(emotion['label'])
    
    return jsonify({
        "sentiment": sentiment,
        "emotion": emotion,
        "risk_level": risk_level,
        "response": response,
        "resources": resources
    })

def get_resources(emotion):
    resources = {
        "sadness": [
            "Guided meditation for sadness: 5-minute body scan",
            "Journaling prompts: 'What does my sadness need me to know today?'",
            "Comforting playlist: Soothing instrumental music",
            "Self-care idea: Warm tea and a cozy blanket"
        ],
        "anger": [
            "Anger management: 10-minute timeout technique",
            "Physical release: Try punching a pillow or screaming into one",
            "Cool-down exercise: Splash cold water on your face",
            "Perspective tool: 'Will this matter in 5 years?' worksheet"
        ],
        "fear": [
            "Anxiety reduction: 4-7-8 breathing technique",
            "Grounding exercise: Describe your surroundings in detail",
            "Worry containment: Set aside 15 minutes of 'worry time' later",
            "Safety reminder: Make a list of people you can call right now"
        ],
        "joy": [
            "Positive habits: Gratitude journal template",
            "Moment savoring: Take a mental photograph of this feeling",
            "Connection idea: Share your joy with someone else",
            "Energy channeling: Creative activity suggestions"
        ],
        "love": [
            "Relationship building: Active listening exercises",
            "Connection ideas: Meaningful questions to ask loved ones",
            "Self-love: Appreciation journal for yourself",
            "Kindness challenge: Random acts of kindness ideas"
        ],
        "surprise": [
            "Adaptation tools: Change management worksheet",
            "Perspective shift: 'What might be good about this?' exercise",
            "Stabilizing technique: Maintain your normal routine where possible",
            "Support system: Who can help you process this?"
        ]
    }
    return resources.get(emotion, [
        "General wellness tips",
        "Mindfulness meditation guide",
        "Daily self-care checklist",
        "Sleep hygiene recommendations"
    ])

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

@app.route('/get_mood_history', methods=['GET'])
def get_mood_history():
    # Return mood history for visualization
    return jsonify({
        "mood_history": user_data["mood_history"],
        "stats": {
            "total_entries": len(user_data["mood_history"]),
            "recent_emotion": user_data["mood_history"][-1]["emotion"]["label"] if user_data["mood_history"] else None,
            "avg_sentiment": np.mean([entry["sentiment"]["score"] for entry in user_data["mood_history"]]) if user_data["mood_history"] else 0
        }
    })

if __name__ == '__main__':
    app.run(debug=True)