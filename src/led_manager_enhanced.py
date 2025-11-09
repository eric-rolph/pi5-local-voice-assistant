#!/usr/bin/env python3
"""
LED Manager for Adafruit Voice Bonnet RGB DotStar LEDs
Provides visual feedback for voice AI states: listening, thinking, speaking
"""

import asyncio
import time
import math
import logging
from typing import Optional, Tuple
import numpy as np
import sounddevice as sd

try:
    import board
    import adafruit_dotstar
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("GPIO libraries not available - LED functionality disabled")

class LEDManager:
    """Manages the 3 RGB DotStar LEDs on the Adafruit Voice Bonnet"""
    
    def __init__(self, brightness: float = 0.3):
        self.logger = logging.getLogger(__name__)
        self.brightness = brightness
        self.dots = None
        self.current_animation_task = None
        self.thinking_stop_event = asyncio.Event()
        
        if GPIO_AVAILABLE:
            try:
                # Voice Bonnet DotStar LEDs: CLK=D6, DATA=D5, 3 LEDs
                self.dots = adafruit_dotstar.DotStar(
                    board.D6, board.D5, 3, 
                    brightness=brightness, 
                    auto_write=True
                )
                self.logger.info("✅ LED Manager initialized with 3 DotStar LEDs")
                self.clear_all()
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize LEDs: {e}")
                self.dots = None
        else:
            self.logger.warning("⚠️ GPIO not available - LED Manager running in simulation mode")

    def is_available(self) -> bool:
        """Check if LEDs are available"""
        return self.dots is not None

    def set_color(self, index: int, color: Tuple[int, int, int]):
        """Set color of a specific LED (0-2)"""
        if not self.is_available():
            return
        try:
            self.dots[index] = color
        except Exception as e:
            self.logger.error(f"Failed to set LED {index} color: {e}")

    def set_all(self, color: Tuple[int, int, int]):
        """Set all LEDs to the same color"""
        if not self.is_available():
            return
        try:
            self.dots[:] = [color] * 3
        except Exception as e:
            self.logger.error(f"Failed to set all LEDs: {e}")

    def clear_all(self):
        """Turn off all LEDs"""
        self.set_all((0, 0, 0))


    # Startup and Loading LED Methods
    async def show_startup(self):
        """Purple/magenta startup sequence"""
        await self._stop_current_animation()
        self.current_animation_task = asyncio.create_task(
            self._startup_animation()
        )
    
    async def show_loading(self, component_name: str = ""):
        """Orange loading animation for different components"""
        await self._stop_current_animation()
        self.current_animation_task = asyncio.create_task(
            self._loading_animation()
        )
    
    async def show_success(self, duration: float = 1.0):
        """Green success flash"""
        await self._stop_current_animation()
        # Brief green flash
        for i in range(3):
            self.set_color(i, (0, 255, 0))
        await asyncio.sleep(duration)
    
    async def _startup_animation(self):
        """Purple/magenta startup wave animation"""
        try:
            while True:
                t = time.time()
                
                for i in range(3):
                    # Create a wave that moves across the LEDs
                    phase = (t * 2) + (i * 2.0)  # 2 Hz with phase offset
                    intensity = (math.sin(phase) + 1) / 2
                    
                    # Purple/magenta gradient (startup color)
                    r = int(255 * intensity)
                    g = int(0 * intensity)
                    b = int(255 * intensity)
                    
                    self.set_color(i, (r, g, b))
                
                await asyncio.sleep(0.05)  # 20fps
        except asyncio.CancelledError:
            pass
    
    async def _loading_animation(self):
        """Orange loading spinner/pulse"""
        try:
            while True:
                t = time.time()
                
                # Create a rotating loading pattern
                for i in range(3):
                    angle = (t * 3) + (i * 2 * math.pi / 3)  # 3 Hz rotation
                    intensity = (math.sin(angle) + 1) / 2
                    intensity = max(0.2, intensity)  # Keep some minimum brightness
                    
                    # Orange loading color
                    r = int(255 * intensity)
                    g = int(165 * intensity)  # Orange = (255, 165, 0)
                    b = int(0 * intensity)
                    
                    self.set_color(i, (r, g, b))
                
                await asyncio.sleep(0.04)  # 25fps for smooth loading
        except asyncio.CancelledError:
            pass

    async def show_speaking_with_waveform(self, audio_file_path=None):
        """Enhanced speaking state with real-time waveform visualization"""
        await self._stop_current_animation()
        
        if audio_file_path and audio_file_path.endswith('.wav'):
            # Start waveform visualization for WAV file
            self.current_animation_task = asyncio.create_task(
                self._waveform_from_file(audio_file_path)
            )
        else:
            # Fallback to dynamic warm light animation
            self.current_animation_task = asyncio.create_task(
                self._dynamic_speaking_animation()
            )
    
    async def _waveform_from_file(self, wav_file):
        """Visualize waveform from WAV file"""
        try:
            import wave
            import numpy as np
            
            # Open WAV file
            with wave.open(wav_file, 'rb') as wf:
                frames = wf.readframes(-1)
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                
                # Convert to numpy array
                if wf.getsampwidth() == 2:
                    audio_data = np.frombuffer(frames, dtype=np.int16)
                else:
                    audio_data = np.frombuffer(frames, dtype=np.uint8)
                
                # Handle stereo
                if channels == 2:
                    audio_data = audio_data[::2]  # Take every other sample
                
                # Calculate chunk size for real-time playback
                chunk_size = int(sample_rate * 0.05)  # 50ms chunks
                total_chunks = len(audio_data) // chunk_size
                
                start_time = time.time()
                
                for i in range(total_chunks):
                    # Get current chunk
                    chunk_start = i * chunk_size
                    chunk_end = min(chunk_start + chunk_size, len(audio_data))
                    chunk = audio_data[chunk_start:chunk_end]
                    
                    # Calculate RMS amplitude
                    if len(chunk) > 0:
                        rms = np.sqrt(np.mean(chunk.astype(np.float32)**2))
                        amplitude = min(1.0, rms / 8000.0)  # Normalize
                    else:
                        amplitude = 0.0
                    
                    # Base warm color
                    base_color = (255, 200, 100)
                    
                    # Calculate brightness (30% to 100%)
                    brightness = 0.3 + (amplitude * 0.7)
                    
                    # Apply to all LEDs with wave effect
                    for led_idx in range(3):
                        # Add slight phase offset for wave effect
                        wave_phase = (time.time() * 3 + led_idx * 0.5) % (2 * math.pi)
                        wave_factor = 0.9 + 0.1 * math.sin(wave_phase)
                        
                        final_brightness = brightness * wave_factor
                        
                        r = int(base_color[0] * final_brightness)
                        g = int(base_color[1] * final_brightness) 
                        b = int(base_color[2] * final_brightness)
                        
                        # Clamp values
                        r = min(255, max(20, r))
                        g = min(255, max(15, g))
                        b = min(255, max(10, b))
                        
                        self.set_color(led_idx, (r, g, b))
                    
                    # Wait for real-time playback timing
                    expected_time = start_time + (i * 0.05)
                    current_time = time.time()
                    if current_time < expected_time:
                        await asyncio.sleep(expected_time - current_time)
                        
                    # Check if task was cancelled
                    if asyncio.current_task().cancelled():
                        break
                        
        except Exception as e:
            self.logger.warning(f"⚠️ Waveform visualization failed: {e}")
            # Fallback to dynamic animation
            await self._dynamic_speaking_animation()
    
    async def _dynamic_speaking_animation(self):
        """Dynamic warm light animation for speaking"""
        try:
            base_color = (255, 200, 100)  # Warm white
            
            while True:
                t = time.time()
                
                # Create a dynamic, speech-like brightness pattern
                # Combine multiple frequencies to simulate speech patterns
                primary = math.sin(t * 4) * 0.3       # Main speech rhythm
                secondary = math.sin(t * 7) * 0.2     # Higher frequency
                tertiary = math.sin(t * 11) * 0.1     # Even higher detail
                
                # Ensure always positive and in good range
                brightness = 0.5 + abs(primary + secondary + tertiary)
                brightness = min(1.0, max(0.3, brightness))
                
                # Apply to each LED with slight phase differences
                for i in range(3):
                    # Add per-LED variation
                    led_phase = i * 0.3
                    led_brightness = brightness * (0.9 + 0.1 * math.sin(t * 2 + led_phase))
                    
                    r = int(base_color[0] * led_brightness)
                    g = int(base_color[1] * led_brightness)
                    b = int(base_color[2] * led_brightness)
                    
                    # Ensure minimum visibility
                    r = max(30, r)
                    g = max(20, g)  
                    b = max(10, b)
                    
                    self.set_color(i, (r, g, b))
                
                await asyncio.sleep(0.03)  # ~30fps for smooth animation
                
        except asyncio.CancelledError:
            pass


    def cleanup(self):
        """Cleanup - turn off LEDs"""
        if self.current_animation_task:
            self.current_animation_task.cancel()
        self.clear_all()

    # === STATE INDICATORS ===

    async def show_idle(self):
        """Show idle state - soft breathing blue"""
        if not self.is_available():
            return
            
        await self._stop_current_animation()
        self.current_animation_task = asyncio.create_task(self._breathing_animation((0, 50, 100)))

    async def show_listening(self):
        """Show listening state - steady cyan"""
        if not self.is_available():
            return
            
        await self._stop_current_animation()
        self.set_all((30, 120, 120))

    async def show_thinking(self):
        """Show thinking/LLM processing - blue spinner animation"""
        if not self.is_available():
            return
            
        await self._stop_current_animation()
        self.thinking_stop_event.clear()
        self.current_animation_task = asyncio.create_task(self._thinking_spinner())

    async def show_speaking(self):
        """Show speaking state - warm white"""
        if not self.is_available():
            return
            
        await self._stop_current_animation()
        self.set_all((255, 160, 60))  # Warm white

    async def show_audio_visualization(self, duration_ms: int = 100):
        """Show real-time audio visualization during recording"""
        if not self.is_available():
            return
            
        await self._stop_current_animation()
        self.current_animation_task = asyncio.create_task(self._audio_viz_loop(duration_ms))

    # === PRIVATE ANIMATION METHODS ===

    async def _stop_current_animation(self):
        """Stop any running animation"""
        if self.current_animation_task and not self.current_animation_task.done():
            self.current_animation_task.cancel()
            try:
                await self.current_animation_task
            except asyncio.CancelledError:
                pass
        self.thinking_stop_event.set()

    async def _breathing_animation(self, base_color: Tuple[int, int, int]):
        """Soft breathing animation"""
        try:
            while True:
                for i in range(100):
                    # Sine wave breathing effect
                    intensity = (math.sin(i * 0.1) + 1) / 2  # 0 to 1
                    color = tuple(int(c * intensity * 0.5) for c in base_color)
                    self.set_all(color)
                    await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            self.clear_all()

    async def _thinking_spinner(self):
        """Blue spinner animation for thinking state"""
        try:
            i = 0
            colors = [(0, 0, 120), (0, 0, 60), (0, 0, 20)]
            while not self.thinking_stop_event.is_set():
                self.clear_all()
                for j, intensity in enumerate([120, 60, 20]):
                    led_index = (i + j) % 3
                    self.set_color(led_index, (0, 0, intensity))
                i += 1
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            self.clear_all()

    async def _audio_viz_loop(self, duration_ms: int):
        """Real-time audio visualization"""
        try:
            viz = AudioVisualizer()
            with viz:
                end_time = time.time() + (duration_ms / 1000.0)
                while time.time() < end_time:
                    level = viz.get_audio_level()
                    self._display_audio_level(level)
                    await asyncio.sleep(0.03)  # ~33 FPS
        except Exception as e:
            self.logger.error(f"Audio visualization error: {e}")
        finally:
            self.clear_all()

    def _display_audio_level(self, level: float):
        """Display audio level as VU meter (0.0 to 1.0)"""
        if not self.is_available():
            return
            
        # Calculate number of LEDs to light based on level
        num_leds = min(3, max(0, int(level * 4)))  # 0 to 3 LEDs
        
        # Color progression: green -> yellow -> red
        if level < 0.3:
            color = (0, int(255 * level * 3), 0)  # Green
        elif level < 0.7:
            color = (int(255 * (level - 0.3) * 2.5), 255, 0)  # Yellow
        else:
            color = (255, int(255 * (1 - level) * 2.5), 0)  # Red

        # Light up LEDs based on level
        self.clear_all()
        for i in range(num_leds):
            brightness_multiplier = 1.0 - (i * 0.2)  # Fade effect
            fade_color = tuple(int(c * brightness_multiplier) for c in color)
            self.set_color(i, fade_color)


class AudioVisualizer:
    """Real-time audio level analyzer for LED visualization"""
    
    def __init__(self, samplerate: int = 16000, block_ms: int = 30):
        self.samplerate = samplerate
        self.blocksize = int(samplerate * block_ms / 1000)
        self.stream = None
        self.current_level = 0.0
        
    def __enter__(self):
        try:
            self.stream = sd.InputStream(
                channels=1,
                samplerate=self.samplerate,
                blocksize=self.blocksize,
                dtype='int16'
            )
            self.stream.__enter__()
            return self
        except Exception as e:
            logging.error(f"Failed to initialize audio stream: {e}")
            self.stream = None
            return self
            
    def __exit__(self, *args):
        if self.stream:
            self.stream.__exit__(*args)
    
    def get_audio_level(self) -> float:
        """Get current audio level (0.0 to 1.0)"""
        if not self.stream:
            return 0.0
            
        try:
            audio_data, _ = self.stream.read(self.blocksize)
            if len(audio_data) == 0:
                return self.current_level
                
            # Convert to float and calculate RMS
            audio_float = audio_data.astype(np.float32).flatten()
            rms = np.sqrt(np.mean(audio_float ** 2)) / 32768.0
            
            # Smooth the level with simple low-pass filtering
            target_level = min(1.0, rms * 8.0)  # Scale and clamp
            self.current_level = 0.7 * self.current_level + 0.3 * target_level
            
            return self.current_level
            
        except Exception as e:
            logging.error(f"Error reading audio: {e}")
            return self.current_level


# === TESTING CODE ===
async def demo_led_states():
    """Demo all LED states"""
    led_manager = LEDManager()
    
    if not led_manager.is_available():
        print("❌ LEDs not available - check hardware connection")
        return
    
    print("🎯 LED Demo Starting...")
    
    # Idle breathing
    print("💤 Idle state (breathing blue)")
    await led_manager.show_idle()
    await asyncio.sleep(3)
    
    # Listening
    print("👂 Listening state (cyan)")
    await led_manager.show_listening()
    await asyncio.sleep(2)
    
    # Audio visualization
    print("��️ Audio visualization (3 seconds)")
    await led_manager.show_audio_visualization(3000)
    
    # Thinking
    print("🧠 Thinking state (blue spinner)")
    await led_manager.show_thinking()
    await asyncio.sleep(3)
    
    # Speaking
    print("🗣️ Speaking state (warm white)")
    await led_manager.show_speaking()
    await asyncio.sleep(2)
    
    # Cleanup
    led_manager.cleanup()
    print("✅ Demo complete")


if __name__ == "__main__":
    asyncio.run(demo_led_states())
