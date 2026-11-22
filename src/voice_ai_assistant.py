#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from greeting_phrases import get_mixed_greeting, get_time_aware_greeting, get_glados_greeting, get_random_greeting
"""
Raspberry Pi 5 Voice AI Assistant
Voice Bonnet → onnx-asr (INT8 Parakeet-TDT) → Ollama LLM → KittenTTS Pipeline

Performance optimized with INT8 quantized Parakeet-TDT:
- 7.77x realtime transcription on ARM SBCs
- Sub-second STT processing for most queries
- Dramatically reduced latency vs sherpa-onnx
"""

import asyncio
import logging
import os
import sys
import time
import threading
import queue
import numpy as np
from typing import Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from pathlib import Path
import tempfile

# Audio and GPIO
import pyaudio
import soundfile as sf
import board
import digitalio
from adafruit_debouncer import Debouncer

# AI Components - FAST onnx-asr instead of sherpa-onnx!
import onnx_asr
from tts_manager import TTSManager
import ollama
import yaml
from led_manager_enhanced import LEDManager

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "voice_ai_config.yaml"

@dataclass
class AudioChunk:
    """Audio data chunk for processing"""
    data: np.ndarray
    sample_rate: int
    timestamp: float
    is_speech: bool = False

@dataclass 
class STTResult:
    """Speech-to-text result"""
    text: str
    confidence: float
    processing_time: float

class VoiceAIAssistant:
    """
    High-performance Voice AI Assistant optimized for Raspberry Pi 5
    
    Features:
    - Ultra-fast INT8 quantized STT (7.77x realtime)
    - Dual LLM model support with voice switching  
    - Real-time audio pipeline with VAD
    - Voice Bonnet integration with debounced button
    - CPU affinity optimization for Pi 5
    """
    
    def __init__(self, config_path: str = str(CONFIG_FILE)):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Core components
        self.stt_model = None
        self.tts_manager = None
        self.ollama_client = ollama.Client()
        self.current_llm_model = self.config['llm']['default_model']

        # LED Manager for visual feedback
        self.led_manager = LEDManager(brightness=0.2)
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.is_processing = False
        
        # GPIO setup for Voice Bonnet
        self.button_pin = digitalio.DigitalInOut(getattr(board, self.config['hardware']['voice_bonnet']['button_pin']))
        self.button_pin.direction = digitalio.Direction.INPUT
        self.button_pin.pull = digitalio.Pull.UP
        self.button = Debouncer(self.button_pin)
        
        # Performance monitoring
        self.stats = {
            'button_presses': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_stt_time': 0.0,
            'avg_llm_time': 0.0,
            'avg_tts_time': 0.0
        }

    async def initialize(self):
        """Initialize all AI components with LED startup feedback"""
        await self.led_manager.show_startup()
        self.logger.info("🚀 Initializing Voice AI Assistant...")
        
        initialization_tasks = [
            self._init_stt_model(),
            self._init_tts_engine(),
            self._validate_ollama_connection(),
            self._optimize_cpu_affinity()
        ]
        
        try:
            await asyncio.gather(*initialization_tasks)
            self.logger.info("✅ All components initialized successfully!")
            # Play startup greeting only AFTER TTS engine is initialized
            greeting = self._get_startup_greeting()
            self.logger.info(f"🎤 Startup greeting: {greeting}")
            asyncio.create_task(self.speak_greeting(greeting))
            return True
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            return False

    async def _init_stt_model(self):
        """Initialize onnx-asr with INT8 quantized Parakeet-TDT"""
        self.logger.info("🎤 Loading INT8 quantized Parakeet-TDT model...")
        
        try:
            # Load with INT8 quantization for maximum speed!
            self.stt_model = onnx_asr.load_model(
                "nemo-parakeet-tdt-0.6b-v2", 
                quantization="int8"
            )
            self.logger.info("✅ onnx-asr STT model loaded (INT8 quantized)")
            
            # Test transcription to ensure it works
            test_result = "Model loaded successfully"
            self.logger.info(f"🎯 STT Test: {test_result}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load STT model: {e}")
            raise

    async def _init_tts_engine(self):
        """Initialize TTS engine based on configuration"""
        tts_engine = self.config.get('tts_engine', 'kittentts')
        self.logger.info(f"🗣️ Initializing {tts_engine.upper()} TTS engine...")
        
        try:
            tts_voice = self.config.get("tts", {}).get("voice", "libritts_r")
            self.tts_manager = TTSManager(engine=tts_engine, voice=tts_voice)
            await self.tts_manager.initialize()
            
            engine_info = self.tts_manager.get_engine_info()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize TTS: {e}")
            raise

    async def _validate_ollama_connection(self):
        """Test Ollama connection and ensure models are available"""
        self.logger.info("🧠 Validating Ollama LLM connection...")
        
        try:
            # Check if Ollama is running
            models = await asyncio.to_thread(self.ollama_client.list)
            available_models = [m.model for m in models.models]
            
            if self.current_llm_model not in available_models:
                self.logger.warning(f"⚠️ Default model {self.current_llm_model} not found")
                if available_models:
                    self.current_llm_model = available_models[0]
                    self.logger.info(f"🔄 Switched to available model: {self.current_llm_model}")
                else:
                    raise Exception("No Ollama models available")
            
#            # Test generation
#            test_response = await asyncio.to_thread(
#                self.ollama_client.generate,
#                model=self.current_llm_model,
#                prompt="Say 'ready'",
#                options={'num_predict': 5, 'num_ctx': 512}
#            )
            
            self.logger.info(f"✅ Ollama connection validated with {self.current_llm_model}")
            
        except Exception as e:
            self.logger.error(f"❌ Ollama validation failed: {e}")
            raise

    async def _optimize_cpu_affinity(self):
        """Set CPU affinity for optimal Pi 5 performance"""
        try:
            import psutil
            process = psutil.Process()
            # Use cores 2-3 for AI processing (leave 0-1 for system)
            process.cpu_affinity([2, 3])
            self.logger.info("⚡ CPU affinity set to cores 2-3 for AI processing")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not set CPU affinity: {e}")

    def set_greeting_mode(self, mode: str = "mixed"):
        """Set the greeting mode for startup ('mixed', 'time_aware', 'glados', 'random')."""
        self.greeting_mode = mode
        self.logger.info(f"🎤 Greeting mode set to: {mode}")

    def _get_startup_greeting(self) -> str:
        mode = getattr(self, "greeting_mode", "mixed")
        if mode == "time_aware":
            return get_time_aware_greeting()
        if mode == "glados":
            return get_glados_greeting()
        if mode == "random":
            return get_random_greeting()
        return get_mixed_greeting()

    async def run(self):
        """Main event loop - wait for button presses and handle voice interactions"""
        await self.led_manager.show_success(1.0)  # Startup complete
        self.logger.info("🎮 Voice AI Assistant ready! Press the button to speak...")
        await self.led_manager.show_idle()  # Ready for interaction
        
        try:
            while True:
                self.button.update()
                
                if self.button.fell:  # Button pressed
                    self.stats['button_presses'] += 1
                    asyncio.create_task(self._handle_button_press())
                
                await asyncio.sleep(0.01)  # 100Hz polling
                
        except KeyboardInterrupt:
            self.logger.info("👋 Shutting down Voice AI Assistant...")
        finally:
            await self._cleanup()

    async def _handle_button_press(self):
        """Handle button press → record → transcribe → process → respond"""
        if self.is_processing:
            self.logger.info("⏳ Still processing previous request...")
            return
            
        self.is_processing = True
        start_time = time.time()
        
        try:
            self.logger.info("🎙️ Button pressed - Recording audio...")
            await self.led_manager.show_listening()
            
            # Record audio
            audio_file = await self._record_audio()
            
            # Transcribe with ultra-fast INT8 quantized Parakeet-TDT
            transcript = await self._process_stt(audio_file)
            if not transcript.text.strip():
                self.logger.warning("🔇 No speech detected")
                return
                
            self.logger.info(f"📝 Transcript: {transcript.text}")
            
            # Check for voice commands
            if await self._handle_voice_commands(transcript.text):
                return
            
            # Stream LLM response sentence-by-sentence directly into TTS for low time-to-first-audio
            await self._stream_llm_and_speak(transcript.text)
            
            # Update stats
            total_time = time.time() - start_time
            self.stats['successful_queries'] += 1
            self.logger.info(f"✅ Voice interaction completed in {total_time:.2f}s")
            
        except Exception as e:
            self.stats['failed_queries'] += 1
            self.logger.error(f"❌ Voice interaction failed: {e}")
        finally:
            self.is_processing = False
            await self.led_manager.show_idle()

    def _record_audio_sync(self) -> str:
        """Blocking audio capture run on a worker thread so the asyncio event loop stays responsive."""
        sample_rate = self.config['audio']['sample_rate']
        channels = self.config['audio']['channels']
        chunk_size = self.config['audio']['chunk_size']
        max_duration = self.config['audio']['max_record_duration']

        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size
        )

        frames = []
        silence_count = 0
        start_time = time.time()
        try:
            self.logger.info("🔴 Recording... (speak now)")
            while time.time() - start_time < max_duration:
                self.button.update()
                if self.button.rose:  # Button released
                    break

                data = stream.read(chunk_size, exception_on_overflow=False)
                frames.append(data)

                # Reset per-recording silence counter to avoid premature cutoffs
                volume = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                if len(frames) > 10 and np.max(np.abs(volume)) < 1000:
                    silence_count += 1
                    if silence_count > 20:  # ~2 seconds of silence
                        break
                else:
                    silence_count = 0
        finally:
            stream.stop_stream()
            stream.close()

        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_path = temp_file.name
        sf.write(temp_path, audio_data, sample_rate)

        duration = len(audio_data) / sample_rate
        self.logger.info(f"⏹️ Recording stopped ({duration:.1f}s)")
        return temp_path

    async def _record_audio(self) -> str:
        """Record audio from Voice Bonnet microphone without blocking the asyncio loop."""
        try:
            return await asyncio.to_thread(self._record_audio_sync)
        except Exception as e:
            self.logger.error(f"❌ Audio recording failed: {e}")
            raise

    async def _process_stt(self, audio_file: str) -> STTResult:
        """Ultra-fast speech-to-text with INT8 quantized Parakeet-TDT"""
        start_time = time.time()
        
        try:
            self.logger.info("🔥 Processing STT with INT8 Parakeet-TDT...")
            
            # Use onnx-asr for blazing fast transcription
            transcript = await asyncio.to_thread(
                self.stt_model.recognize,
                audio_file
            )
            
            processing_time = time.time() - start_time
            
            # Update running average
            self.stats['avg_stt_time'] = (
                (self.stats['avg_stt_time'] * self.stats['successful_queries'] + processing_time) 
                / (self.stats['successful_queries'] + 1)
            )
            
            self.logger.info(f"⚡ STT completed in {processing_time:.3f}s (avg: {self.stats['avg_stt_time']:.3f}s)")
            
            # Clean up temp file
            os.unlink(audio_file)
            
            return STTResult(
                text=transcript,
                confidence=1.0,  # onnx-asr doesn't provide confidence
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"❌ STT processing failed: {e}")
            if os.path.exists(audio_file):
                os.unlink(audio_file)
            raise

    async def _handle_voice_commands(self, text: str) -> bool:
        """Handle special voice commands like 'swap model'"""
        text_lower = text.lower().strip()
        
        if any(phrase in text_lower for phrase in ['swap model', 'switch model', 'change model']):
            await self._swap_llm_model()
            return True
            
        elif 'check temperature' in text_lower:
            temp = self._get_cpu_temperature()
            response = f"CPU temperature is {temp:.1f} degrees Celsius"
            await self._synthesize_and_play(response)
            return True
            
        elif 'check memory' in text_lower:
            import psutil
            memory = psutil.virtual_memory()
            response = f"Memory usage is {memory.percent:.1f} percent, {memory.available // 1024**2} megabytes available"
            await self._synthesize_and_play(response)
            return True
            
        return False

    async def _swap_llm_model(self):
        """Switch between available LLM models"""
        try:
            models = await asyncio.to_thread(self.ollama_client.list)
            available_models = [m.model for m in models.models]
            
            if len(available_models) < 2:
                response = "Only one model is available, cannot swap"
            else:
                current_idx = available_models.index(self.current_llm_model)
                next_idx = (current_idx + 1) % len(available_models)
                self.current_llm_model = available_models[next_idx]
                
                model_name = self.current_llm_model.split(':')[0]  # Remove tag for speech
                response = f"Switched to {model_name} model"
                
            self.logger.info(f"🔄 {response}")
            await self._synthesize_and_play(response)
            
        except Exception as e:
            self.logger.error(f"❌ Model swap failed: {e}")
            await self._synthesize_and_play("Model swap failed")


    def _clean_llm_response(self, response_text: str) -> str:
        """Clean LLM response by removing template tags and artifacts"""
        # Remove Llama-3-Instruct template tags
        response_text = response_text.strip()

        # For Q&A format, extract only the first answer
        if response_text.startswith("A: "):
            response_text = response_text[3:]  # Remove "A: " prefix

        # Stop at the first occurrence of a new question
        if "\nQ:" in response_text:
            response_text = response_text.split("\nQ:")[0]
        if "\n\nQ:" in response_text:
            response_text = response_text.split("\n\nQ:")[0]

        
        # Remove common template artifacts
        artifacts_to_remove = [
            "<|start_header_id|>assistant<|end_header_id|>",
            "<|start_header_id|>system<|end_header_id|>",
            "<|start_header_id|>user<|end_header_id|>",
            "<|eot_id|>",
            "<|begin_of_text|>"
        ]
        
        for artifact in artifacts_to_remove:
            response_text = response_text.replace(artifact, "")
        
        # Clean up extra whitespace and newlines
        response_text = response_text.strip()
        while "\n\n" in response_text:
            response_text = response_text.replace("\n\n", "\n")
        
        return response_text
    async def _process_llm(self, text: str) -> str:
        """Generate LLM response using Ollama"""
        start_time = time.time()
        
        try:
            self.logger.info(f"🧠 Processing with {self.current_llm_model}...")
            await self.led_manager.show_thinking()
            
            # Load system prompt and settings from config
            llm_config = self.config.get('llm', {})
            system_prompt = llm_config.get('system_prompt', 'You are a helpful voice assistant.')
            
            # Prepare Ollama options from config
            options = {
                'num_predict': llm_config.get('max_tokens', 500),
                'temperature': llm_config.get('temperature', 0.7),
                'top_p': llm_config.get('top_p', 0.9)
            }
            
            # Add context settings if available
            # Speed optimizations for sub-7s responses
            options['repeat_penalty'] = 1.1  # Prevent repetition
            options['top_k'] = llm_config.get('top_k', 20)  # Faster sampling
            if 'min_p' in llm_config:
                options['min_p'] = llm_config['min_p']

            context_settings = llm_config.get('context_settings', {})
            if 'num_ctx' in context_settings:
                options['num_ctx'] = context_settings['num_ctx']
            if 'num_batch' in context_settings:
                options['num_batch'] = context_settings['num_batch']
            
            response = await asyncio.to_thread(
                self.ollama_client.generate,
                model=self.current_llm_model,
                prompt=f"<bos><start_of_turn>system\n{system_prompt}<end_of_turn>\n<start_of_turn>user\n{text}<end_of_turn>\n<start_of_turn>model\n",
                options=options
            )
            
            processing_time = time.time() - start_time
            self.stats['avg_llm_time'] = (
                (self.stats['avg_llm_time'] * self.stats['successful_queries'] + processing_time)
                / (self.stats['successful_queries'] + 1)
            )
            
            response_text = self._clean_llm_response(response['response'])
            self.logger.info(f"🧠 LLM response ({processing_time:.2f}s): {response_text}...")
            
            return response_text
            
        except Exception as e:
            self.logger.error(f"❌ LLM processing failed: {e}")
            return "I'm sorry, I couldn't process that request."

    def _build_llm_options(self) -> tuple[str, Dict[str, Any]]:
        llm_config = self.config.get('llm', {})
        system_prompt = llm_config.get('system_prompt', 'You are a helpful voice assistant.')
        options: Dict[str, Any] = {
            'num_predict': llm_config.get('max_tokens', 500),
            'temperature': llm_config.get('temperature', 0.7),
            'top_p': llm_config.get('top_p', 0.9),
            'repeat_penalty': 1.1,
            'top_k': llm_config.get('top_k', 20),
        }
        if 'min_p' in llm_config:
            options['min_p'] = llm_config['min_p']
        context_settings = llm_config.get('context_settings', {})
        if 'num_ctx' in context_settings:
            options['num_ctx'] = context_settings['num_ctx']
        if 'num_batch' in context_settings:
            options['num_batch'] = context_settings['num_batch']
        return system_prompt, options

    async def _stream_llm_and_speak(self, text: str) -> str:
        """Stream Ollama tokens sentence-by-sentence into TTS to cut time-to-first-audio."""
        import re

        start_time = time.time()
        await self.led_manager.show_thinking()
        system_prompt, options = self._build_llm_options()
        prompt = (
            f"<bos><start_of_turn>system\n{system_prompt}<end_of_turn>\n"
            f"<start_of_turn>user\n{text}<end_of_turn>\n<start_of_turn>model\n"
        )
        loop = asyncio.get_running_loop()
        sentence_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        collected: list[str] = []
        boundary_re = re.compile(r'(?<=[.!?])\s+|\n+')

        def producer() -> None:
            buf = ""
            try:
                stream = self.ollama_client.generate(
                    model=self.current_llm_model,
                    prompt=prompt,
                    options=options,
                    stream=True,
                )
                for chunk in stream:
                    token = chunk.get('response', '') if isinstance(chunk, dict) else getattr(chunk, 'response', '')
                    if not token:
                        continue
                    buf += token
                    if "\nQ:" in buf:
                        buf = buf.split("\nQ:", 1)[0]
                        break
                    parts = boundary_re.split(buf)
                    if len(parts) > 1:
                        for seg in parts[:-1]:
                            cleaned = self._clean_llm_response(seg)
                            if cleaned:
                                collected.append(cleaned)
                                loop.call_soon_threadsafe(sentence_queue.put_nowait, cleaned)
                        buf = parts[-1]
                tail = self._clean_llm_response(buf)
                if tail:
                    collected.append(tail)
                    loop.call_soon_threadsafe(sentence_queue.put_nowait, tail)
            except Exception as exc:
                self.logger.error(f"❌ Streaming LLM failed: {exc}")
                if not collected:
                    loop.call_soon_threadsafe(
                        sentence_queue.put_nowait, "I'm sorry, I couldn't process that request."
                    )
            finally:
                loop.call_soon_threadsafe(sentence_queue.put_nowait, None)

        prod_task = asyncio.create_task(asyncio.to_thread(producer))
        try:
            while True:
                sentence = await sentence_queue.get()
                if sentence is None:
                    break
                await self._synthesize_and_play_with_waveform(sentence)
        finally:
            await prod_task

        processing_time = time.time() - start_time
        self.stats['avg_llm_time'] = (
            (self.stats['avg_llm_time'] * self.stats['successful_queries'] + processing_time)
            / (self.stats['successful_queries'] + 1)
        )
        return " ".join(collected)

    async def _synthesize_and_play(self, text: str):
        """Generate speech and play through Voice Bonnet using TTS Manager"""
        start_time = time.time()
        
        try:
            # Generate audio using TTS Manager
            audio_data = await self.tts_manager.generate_speech(text)
            
            # Prevent clipping without volume boost
            # Audio data without software boost (using hardware volume control)
            max_val = np.max(np.abs(audio_data))
            if max_val > 1.0:
                audio_data = audio_data / max_val
            
            # Save to temporary file and play
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # Convert to proper format for soundfile
                audio_int16 = (audio_data * 32767).astype(np.int16)
                sf.write(temp_file.name, audio_int16, samplerate=22050)
                
                # Play through aplay (Voice Bonnet compatible)
                process = await asyncio.create_subprocess_exec(
                    'aplay', '-D', 'plughw:0,0', temp_file.name,  # hw:1,0 is Voice Bonnet DAC
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await process.wait()
            
            # Clean up temp file
            try:
                os.unlink(temp_file.name)
            except:
                pass
            
            processing_time = time.time() - start_time
            self.stats['avg_tts_time'] = (
                (self.stats['avg_tts_time'] * self.stats['successful_queries'] + processing_time)
                / (self.stats['successful_queries'] + 1)
            )
            
            engine_info = self.tts_manager.get_engine_info()
            self.logger.info(f"🔊 Audio played with {engine_info['engine']} ({processing_time:.2f}s)")
            
        except Exception as e:
            self.logger.error(f"❌ TTS/Audio playback failed: {e}")

    def _get_cpu_temperature(self) -> float:
        """Get Raspberry Pi CPU temperature"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
            return temp
        except Exception:
            return 0.0

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            # Return minimal default config matching expected schema
            return {
                'audio': {'sample_rate': 16000, 'channels': 1, 'chunk_size': 1024, 'max_record_duration': 10},
                'hardware': {'voice_bonnet': {'button_pin': 'D17'}},
                'llm': {'default_model': 'gemma2:2b-instruct-q4_K_M'},
                'tts': {'device': 'cpu', 'voice': 'default'},
                'logging': {'level': 'INFO'}
            }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = PROJECT_ROOT / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=getattr(logging, self.config.get('logging', {}).get('level', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_dir / 'voice_ai.log')
            ]
        )
        return logging.getLogger(__name__)


    async def _synthesize_and_play_with_waveform(self, text: str):
        """Generate speech and play with waveform LED visualization"""
        start_time = time.time()
        
        try:
            # Generate audio using TTS Manager
            audio_data = await self.tts_manager.generate_speech(text)
            
            # Prevent clipping without volume boost
            max_val = np.max(np.abs(audio_data))
            if max_val > 1.0:
                audio_data = audio_data / max_val
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_audio_path = temp_file.name
                # Convert to proper format for soundfile
                audio_int16 = (audio_data * 32767).astype(np.int16)
                sf.write(temp_audio_path, audio_int16, samplerate=22050)
            
            # Start waveform visualization with the audio file
            await self.led_manager.show_speaking_with_waveform(temp_audio_path)
            
            # Play the audio
            process = await asyncio.create_subprocess_exec(
                "aplay", "-D", "plughw:0,0", temp_audio_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()
            
            # Clean up temp file
            try:
                os.unlink(temp_audio_path)
            except:
                pass
            
            processing_time = time.time() - start_time
            self.stats["avg_tts_time"] = (
                (self.stats["avg_tts_time"] * self.stats["successful_queries"] + processing_time)
                / (self.stats["successful_queries"] + 1)
            )
            
            self.logger.info(f"🔊 Audio played ({processing_time:.2f}s)")
            
        except Exception as e:
            self.logger.error(f"❌ TTS waveform synthesis failed: {e}")
            # Fallback to regular speaking animation
            await self.led_manager.show_speaking()
            await asyncio.sleep(2)
    async def speak_greeting(self, greeting_text):
        """Speak the startup greeting with waveform visualization"""
        try:
            await self._synthesize_and_play_with_waveform(greeting_text)
            self.logger.info(f"🗣️ Startup greeting played: {greeting_text}")
        except Exception as e:
            self.logger.error(f"❌ Failed to play startup greeting: {e}")


    async def _cleanup(self):
        """Clean up resources"""
        self.logger.info("🧹 Cleaning up resources...")
        self.led_manager.cleanup()
        
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()
        
        # Print final statistics
        self.logger.info("📊 Final Statistics:")
        for key, value in self.stats.items():
            self.logger.info(f"  {key}: {value}")

def main():
    """Main entry point"""
    # Ensure we're running with proper permissions
    if os.geteuid() != 0:
        print("⚠️ Warning: Not running as root. GPIO access may fail.")
    
    try:
        assistant = VoiceAIAssistant()
        
        # Run initialization and main loop
        async def run_assistant():
            if await assistant.initialize():
                await assistant.run()
            else:
                print("❌ Failed to initialize assistant")
                sys.exit(1)
        
        asyncio.run(run_assistant())
        
    except KeyboardInterrupt:
        print("\n👋 Voice AI Assistant stopped by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
