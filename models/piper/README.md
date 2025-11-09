# Piper TTS Voice Models

This directory contains ONNX voice models for the Piper TTS engine.

## GLaDOS Voice Model

The GLaDOS voice model is required for authentic Portal-style text-to-speech.

### Download Instructions

```bash
# Navigate to this directory
cd models/piper

# Download GLaDOS voice model and config
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/glados/medium/glados.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/glados/medium/glados.onnx.json
```

### Alternative Voices

You can also download other voices if you prefer:

#### LibriTTS-R (High-quality neutral voice)
```bash
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx.json
```

#### Lessac (Professional female voice)
```bash
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

## Model Information

- **Format**: ONNX (Open Neural Network Exchange)
- **Size**: ~60MB per voice model
- **Quality**: Medium quality (optimal for Raspberry Pi 5)
- **License**: Creative Commons licenses (see individual model pages)

## Using Different Voices

To change the voice, edit `config/voice_ai_config.yaml`:

```yaml
tts:
  voice: "glados"  # Options: glados, libritts_r, lessac
```

## Note

These models are **NOT included in the git repository** due to their size. They must be downloaded separately during installation.

The `.gitignore` file excludes `*.onnx` files from version control.
