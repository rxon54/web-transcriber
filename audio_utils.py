import subprocess
import tempfile
import os
import json

def convert_audio_ffmpeg(input_bytes: bytes, input_format: str, output_format: str = "wav", sample_width: int = 2, channels: int = 1, frame_rate: int = 16000) -> bytes:
    """
    Convert audio bytes to the desired format and parameters using ffmpeg.
    Default: 16-bit WAV, mono, 16kHz.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{input_format}') as in_file:
        in_file.write(input_bytes)
        in_file.flush()
        in_path = in_file.name
    out_path = in_path + f'.converted.{output_format}'
    cmd = [
        'ffmpeg', '-y', '-i', in_path,
        '-ar', str(frame_rate), '-ac', str(channels), '-sample_fmt', 's16',
        out_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        with open(out_path, 'rb') as f:
            out_bytes = f.read()
    finally:
        os.remove(in_path)
        if os.path.exists(out_path):
            os.remove(out_path)
    return out_bytes

def get_audio_duration_ffprobe(input_bytes: bytes, input_format: str) -> float:
    """
    Get audio duration in seconds using ffprobe.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{input_format}') as in_file:
        in_file.write(input_bytes)
        in_file.flush()
        in_path = in_file.name
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', in_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
    finally:
        os.remove(in_path)
    return duration
