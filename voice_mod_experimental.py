#!/usr/bin/env python3
# voice_mod_experimental.py
# Low latency voice modulator with push-to-talk
import numpy as np
import sounddevice as sd
import sys
import select
import termios
import tty
from scipy import interpolate

# Ultra-low latency settings
SAMPLE_RATE = 48000
BLOCK_SIZE = 256  # Minimum for stability
PITCH_SHIFT = 3.0

# State
current_pitch = [PITCH_SHIFT]
robotic_enabled = [True]
push_to_talk_enabled = [False]  # Push-to-talk mode
is_talking = [False]  # Currently holding talk key

# Pre-compute carrier wave table for robotic effect (optimization)
carrier_table_size = 4800  # 100ms at 48kHz
carrier_table = np.sin(2 * np.pi * 95 * np.arange(carrier_table_size) / SAMPLE_RATE).astype(np.float32)
carrier_idx = [0]

def pitch_shift_fast(audio, semitones):
    """Fast pitch shift using frequency domain approach"""
    if abs(semitones) < 0.1:
        return audio
    
    # Calculate pitch ratio
    ratio = 2.0 ** (semitones / 12.0)
    
    # Use FFT to shift frequencies
    spectrum = np.fft.rfft(audio)
    freqs = np.fft.rfftfreq(len(audio), 1/SAMPLE_RATE)
    
    # Create new spectrum with shifted frequencies
    new_spectrum = np.zeros_like(spectrum)
    
    for i in range(len(spectrum)):
        # Calculate where this frequency should map to
        new_freq_idx = int(i / ratio)
        if 0 <= new_freq_idx < len(new_spectrum):
            new_spectrum[new_freq_idx] += spectrum[i]
    
    # Inverse FFT
    shifted = np.fft.irfft(new_spectrum, n=len(audio))
    
    # Normalize
    max_val = np.max(np.abs(shifted))
    if max_val > 0:
        shifted = shifted / max_val * np.max(np.abs(audio))
    
    return shifted.astype(np.float32)

def apply_robotic_effect(audio, intensity=0.7):
    """Apply robotic effect with pre-computed carrier"""
    global carrier_idx
    
    # Use pre-computed carrier wave for efficiency
    start_idx = carrier_idx[0]
    end_idx = start_idx + len(audio)
    
    # Wrap around if needed
    if end_idx <= carrier_table_size:
        carrier = carrier_table[start_idx:end_idx]
    else:
        carrier = np.concatenate([
            carrier_table[start_idx:],
            carrier_table[:end_idx - carrier_table_size]
        ])
    
    carrier_idx[0] = end_idx % carrier_table_size
    
    # Ring modulation
    modulated = audio * carrier * intensity + audio * (1 - intensity)
    
    # Bit reduction
    bits = 10
    modulated = np.round(modulated * (2 ** bits)) / (2 ** bits)
    
    # Soft clipping
    modulated = np.tanh(modulated * 1.2) * 0.9
    
    return modulated.astype(np.float32)

def audio_callback(indata, outdata, frames, time_info, status):
    """Real-time audio processing"""
    if status:
        pass  # Ignore status messages for performance
    
    # Get mono input
    mono = indata[:, 0] if indata.shape[1] > 1 else indata.flatten()
    
    # Check push-to-talk mode
    if push_to_talk_enabled[0] and not is_talking[0]:
        # Mute output when push-to-talk is enabled but key not held
        outdata[:, 0] = np.zeros(frames, dtype=np.float32)
        outdata[:, 1] = np.zeros(frames, dtype=np.float32)
        return
    
    try:
        # Pitch shift
        if abs(current_pitch[0]) > 0.1:
            shifted = pitch_shift_fast(mono, current_pitch[0])
            
            # Ensure correct length
            if len(shifted) > frames:
                shifted = shifted[:frames]
            elif len(shifted) < frames:
                shifted = np.pad(shifted, (0, frames - len(shifted)))
        else:
            shifted = mono
        
        # Apply robotic effect
        if robotic_enabled[0]:
            shifted = apply_robotic_effect(shifted, intensity=0.7)
        
        # Boost volume
        shifted = shifted * 2.2
        shifted = np.clip(shifted, -0.95, 0.95)
        
        # Output stereo
        outdata[:, 0] = shifted
        outdata[:, 1] = shifted
        
    except Exception as e:
        # Passthrough on error
        outdata[:, 0] = mono * 1.5
        outdata[:, 1] = mono * 1.5

def get_key():
    """Non-blocking keyboard input"""
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        if select.select([sys.stdin], [], [], 0.1)[0]:
            return sys.stdin.read(1)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    return None

def print_status():
    pitch = current_pitch[0]
    robot_status = "🤖 ON" if robotic_enabled[0] else "OFF"
    ptt_status = "PTT: ON" if push_to_talk_enabled[0] else "PTT: OFF"
    talk_status = " [TALKING]" if is_talking[0] else ""
    latency_ms = (BLOCK_SIZE / SAMPLE_RATE) * 1000 * 2.5
    print(f"\r🎤 Pitch: {pitch:+.1f} | Robot: {robot_status} | {ptt_status}{talk_status}     ", end='', flush=True)

def main():
    print("=== Voice Modulator with Push-to-Talk ===")
    print("Controls:")
    print("  ↑/+ : Increase pitch")
    print("  ↓/- : Decrease pitch")
    print("  r   : Toggle robotic effect")
    print("  p   : Toggle push-to-talk mode")
    print("  SPACE : Hold to talk (when PTT enabled)")
    print("  0   : Reset to +3 semitones")
    print("  q   : Quit")
    print("\nPush-to-talk: OFF by default (always transmitting)")
    print("Press 'p' to enable PTT, then hold SPACE to talk")
    print_status()
    
    try:
        with sd.Stream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=(1, 2),
            callback=audio_callback,
            latency=0.005,  # Request 5ms latency explicitly
            prime_output_buffers_using_stream_callback=False
        ):
            while True:
                key = get_key()
                
                if key:
                    if key == 'q':
                        print("\n\nStopping...")
                        break
                    elif key == 'r' or key == 'R':
                        robotic_enabled[0] = not robotic_enabled[0]
                        print_status()
                    elif key == 'p' or key == 'P':
                        push_to_talk_enabled[0] = not push_to_talk_enabled[0]
                        if not push_to_talk_enabled[0]:
                            is_talking[0] = False  # Reset talk state
                        print_status()
                    elif key == ' ':  # Spacebar
                        if push_to_talk_enabled[0]:
                            is_talking[0] = not is_talking[0]  # Toggle on space
                            print_status()
                    elif key == '+' or key == '=':
                        current_pitch[0] += 0.5
                        print_status()
                    elif key == '-' or key == '_':
                        current_pitch[0] -= 0.5
                        print_status()
                    elif key == '0':
                        current_pitch[0] = PITCH_SHIFT
                        print_status()
                    elif key == '\x1b':
                        next1 = get_key()
                        next2 = get_key()
                        if next1 == '[':
                            if next2 == 'A':
                                current_pitch[0] += 0.5
                                print_status()
                            elif next2 == 'B':
                                current_pitch[0] -= 0.5
                                print_status()
                
    except KeyboardInterrupt:
        print("\n\nStopping...")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
