import os
import time
import requests
import json

def test_end_to_end_workflow():
    # Path to a small test audio file (should exist in tests/fixtures/)
    audio_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'test.wav')
    assert os.path.exists(audio_path), f"Test audio file not found: {audio_path}"

    url = 'http://localhost:8000/upload-audio'
    with open(audio_path, 'rb') as f:
        files = {'file': ('test.wav', f, 'audio/wav')}
        resp = requests.post(url, files=files)
    assert resp.status_code == 200, f"Upload failed: {resp.text}"
    data = resp.json()
    transcription_id = data['transcription_id']

    # Wait for background processing (poll for up to 60s for JSON status)
    trans_json = os.path.join('transcriptions', transcription_id + '.json')
    md_file = None
    for _ in range(120):
        if os.path.exists(trans_json):
            with open(trans_json) as jf:
                meta = json.load(jf)
            if meta.get('status') == 'success' and meta.get('markdown_file'):
                md_file = os.path.join('markdowns', meta['markdown_file'])
                break
        time.sleep(1)
    assert md_file, "Transcription JSON did not reference a markdown file in time."
    # Now poll for the markdown file to appear (up to 30s)
    for _ in range(60):
        if os.path.exists(md_file):
            break
        time.sleep(0.5)
    assert os.path.exists(md_file), f"Markdown file not generated: {md_file}"
    print(f"Test passed: Markdown generated at {md_file}")

if __name__ == "__main__":
    test_end_to_end_workflow()
