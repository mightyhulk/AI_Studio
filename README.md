# HuggingFace AI Studio

![Status](https://img.shields.io/badge/status-under%20development-yellow)

## 🚧 Project Status
This project is under active development. Core features are being implemented and enhanced.



A unified **Multimodal Generative AI application** built using **Hugging Face Transformers**, showcasing the power of Large Language Models (LLMs) across **Text, Image, and Speech modalities**.

This project combines:
- ✍️ Text Summarization
- 🎨 Text-to-Image Generation
- 🔊 Text-to-Speech Generation

into a single, scalable AI system.

---

## 🚀 Features

### 1️⃣ Text Summarization
- Summarizes long-form text into concise, meaningful summaries  
- Powered by Hugging Face Transformer models  
- Supports custom input length and summary size  

### 2️⃣ Text-to-Image Generation
- Generates high-quality images from natural language prompts  
- Uses state-of-the-art diffusion-based models  
- Enables creative and descriptive prompt-based image synthesis  

### 3️⃣ Text-to-Speech Generation
- Converts text into natural-sounding speech  
- Supports different voices and speech styles  
- Useful for accessibility, narration, and voice-based applications  

---

## 🧠 Models Used

| Task | Model |
|------|-------|
| Text Summarization | `facebook/bart-large-cnn` |
| Text-to-Image | `stabilityai/stable-diffusion` |
| Text-to-Speech | `facebook/fastspeech2-en-ljspeech` / `suno/bark` |

*(Models can be easily swapped or upgraded)*

---

## 🛠️ Tech Stack

- **Python**
- **Hugging Face Transformers**
- **Diffusers**
- **Torch**
- **FastAPI / Streamlit** 
- **NumPy, PIL**

---

## 📂 Project Structure

```
huggingface-ai-studio/
│
├── text_summarization/
│ └── summarizer.py
│
├── text_to_image/
│ └── image_generator.py
│
├── text_to_speech/
│ └── speech_generator.py
│
├── app.py # Unified entry point
├── requirements.txt
└── README.md

```