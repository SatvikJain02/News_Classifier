# Command prompt to run:
# uvicorn main:app --reload

# Imports:
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, ConfigDict, Field
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle
import numpy as np
import os
from auth import (
    UserAuth, TokenResponse, register_new_user, authenticate_user, 
    create_access_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta

# Initializing the app:
app = FastAPI(
    title="News Classifier API",
    description="The TRUTH SEEKER: Detecting Fake News with Neural Networks 🕵️‍♂️"
)

# Robust Resource Loading:
MODEL_PATH = 'news_classifier_model.h5'
TOKENIZER_PATH = 'tokenizer.pickle'

# ⚠️ CRITICAL: This must match the 'maxlen' you used during training!
MAX_SEQUENCE_LENGTH = 256

# Load Model:
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"⚠️ Model file not found at {MODEL_PATH}")
model = tf.keras.models.load_model(MODEL_PATH)

# Load Tokenizer:
if not os.path.exists(TOKENIZER_PATH):
    raise FileNotFoundError(f"⚠️ Tokenizer file not found at {TOKENIZER_PATH}")
with open(TOKENIZER_PATH, 'rb') as handle:
    tokenizer = pickle.load(handle)

# Input Schema:
class NewsData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # Input validation
    text: str = Field(..., alias='News Content', min_length=10, example="Breaking: Scientists discover water on the Sun.")

# Output Schema:
class Result(BaseModel):
    prediction: str
    confidence_score: float

# Prediction Endpoint:
@app.post('/predict', response_model=Result)
def predict(data: NewsData, username: str = Depends(verify_token)):
    
    print(f"User {username} is investigating a headline! 🕵️‍♂️")

    try:
        # Step 1: Preprocessing (Tokenization)
        # Convert text string to sequence of integers
        sequences = tokenizer.texts_to_sequences([data.text])

        # Step 2: Padding
        # Ensure input is the exact length the model expects
        padded_input = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)

        # Step 3: Prediction
        prediction_prob = model.predict(padded_input)[0][0] # Assuming binary output (0-1)

        # Step 4: Logic (Thresholding)
        # Adjust '0.5' based on your model's sensitivity
        label = "Fake News" if prediction_prob >= 0.5 else "Real News"

        return Result(
            prediction=label,
            confidence_score=float(prediction_prob)
        )
    
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

# Home Endpoint:
@app.get('/')
def home():
    return {'message': "News Classifier is Live! Check /docs for the truth."}

# Auth Endpoints (Kept from your original code):
@app.post('/register', response_model=TokenResponse)
def register(user: UserAuth):
    register_new_user(user)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {'access_token': access_token, 'token_type': 'Bearer', 'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60}

@app.post('/login', response_model=TokenResponse)
def login(user: UserAuth):
    if not authenticate_user(user):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(
        data={'sub': user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {'access_token': access_token, 'token_type': 'Bearer', 'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60}