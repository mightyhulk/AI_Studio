from fastapi import FastAPI
from pydantic import BaseModel, Form, UploadFile
from summarizer import text_summarizer
from image_generator import image_gen
from speech_generator import speech_gen
from text_generator import chat


class Prompt(BaseModel):
    prompt: str


app = FastAPI()


@app.post("/home")
async def main(intent = Form(...), file: UploadFile = File(...), prompt: Prompt):
    
    if intent == summarize:
        response = text_summarizer(file, prompt)
    elif intent == image_generation:
        response = image_gen(file, prompt)
    elif intent == speech_generation:
        response = speech_gen(file, prompt)
    else: 
        response = chat(file, prompt)
    
    return {response}































