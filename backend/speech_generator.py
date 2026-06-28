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

# Gemini TTS multi-speaker mode supports exactly 2 speakers.
MAX_MULTI_SPEAKERS = 2


def _resolve_voice_name(gender: str | None, used: set | None = None) -> str:
    """Pick a voice for the given gender, avoiding already-used voices."""
    key = (gender or "neutral").lower()
    candidates = VOICE_MAP.get(key, VOICE_MAP["neutral"])
    if used:
        for v in candidates:
            if v not in used:
                return v
    return candidates[0]


def get_voice_config(speaker_name: str, gender: str, used_voices: set):
    voice_name = _resolve_voice_name(gender, used_voices)
    used_voices.add(voice_name)
    return types.SpeakerVoiceConfig(
        speaker=speaker_name,
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
        ),
    )


def build_speaker_configs(speakers):
    used_voices = set()
    return [get_voice_config(s["name"], s["gender"], used_voices) for s in speakers]


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


def _sanitize_json(raw: str) -> str:
    """Fix common LLM JSON issues: trailing commas, single quotes, etc."""
    # Remove trailing commas before } or ]
    cleaned = re.sub(r",\s*([}\]])", r"\1", raw)
    # Replace single-quoted strings with double-quoted strings
    cleaned = re.sub(r"'(\w+)'\s*:", r'"\1":', cleaned)
    cleaned = re.sub(r":\s*'([^']*)'", r': "\1"', cleaned)
    return cleaned


def extract_json(text: str):
    match = re.search(r"(\[.*\])", text, re.DOTALL)
    if match:
        return _sanitize_json(match.group(1))
    return None


def get_client():
    return genai.Client(api_key=os.getenv("gemini_api", "missing_key"))


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

    analysis_instruction = f"""\
Analyze the following prompt and extract speakers.
For each speaker return an object with keys: "name", "gender", "description".
If names are not given, invent plausible ones. Gender must be one of: male, female, neutral.
Return ONLY a JSON array, no markdown, no extra text.

Prompt:
\"\"\"{prompt}\"\"\"
"""

    client = get_client()
    analysis_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=analysis_instruction,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    json_text = extract_json(_response_text(analysis_response))
    if not json_text:
        # Fallback: treat the prompt as single-speaker narration
        speakers = [{"name": "Narrator", "gender": "neutral", "description": "General narration"}]
    else:
        try:
            speakers = json.loads(json_text)
        except json.JSONDecodeError:
            # JSON was still malformed after sanitization — use a safe default
            speakers = [{"name": "Narrator", "gender": "neutral", "description": "General narration"}]
        if not isinstance(speakers, list) or not speakers:
            speakers = [{"name": "Narrator", "gender": "neutral", "description": "General narration"}]

    for index, speaker in enumerate(speakers):
        speaker.setdefault("name", f"Speaker {index + 1}")
        speaker.setdefault("gender", "neutral")
        speaker.setdefault("description", "General narration")

    # Gemini TTS allows at most 2 speakers in multi-speaker mode.
    # If the LLM detected more, keep only the first two and note the rest.
    all_speakers = speakers
    if len(speakers) > MAX_MULTI_SPEAKERS:
        speakers = speakers[:MAX_MULTI_SPEAKERS]

    if is_descriptive_prompt(prompt, speakers):
        if len(speakers) == 1:
            instruction = (
                f"Write a detailed, engaging lecture or speech (about 100-200 words) in first person, "
                f"as if delivered by {speakers[0]['name']} ({speakers[0]['gender']}). "
                f"Topic: {speakers[0]['description']}."
            )
        else:
            speaker_list = ", ".join([f"{s['name']} ({s['gender']})" for s in speakers])
            topic = all_speakers[0].get('description') or 'a casual conversation'
            instruction = (
                f"Write a detailed, engaging conversation (about 100-200 words) as a dialogue between exactly these two speakers: {speaker_list}. "
                f"Each line MUST start with the speaker's name followed by a colon. "
                f"Use ONLY these two speaker names, no others. "
                f"Topic: {topic}."
            )

        client = get_client()
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

    try:
        client = get_client()
        tts_response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=formatted_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=speech_config,
            ),
        )
    except Exception as tts_err:
        raise ValueError(f"Speech generation failed: {tts_err}") from tts_err

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
