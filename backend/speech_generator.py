
## Auto speaker config: LLM analyzes prompt for speaker count, names, genders, etc.
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import wave
import json
import re

load_dotenv()

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

# Predefined voice options (can be extended)
VOICE_MAP = {
    "male": ["Puck", "Bram", "Kai"],
    "female": ["Kore", "Nova", "Mira"],
    "neutral": ["Sky", "Echo"]
}

def get_voice_config(speaker_name, gender):
    voices = VOICE_MAP.get(gender.lower(), VOICE_MAP["neutral"])
    voice_name = voices[0]
    return types.SpeakerVoiceConfig(
        speaker=speaker_name,
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=voice_name
            )
        )
    )

def build_speaker_configs(speakers):
    return [get_voice_config(s["name"], s["gender"]) for s in speakers]

def format_prompt_for_speakers(prompt, speakers):
    if len(speakers) == 1:
        return prompt
    # If multiple speakers, try to format as a dialogue if not already
    if any(s["name"] + ":" in prompt for s in speakers):
        return prompt
    lines = prompt.split('\n')
    formatted = []
    for i, line in enumerate(lines):
        speaker = speakers[i % len(speakers)]["name"]
        formatted.append(f"{speaker}: {line.strip()}")
    return "\n".join(formatted)

def extract_json(text):
    match = re.search(r'(\[.*\])', text, re.DOTALL)
    if match:
        return match.group(1)
    return None

client = genai.Client(api_key=os.getenv('gemini_api'))



def speech_gen(query):
    prompt = query

    # Use LLM to analyze prompt and extract speaker info
    analysis_instruction = """
    Analyze the following prompt and extract:
    - The number of speakers
    - For each speaker: name (if any), gender (male/female/neutral/unknown), and a short description if possible
    - If names are not given, invent plausible ones based on context and gender
    - Output a JSON list of speakers, each as an object with keys: name, gender, description

    Prompt:
    \"\"\"{}\"\"\"
    """.format(prompt)

    analysis_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=analysis_instruction
    )

    json_text = extract_json(analysis_response.text)
    if not json_text:
        raise ValueError("Could not extract speaker info from LLM response:\n" + analysis_response.text)

    speakers = json.loads(json_text)

    # If the prompt is descriptive (not a direct speech or dialogue), generate content first
    def is_descriptive_prompt(prompt, speakers):
        # Heuristic: if the prompt is short, or doesn't contain "I", or is a description
        if len(speakers) == 1:
            if len(prompt.split()) < 15 or "I " not in prompt and ":" not in prompt:
                return True
        return False

    def is_descriptive_prompt(prompt, speakers):
        # Heuristic: if the prompt is short, or doesn't contain ":", or is a description
        if len(prompt.split()) < 15 or not any(s["name"] + ":" in prompt for s in speakers):
            return True
        return False

    if is_descriptive_prompt(prompt, speakers):
        if len(speakers) == 1:
            gen_content_instruction = (
                f"Write a detailed, engaging lecture or speech (about 100-200 words) in first person, "
                f"as if delivered by {speakers[0]['name']} ({speakers[0]['gender']}). "
                f"Topic: {speakers[0]['description']}."
            )
        else:
            # For multiple speakers, generate a dialogue
            speaker_list = ", ".join([f'{s["name"]} ({s["gender"]})' for s in speakers])
            gen_content_instruction = (
                f"Write a detailed, engaging conversation (about 100-200 words) as a dialogue between {speaker_list}. "
                f"Each line should start with the speaker's name followed by a colon. "
                f"Topic: {speakers[0]['description']}."
            )
        gen_content_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=gen_content_instruction
        )
        generated_content = gen_content_response.text.strip()
        formatted_prompt = generated_content
    else:
        formatted_prompt = format_prompt_for_speakers(prompt, speakers)

    # If only one speaker, use single speaker config
    if len(speakers) == 1:
        voice_config = types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=VOICE_MAP[speakers[0]["gender"].lower()][0]
            )
        )
        speech_config = types.SpeechConfig(
            voice_config=voice_config
        )
    else:
        multi_speaker_config = types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=build_speaker_configs(speakers)
        )
        speech_config = types.SpeechConfig(
            multi_speaker_voice_config=multi_speaker_config
        )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=formatted_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=speech_config
            )
        )
        data = response.candidates[0].content.parts[0].inline_data.data
        file_name = 'backend/audio2.wav'
        wave_file(file_name, data)
        print(f"Audio saved to {file_name}")
        print("Speaker analysis:", json.dumps(speakers, indent=2))
        print("Prompt sent to TTS:\n", formatted_prompt)
    except Exception as e:
        print("Error generating audio:", e)
        print("Speaker analysis:", json.dumps(speakers, indent=2))
        print("Prompt sent to TTS:\n", formatted_prompt)

    
    
    


query = "Two female girls taking about their boyfriend on phone call"
speech_gen(query)




