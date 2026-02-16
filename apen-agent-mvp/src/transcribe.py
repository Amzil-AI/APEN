"""
Speech-to-text for audio testing. Uses OpenAI Whisper API.
Set OPENAI_API_KEY in env. Supports: mp3, mp4, mpeg, mpga, m4a, wav, webm.
"""
import os
from typing import Optional

def transcribe_audio(audio_path: str, language: Optional[str] = None) -> str:
    """
    Transcribe audio file to text via OpenAI Whisper API.
    Returns transcript or raises ValueError if API key missing or request fails.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not set. Add it to .env or export OPENAI_API_KEY=sk-..."
        )

    try:
        from openai import OpenAI
    except ImportError:
        raise ValueError("Install openai: pip install openai")

    client = OpenAI(api_key=api_key)

    with open(audio_path, "rb") as f:
        # language hint improves accuracy (e.g. "fr", "en")
        kwargs = {"file": f, "model": "whisper-1"}
        if language:
            kwargs["language"] = language
        response = client.audio.transcriptions.create(**kwargs)

    return (response.text or "").strip()
