#!/usr/bin/env python3
"""
TTS Manager for Voice AI Assistant - Fixed Text Preprocessing
Supports KittenTTS, Piper TTS engines, and comprehensive text cleaning
"""

import asyncio
import logging
import re
import tempfile
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

class TTSManager:
    def __init__(self, engine: str = "kittentts", voice: str = "libritts_r"):
        self.engine = engine.lower()
        self.voice = voice.lower()
        self.logger = logging.getLogger(__name__)
        self.tts_instance = None
        self.piper_cmd = None
        
        # Define available voices and their model paths
        self.available_voices = {
            "libritts_r": {
                "model": "en_US-libritts_r-medium.onnx",
                "config": "en_US-libritts_r-medium.onnx.json",
                "description": "High-quality neutral English voice"
            },
            "lessac": {
                "model": "en_US-lessac-medium.onnx",
                "config": "en_US-lessac-medium.onnx.json",
                "description": "Professional female English voice"
            },
            "glados": {
                "model": "glados.onnx",
                "config": "glados.onnx.json",
                "description": "GLaDOS - Genetic Lifeform and Disk Operating System"
            }
        }
        
        # Set model paths based on selected voice
        if self.voice in self.available_voices:
            voice_config = self.available_voices[self.voice]
            self.piper_model_path = Path(__file__).parent.parent / "models" / "piper" / voice_config["model"]
            self.piper_config_path = Path(__file__).parent.parent / "models" / "piper" / voice_config["config"]
        else:
            # Default to libritts_r if voice not found
            self.voice = "libritts_r"
            voice_config = self.available_voices[self.voice]
            self.piper_model_path = Path(__file__).parent.parent / "models" / "piper" / voice_config["model"]
            self.piper_config_path = Path(__file__).parent.parent / "models" / "piper" / voice_config["config"]
    
    async def initialize(self):
        """Initialize the selected TTS engine"""
        try:
            if self.engine == "kittentts":
                await self._init_kittentts()
            elif self.engine == "piper":
                await self._init_piper()
            else:
                raise ValueError(f"Unsupported TTS engine: {self.engine}")
            
            voice_desc = self.available_voices.get(self.voice, {}).get("description", "Unknown voice")
            self.logger.info(f"✅ {self.engine.upper()} TTS engine initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize {self.engine} TTS: {e}")
            raise

    async def _init_kittentts(self):
        """Initialize KittenTTS engine"""
        try:
            from kittentts import KittenTTS
            self.tts_instance = KittenTTS()
            self.logger.info("🐱 KittenTTS engine loaded")
        except ImportError as e:
            self.logger.error(f"❌ KittenTTS not available: {e}")
            raise
    
    async def _init_piper(self):
        """Initialize Piper TTS engine"""
        try:
            if not self.piper_model_path.exists():
                raise FileNotFoundError(f"Voice model not found: {self.piper_model_path}")
            if not self.piper_config_path.exists():
                raise FileNotFoundError(f"Voice config not found: {self.piper_config_path}")
            
            # Find piper command (check virtual env first)
            venv_piper = Path(__file__).parent.parent / "voice_ai_env" / "bin" / "piper"
            
            if venv_piper.exists() and os.access(venv_piper, os.X_OK):
                self.piper_cmd = str(venv_piper)
                self.logger.info(f"🎵 Found Piper TTS at: {self.piper_cmd}")
            else:
                # Check system PATH
                import shutil
                system_piper = shutil.which("piper")
                if system_piper:
                    self.piper_cmd = system_piper
                    self.logger.info(f"🎵 Found Piper TTS in PATH: {self.piper_cmd}")
                else:
                    raise RuntimeError("Piper TTS not found in virtual environment or system PATH")
            
            self.logger.info(f"🎵 Piper TTS ready with {self.voice} voice: {self.piper_model_path.name}")
            
        except Exception as e:
            self.logger.error(f"❌ Piper TTS initialization failed: {e}")
            raise

    def set_voice(self, voice: str):
        """Change the current voice (requires reinitialization)"""
        if voice.lower() in self.available_voices:
            self.voice = voice.lower()
            voice_config = self.available_voices[self.voice]
            self.piper_model_path = Path(__file__).parent.parent / "models" / "piper" / voice_config["model"]
            self.piper_config_path = Path(__file__).parent.parent / "models" / "piper" / voice_config["config"]
            self.logger.info(f"🔄 Voice changed to: {voice} ({voice_config['description']})")
        else:
            available_voices = ", ".join(self.available_voices.keys())
            self.logger.warning(f"⚠️ Voice '{voice}' not available. Available voices: {available_voices}")

    def get_available_voices(self) -> Dict[str, str]:
        """Get list of available voices with descriptions"""
        return {voice: config["description"] for voice, config in self.available_voices.items()}

    def prepare_text_for_tts(self, text: str) -> str:
        """Clean and prepare text for TTS synthesis - comprehensive preprocessing"""
        
        # 1. Remove markdown formatting and problematic symbols
        # Remove markdown bold (**text** and __text__)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        
        # Remove markdown italic (*text* and _text_)  
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        # Remove other markdown/formatting symbols
        text = re.sub(r'[`~#@$%^&\[\]{}\\|<>]', '', text)
        
        # Remove bullet points and list markers
        text = re.sub(r'^\s*[-•*]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)
        
        # 2. Remove emojis and unicode symbols
        text = re.sub(r"[🔥🎉😊😂😭🤔��✨🚀👍👎❤️🙃😎😍🤗🎯🎤🗣️💬🔊🎵🎶🎙️📢🔔🔕⚡💪👏🎊��]", "", text)
        
        # 3. Convert abbreviations to spoken form FIRST (before word boundaries can be affected)
        # Use word boundaries to prevent partial matches
        abbreviations = {
            r'\bDr\.': "Doctor",
            r'\bMr\.': "Mister", 
            r'\bMrs\.': "Missus",
            r'\bMs\.': "Miss",
            r'\bProf\.': "Professor",
            r'\bSt\.': "Street",
            r'\bAve\.': "Avenue",
            r'\b(\d+)°F\b': r'\1 degrees Fahrenheit',
            r'\b(\d+)°C\b': r'\1 degrees Celsius',
            r'\b(\d+)MPH\b': r'\1 miles per hour',
            r'\b(\d+)mph\b': r'\1 miles per hour',
            r'\b(\d+)lbs\b': r'\1 pounds',
            r'\b(\d+)ft\b': r'\1 feet',
            r'\bvs\b': "versus",
            r'\bVS\b': "versus",
            r'\betc\.?': "et cetera"
        }
        
        for pattern, replacement in abbreviations.items():
            text = re.sub(pattern, replacement, text)
        
        # 4. GLaDOS-specific text modifications
        if self.voice == "glados":
            text = self._add_glados_character(text)
        
        # 5. Clean up punctuation and spacing
        text = text.replace("…", "...").replace("–", "-").replace("—", "-")
        
        # Remove multiple spaces and clean whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # 6. Handle line breaks and sections
        # Convert double newlines to periods for natural pauses
        text = re.sub(r'\n\n+', '. ', text)
        text = re.sub(r'\n', ' ', text)
        
        # 7. Add period if missing for natural speech endings
        if text and text[-1] not in "!?.,:;":
            text += "."
        
        return text

    def _add_glados_character(self, text: str) -> str:
        """Add GLaDOS-specific character to text"""
        # Don't modify if it's already very GLaDOS-like
        glados_indicators = ["subject", "test", "chamber", "aperture", "science", "cake", "neurotoxin", "portal"]
        if any(indicator in text.lower() for indicator in glados_indicators):
            return text
            
        # Add subtle GLaDOS character without being too intrusive
        return text

    async def generate_speech(self, text: str) -> np.ndarray:
        """Generate speech audio from text using the selected TTS engine"""
        cleaned_text = self.prepare_text_for_tts(text)
        
        if self.engine == "kittentts":
            return await self._generate_kittentts(cleaned_text)
        elif self.engine == "piper":
            return await self._generate_piper(cleaned_text)
        else:
            raise ValueError(f"Unsupported TTS engine: {self.engine}")

    async def _generate_kittentts(self, text: str) -> np.ndarray:
        """Generate speech using KittenTTS"""
        try:
            audio_data = await asyncio.to_thread(
                self.tts_instance.generate,
                text, voice='expr-voice-4-f', speed=1.5
            )
            return np.array(audio_data, dtype=np.float32)
        except Exception as e:
            self.logger.error(f"❌ KittenTTS generation failed: {e}")
            raise

    async def _generate_piper(self, text: str) -> np.ndarray:
        """Generate speech using Piper TTS"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                # Run piper TTS with proper arguments
                cmd = [
                    self.piper_cmd,
                    "--model", str(self.piper_model_path),
                    "--output_file", temp_wav.name
                ]
                
                # Send text to piper via stdin
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate(text.encode('utf-8'))
                
                if process.returncode != 0:
                    raise RuntimeError(f"Piper TTS failed: {stderr.decode()}")
                
                # Load the generated audio
                import soundfile as sf
                audio_data, sample_rate = sf.read(temp_wav.name)
                
                # Clean up temp file
                os.unlink(temp_wav.name)
                
                # Ensure mono
                if len(audio_data.shape) > 1:
                    audio_data = np.mean(audio_data, axis=1)
                
                return audio_data.astype(np.float32)
                
        except Exception as e:
            self.logger.error(f"❌ Piper TTS generation failed: {e}")
            raise

    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the current TTS engine"""
        info = {"engine": self.engine, "voice": self.voice}
        
        if self.engine == "kittentts":
            info.update({
                "voice_internal": "expr-voice-4-f",
                "speed": 1.5,
                "type": "Neural TTS"
            })
        elif self.engine == "piper":
            voice_config = self.available_voices.get(self.voice, {})
            info.update({
                "model": voice_config.get("model", "unknown"),
                "description": voice_config.get("description", "Unknown voice"),
                "type": "Fast Neural TTS",
                "command": self.piper_cmd
            })
        
        return info
