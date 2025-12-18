# Omega Voice Modulator

A real-time voice modulator with robotic effects and pitch shifting, optimized for low latency and high quality. Built for live voice applications with interactive controls.

## Project Structure

```
omega-voice/
├── voice_mod_low_latency.py      # Ultra-low latency version (~13ms)
├── voice_mod_high_quality.py     # High quality version (~50ms)
├── voice_mod_separate_devices.py # Separate input/output devices
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── DEVELOPMENT.md                # Development guide
```

## Features

- **Real-time pitch shifting** using FFT frequency domain processing
- **Robotic voice effect** with ring modulation and bit crushing
- **Interactive controls** for live pitch adjustment
- **Multiple versions** optimized for latency vs quality
- **Separate device support** for headphones mic + laptop speakers
- **Sub-100ms latency** in low-latency mode

## Prerequisites

### System Dependencies

None required! The modulator uses only Python libraries.

### Python Requirements

- Python 3.8+
- numpy
- sounddevice
- scipy (for interpolation)

See `requirements.txt` for complete list.

## Installation & Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install Python dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Make scripts executable (optional):
   ```bash
   chmod +x voice_mod_*.py
   ```

## Usage

### Choose Your Version

#### 1. Low Latency Version (Recommended for responsiveness)
```bash
.venv/bin/python voice_mod_low_latency.py
```
- **Latency:** ~13ms
- **Block size:** 256 samples
- **Best for:** Gaming, live streaming, instant response

#### 2. High Quality Version (Recommended for recording)
```bash
.venv/bin/python voice_mod_high_quality.py
```
- **Latency:** ~50-60ms
- **Block size:** 1024 samples  
- **Best for:** Recording, quality-critical applications

#### 3. Separate Devices Version (Recommended to avoid feedback)
```bash
.venv/bin/python voice_mod_separate_devices.py
```
- **Input:** Headphones microphone
- **Output:** Laptop speakers
- **Best for:** Avoiding acoustic feedback when not using headphones

### Interactive Controls

All versions support the same controls:

- **↑ or +** : Increase pitch (+0.5 semitones)
- **↓ or -** : Decrease pitch (-0.5 semitones)
- **r** : Toggle robotic effect ON/OFF
- **0** : Reset to default (+3.0 semitones)
- **q** : Quit

### Default Settings

- **Pitch:** +3.0 semitones (higher voice)
- **Robotic effect:** ON
- **Sample rate:** 48000 Hz
- **Channels:** Mono input, Stereo output

## Audio Routing

To use this in Discord, Zoom, OBS, or other applications, you need to route the processed audio as a virtual microphone input.

### macOS: BlackHole

1. Install [BlackHole](https://github.com/ExistentialAudio/BlackHole)
2. Create a multi-output device in Audio MIDI Setup:
   - Microphone → App Input → BlackHole → System/Discord
3. In Discord/Zoom: Select BlackHole as your microphone device

### Windows: VB-Cable or Voicemeeter

1. Install [VB-Cable](https://vb-audio.com/Cable/) or [Voicemeeter](https://vb-audio.com/Voicemeeter/)
2. Route the application output to the virtual cable input
3. In Discord/Zoom: Select the virtual cable as your microphone device

## Configuration

Edit the Python files to customize:

### In any version:

- **PITCH_SHIFT**: Default pitch in semitones (default: 3.0)
- **SAMPLE_RATE**: Audio sample rate (default: 48000)
- **robotic_enabled**: Start with robotic effect on/off (default: True)

### In `voice_mod_separate_devices.py`:

- **INPUT_DEVICE**: Audio input device ID
- **OUTPUT_DEVICE**: Audio output device ID

Run this to see available devices:
```bash
.venv/bin/python -c "import sounddevice as sd; print(sd.query_devices())"
```

### Latency vs Quality Trade-off:

- **Lower BLOCK_SIZE** = Lower latency, more CPU, possible artifacts
- **Higher BLOCK_SIZE** = Higher latency, less CPU, cleaner audio

## Troubleshooting

### Poor quality without headphones
**Cause:** Acoustic feedback - your mic picks up the output from speakers.

**Solution:** Use one of these:
1. Wear headphones (simplest)
2. Use `voice_mod_separate_devices.py` with headphones mic + laptop speakers
3. Lower the output volume

### Audio underflow/overflow warnings
**Cause:** CPU can't keep up with real-time processing.

**Solution:**
- Use `voice_mod_high_quality.py` (larger block size)
- Close other CPU-intensive applications
- Reduce pitch shift amount (closer to 0 = faster)

### High latency with Bluetooth
**Cause:** Bluetooth audio has inherent 100-200ms latency.

**Solution:**
- Use wired headphones or built-in mic/speakers
- The modulator itself adds only 13-60ms depending on version

### No audio output
**Cause:** Wrong device selected or volume too low.

**Solution:**
1. Check system audio settings
2. Increase volume (the modulator boosts by 2.2x)
3. Try different version (especially `voice_mod_separate_devices.py`)

### Module import errors
**Cause:** Dependencies not installed.

**Solution:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## How It Works

### Pitch Shifting Algorithm

1. **FFT Transform**: Convert time-domain audio to frequency domain
2. **Frequency Shifting**: Redistribute frequency bins based on pitch ratio
3. **IFFT Transform**: Convert back to time-domain audio
4. **Normalization**: Maintain consistent volume levels

### Robotic Effect

1. **Ring Modulation**: Multiply audio with 95Hz sine wave carrier
2. **Bit Crushing**: Reduce bit depth to 10-bits for digital character
3. **Soft Clipping**: Apply tanh compression for warmth

### Latency Breakdown

- **Audio buffer:** 5-21ms (depending on block size)
- **Processing:** 2-10ms (FFT + effects)
- **System overhead:** 5-10ms (OS audio driver)
- **Total:** 13-60ms (well within acceptable range for live use)

## Technical Details

- **Architecture:** Duplex audio stream (simultaneous input/output)
- **Pitch method:** Frequency-domain resampling (no tempo change)
- **Sample format:** 32-bit float
- **Channels:** Mono in, Stereo out
- **Optimization:** Pre-computed carrier wave tables

## License

Open source - feel free to modify and experiment!

## Credits

Built with:
- [NumPy](https://numpy.org/) - Fast array operations and FFT
- [sounddevice](https://python-sounddevice.readthedocs.io/) - Real-time audio I/O
- [SciPy](https://scipy.org/) - Scientific computing utilities

## See Also

- **DEVELOPMENT.md** - Technical guide for developers
- **requirements.txt** - Python dependencies
