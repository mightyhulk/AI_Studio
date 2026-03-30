## Auto speaker config: LLM analyzes prompt for speaker count, names, genders, etc.
import base64
import json
import os
import re
import wave
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

BASE_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "generated"
DEFAULT_AUDIO_PATH = BASE_OUTPUT_DIR / "audio2.wav"


def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(filename), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


VOICE_MAP = {
    "male": ["puck", "charon", "iapetus"],
    "female": ["kore", "schedar", "sulafat"],
    "neutral": ["zephyr", "umbriel", "vindemiatrix"],
}


def _resolve_voice_name(gender: str | None) -> str:
    key = (gender or "neutral").lower()
    return VOICE_MAP.get(key, VOICE_MAP["neutral"])[0]


def get_voice_config(speaker_name: str, gender: str):
    voice_name = _resolve_voice_name(gender)
    return types.SpeakerVoiceConfig(
        speaker=speaker_name,
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
        ),
    )


def build_speaker_configs(speakers):
    return [get_voice_config(s["name"], s["gender"]) for s in speakers]


def format_prompt_for_speakers(prompt: str, speakers):
    if len(speakers) == 1:
        return prompt
    if any(f"{s['name']}:" in prompt for s in speakers):
        return prompt
    lines = prompt.split("\n")
    formatted = []
    for index, line in enumerate(lines):
        speaker = speakers[index % len(speakers)]["name"]
        formatted.append(f"{speaker}: {line.strip()}")
    return "\n".join(formatted)


def extract_json(text: str):
    match = re.search(r"(\[.*\])", text, re.DOTALL)
    if match:
        return match.group(1)
    return None


client = genai.Client(api_key=os.getenv("gemini_api"))


def is_descriptive_prompt(prompt: str, speakers):
    prompt = prompt or ""
    if not prompt.strip():
        return True
    if any(f"{s.get('name')}:" in prompt for s in speakers):
        return False
    return len(prompt.split()) < 15


def _response_text(response):
    if getattr(response, "text", None):
        return response.text
    candidates = getattr(response, "candidates", [])
    if candidates:
        parts = getattr(candidates[0].content, "parts", [])
        for part in parts:
            if getattr(part, "text", None):
                return part.text
    return ""


def _decode_audio_payload(data):
    if isinstance(data, bytes):
        return data
    return base64.b64decode(data)


def speech_gen(query: str, output_path: str | Path | None = None):
    prompt = (query or "").strip()
    if not prompt:
        raise ValueError("Prompt for speech generation cannot be empty.")

    analysis_instruction = f"""
    Analyze the following prompt and extract:
    - The number of speakers
    - For each speaker: name (if any), gender (male/female/neutral/unknown), and a short description if possible
    - If names are not given, invent plausible ones based on context and gender
    - Output a JSON list of speakers, each as an object with keys: name, gender, description

    Prompt:
    \"\"\"{prompt}\"\"\"
    """

    analysis_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=analysis_instruction,
    )

    json_text = extract_json(_response_text(analysis_response))
    if not json_text:
        raise ValueError("Could not extract speaker info from LLM response.")

    speakers = json.loads(json_text)
    if not isinstance(speakers, list) or not speakers:
        raise ValueError("Speaker analysis did not return any speakers.")

    for index, speaker in enumerate(speakers):
        speaker.setdefault("name", f"Speaker {index + 1}")
        speaker.setdefault("gender", "neutral")
        speaker.setdefault("description", "General narration")

    if is_descriptive_prompt(prompt, speakers):
        if len(speakers) == 1:
            instruction = (
                f"Write a detailed, engaging lecture or speech (about 100-200 words) in first person, "
                f"as if delivered by {speakers[0]['name']} ({speakers[0]['gender']}). "
                f"Topic: {speakers[0]['description']}."
            )
        else:
            speaker_list = ", ".join([f"{s['name']} ({s['gender']})" for s in speakers])
            instruction = (
                f"Write a detailed, engaging conversation (about 100-200 words) as a dialogue between {speaker_list}. "
                f"Each line should start with the speaker's name followed by a colon. "
                f"Topic: {speakers[0]['description']}."
            )

        generated_content = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=instruction,
        )
        formatted_prompt = _response_text(generated_content).strip()
    else:
        formatted_prompt = format_prompt_for_speakers(prompt, speakers)

    if len(speakers) == 1:
        voice_name = _resolve_voice_name(speakers[0].get("gender"))
        speech_config = types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
            )
        )
    else:
        speech_config = types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=build_speaker_configs(speakers)
            )
        )

    tts_response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=formatted_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=speech_config,
        ),
    )

    candidate = tts_response.candidates[0]
    parts = getattr(candidate.content, "parts", [])
    if not parts or not getattr(parts[0], "inline_data", None):
        raise ValueError("No audio data returned by the TTS model.")

    audio_bytes = _decode_audio_payload(parts[0].inline_data.data)
    resolved_output = Path(output_path) if output_path else DEFAULT_AUDIO_PATH
    wave_file(resolved_output, audio_bytes)

    return {
        "file": str(resolved_output),
        "speakers": speakers,
        "prompt": formatted_prompt,
    }
