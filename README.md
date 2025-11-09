# 🤖 Local Voice AI Assistant for Raspberry Pi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Raspberry Pi 5](https://img.shields.io/badge/Raspberry%20Pi-5-red.svg)](https://www.raspberrypi.com/)

A privacy-first, fully local voice AI assistant powered by Raspberry Pi 5. All processing happens on-device with support for multiple voice personalities and customizable responses—no cloud dependencies required.

## 🎥 See It In Action

[![Voice Assistant Demo](https://img.youtube.com/vi/ga9IAmZrm20/maxresdefault.jpg)](https://www.youtube.com/shorts/ga9IAmZrm20)

**Watch the demo:** [YouTube Shorts](https://www.youtube.com/shorts/ga9IAmZrm20) - See the assistant responding with RGB LED feedback!

## ✨ Features

### � Multiple Voice Options
- **Customizable voice personalities** with 161+ unique greeting variations
- **Multiple TTS voices available**: LibriTTS-R (neutral), Lessac (professional), robot-style, and more
- **Time-aware greetings** that adapt to the time of day
- **Configurable response styles** to match your preferences

### 🔒 Privacy-First Design
- **100% local processing** - No cloud dependencies
- **On-device STT** using ONNX ASR with INT8 quantized Parakeet-TDT
- **Local LLM** via Ollama (Gemma 2 2B recommended)
- **Local TTS** with Piper or KittenTTS engines

### 🎨 Visual Feedback
- **6 distinct LED states** using Adafruit Voice Bonnet's RGB DotStar LEDs:
  - 🟣 Purple wave - Startup sequence
  - 🟠 Orange spinner - Loading models
  - 🟢 Green flashes - Success/ready
  - 🔵 Blue breathing - Idle (waiting for input)
  - 🔆 Cyan - Listening to voice
  - 🟡 Yellow - Thinking/processing
- **Real-time waveform visualization** during speech output

### ⚡ High Performance
- **Ultra-fast STT**: INT8 quantized Parakeet-TDT (7.77x realtime)
- **Optimized for Pi 5**: CPU affinity, async architecture
- **Responsive**: Sub-second processing for most queries
- **Memory efficient**: Quantized models for 4-8GB systems

## 🔧 Hardware Requirements

### Required
- **Raspberry Pi 5** (4GB RAM minimum, 8GB recommended)
- **Adafruit Voice Bonnet** with:
  - Stereo microphone
  - 3W stereo amplifier
  - 3x RGB DotStar LEDs
  - Push button for voice activation
- **MicroSD Card** 64GB+ (Class 10 or better)
- **Power Supply** Official Raspberry Pi 5 USB-C (27W recommended)

### Optional
- **Speaker(s)** 4-8Ω for audio output
- **Cooling** Active cooling recommended for sustained AI workloads

## 📦 Installation

### Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/eric-rolph/pi5-local-voice-assistant.git
cd pi5-local-voice-assistant

# Run the automated installer
chmod +x install.sh
./install.sh

# The installer will:
# 1. Create a virtual environment
# 2. Install all Python dependencies
# 3. Set up Ollama and download LLM models
# 4. Configure Piper TTS with voice model
# 5. Set up system services (optional)
```

### Manual Installation

<details>
<summary>Click to expand manual installation steps</summary>

#### 1. System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv git portaudio19-dev \
    build-essential cmake libopenblas-dev libasound2-dev
```

#### 2. Python Environment

```bash
# Create virtual environment
python3 -m venv voice_ai_env
source voice_ai_env/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Ollama LLM Setup

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download recommended model (Gemma 2 2B - optimized for Pi 5)
ollama pull gemma2:2b-instruct-q4_0

# Optional: Download larger model for better responses
ollama pull gemma3-fixed:latest
```

#### 4. Piper TTS Setup

```bash
# Piper is installed via pip, but you need to download voice models
mkdir -p models/piper
cd models/piper

# Download your preferred voice model (examples):

# Option 1: LibriTTS-R (high-quality neutral voice) - RECOMMENDED
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx.json

# Option 2: Lessac (professional female voice)
# wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
# wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Option 3: robot-style voice (Portal character)
# wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/glados/medium/glados.onnx
# wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/glados/medium/glados.onnx.json

cd ../..
```

#### 5. Configuration

```bash
# Copy the secrets template
cp config/secrets.py.example config/secrets.py

# Edit config/secrets.py if you need WiFi or API integration
# (Optional - all features work locally without any credentials)
nano config/secrets.py

# Review and customize voice_ai_config.yaml if needed
nano config/voice_ai_config.yaml
```

</details>

## 🚀 Usage

### Basic Usage

```bash
# Activate virtual environment
source voice_ai_env/bin/activate

# Run the assistant
python src/voice_ai_assistant.py
```

The assistant will:
1. Show startup LED sequence (purple wave)
2. Load models (orange spinner)
3. Greet you with a personalized phrase
4. Enter idle mode (blue breathing)
5. Wait for button press to start listening

### Voice Interaction

1. **Press the button** - LEDs turn cyan (listening)
2. **Speak your question** - Hold button or speak for up to 10 seconds
3. **Release button** - Yellow LEDs (processing)
4. **Hear response** - Waveform visualization during speech playback

### Voice Commands

- **"Swap model"** / **"Switch model"** - Toggle between available LLM models
- **"Check temperature"** - Get Raspberry Pi CPU temperature
- **"Check memory"** - Get memory usage statistics

### Running as a Service (Optional)

<details>
<summary>Click to expand systemd service setup</summary>

```bash
# Create service file
sudo nano /etc/systemd/system/voice-assistant.service
```

Add the following content:

```ini
[Unit]
Description=Local Voice Assistant
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pi5-local-voice-assistant
ExecStart=/home/pi/pi5-local-voice-assistant/voice_ai_env/bin/python /home/pi/pi5-local-voice-assistant/src/voice_ai_assistant.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable voice-assistant
sudo systemctl start voice-assistant

# Check status
sudo systemctl status voice-assistant

# View logs
journalctl -u voice-assistant -f
```

</details>

## ⚙️ Configuration

### Main Configuration (`config/voice_ai_config.yaml`)

Key settings you may want to customize:

```yaml
# LLM Settings
llm:
  default_model: "gemma2:2b-instruct-q4_0"  # Fast, efficient
  large_model: "gemma3-fixed:latest"         # Better quality
  system_prompt: "You are a helpful voice assistant..."
  max_tokens: 500
  temperature: 0.1

# TTS Settings
tts:
  voice: "libritts_r"  # Options: libritts_r, lessac, glados
  speed: 1.0
  volume: 0.8

# Audio Settings
audio:
  sample_rate: 22050
  max_record_duration: 10

# Hardware
hardware:
  voice_bonnet:
    button_pin: "D17"
    audio_device: "plughw:0,0"
```

### Secrets Configuration (`config/secrets.py`)

⚠️ **Security Note**: Copy `secrets.py.example` to `secrets.py` and add your credentials. This file is in `.gitignore` and will never be committed.

```python
secrets = {
    "ssid": "",           # Optional WiFi
    "password": "",       # Optional WiFi password
    "timezone": "UTC",    # Your timezone
}
```

## 📊 Performance

Typical response times on Raspberry Pi 5 (8GB):

| Stage | Time | Notes |
|-------|------|-------|
| STT (Speech Recognition) | 0.3-0.8s | INT8 Parakeet-TDT |
| LLM (Response Generation) | 2-5s | Gemma 2 2B Q4_0 |
| TTS (Speech Synthesis) | 1-2s | Piper TTS |
| **Total** | **3.5-7.5s** | End-to-end response |

## 🎓 Project Structure

```
pi5-local-voice-assistant/
├── src/
│   ├── voice_ai_assistant.py      # Main application
│   ├── tts_manager.py              # Text-to-speech management
│   ├── led_manager_enhanced.py     # LED control system
│   └── greeting_phrases.py         # 161+ greeting variations
├── config/
│   ├── voice_ai_config.yaml        # Main configuration
│   ├── secrets.py.example          # Credentials template
│   └── secrets.py                  # Your credentials (not in git)
├── models/
│   └── piper/
│       ├── *.onnx                 # TTS voice models
│       └── *.onnx.json            # Voice configs
├── logs/
│   └── voice_ai.log               # Application logs
├── docs/
│   ├── HARDWARE_SETUP.md          # Hardware assembly guide
│   ├── TROUBLESHOOTING.md         # Common issues & fixes
│   └── CUSTOMIZATION.md           # Customization guide
├── requirements.txt               # Python dependencies
├── install.sh                     # Automated installer
├── .gitignore                     # Git ignore rules
├── LICENSE                        # MIT License
├── SECURITY.md                    # Security policy
└── README.md                      # This file
```

## 🔍 Troubleshooting

### Common Issues

<details>
<summary><b>LEDs not working</b></summary>

- Check GPIO connections (CLK=D6, DATA=D5)
- Ensure you're running with proper permissions
- Try running with `sudo` for testing
- Check `sudo dmesg | grep spi` for SPI issues
</details>

<details>
<summary><b>Button not responding</b></summary>

- Verify button is connected to GPIO17 (D17)
- Check button wiring (pull-up resistor)
- Test button with: `gpio readall` command
</details>

<details>
<summary><b>No audio output</b></summary>

- Check speaker connections
- Test audio: `aplay -D plughw:0,0 /usr/share/sounds/alsa/Front_Center.wav`
- Verify audio device in config: `aplay -l`
- Adjust volume: `alsamixer`
</details>

<details>
<summary><b>Slow STT processing</b></summary>

- Ensure INT8 quantization is enabled
- Check CPU temperature: `vcgencmd measure_temp`
- Verify CPU affinity settings in config
- Consider active cooling if throttling
</details>

<details>
<summary><b>Ollama connection failed</b></summary>

- Check if Ollama is running: `systemctl status ollama`
- Start Ollama: `sudo systemctl start ollama`
- Verify models: `ollama list`
- Check logs: `journalctl -u ollama -f`
</details>

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more detailed solutions.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
# Clone and create dev branch
git clone https://github.com/eric-rolph/pi5-local-voice-assistant.git
cd pi5-local-voice-assistant
git checkout -b feature/your-feature

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Submit PR when ready
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Piper TTS** - Neural text-to-speech by Rhasspy
- **ONNX ASR** - Fast speech recognition
- **Ollama** - Local LLM inference
- **Adafruit** - Voice Bonnet hardware
- Voice models from the open-source community

## 🔐 Security

This project prioritizes privacy and security:
- ✅ All processing happens locally
- ✅ No telemetry or analytics
- ✅ No cloud API calls required
- ✅ Credentials never committed to git

See [SECURITY.md](SECURITY.md) for our security policy and how to report vulnerabilities.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/eric-rolph/pi5-local-voice-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/eric-rolph/pi5-local-voice-assistant/discussions)
- **Documentation**: [docs/](docs/)

## 🗺️ Roadmap

- [ ] Multi-language support
- [ ] Wake word detection (hands-free mode)
- [ ] Mobile app for remote control
- [ ] Additional voice personalities
- [ ] Smart home integration
- [ ] Conversation history/context
- [ ] Voice command macros

---

**Made with ❤️ for privacy-conscious AI enthusiasts**

*Complete privacy, local processing, customizable voices.*
