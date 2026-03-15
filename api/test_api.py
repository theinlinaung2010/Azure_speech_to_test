"""
Command-line test script for Azure Speech API
"""

import requests
import json
import sys
from pathlib import Path

API_URL = "http://localhost:3333"


def test_health():
    """Test API health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/api/health")
        data = response.json()
        print(f"✅ Health check: {data['status']}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_upload(file_path):
    """Test file upload"""
    print(f"\nUploading file: {file_path}")

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return None

    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{API_URL}/api/upload", files=files)

        if response.status_code == 200:
            data = response.json()
            job_id = data["job_id"]
            print(f"✅ Upload successful!")
            print(f"   Job ID: {job_id}")
            print(f"   Filename: {data['filename']}")
            return job_id
        else:
            print(f"❌ Upload failed: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None


def test_status(job_id):
    """Test status endpoint"""
    print(f"\nChecking job status: {job_id}")
    try:
        response = requests.get(f"{API_URL}/api/status/{job_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"   Created: {data['created_at']}")
            if data.get("completed_at"):
                print(f"   Completed: {data['completed_at']}")
            return data
        else:
            print(f"❌ Status check failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Status error: {e}")
        return None


def stream_transcription(job_id, output_file=None):
    """Stream transcription events"""
    print(f"\nStreaming transcription for job: {job_id}")
    print("=" * 60)

    url = f"{API_URL}/api/stream/{job_id}"
    transcription = []

    try:
        response = requests.get(url, stream=True)

        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data_json = line[6:]  # Remove 'data: ' prefix
                    try:
                        event = json.loads(data_json)

                        if event["type"] == "connected":
                            print(f"✅ Connected to stream\n")

                        elif event["type"] == "started":
                            print("🎤 Transcription started...\n")

                        elif event["type"] == "segment":
                            timestamp = event["timestamp"]
                            text = event["text"]
                            print(f"{timestamp}")
                            print(f"{text}\n")
                            transcription.append(f"{timestamp}\n{text}\n")

                        elif event["type"] == "completed":
                            print("=" * 60)
                            print("✅ Transcription completed!")

                            if output_file:
                                with open(output_file, "w", encoding="utf-8") as f:
                                    f.writelines(transcription)
                                print(f"📝 Saved to: {output_file}")
                            break

                        elif event["type"] == "error":
                            print(f"❌ Error: {event.get('message', 'Unknown error')}")
                            break

                    except json.JSONDecodeError:
                        pass

    except Exception as e:
        print(f"❌ Streaming error: {e}")


def download_transcript(job_id, output_file):
    """Download completed transcript"""
    print(f"\nDownloading transcript for job: {job_id}")
    try:
        response = requests.get(f"{API_URL}/api/download/{job_id}")
        if response.status_code == 200:
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"✅ Downloaded to: {output_file}")
            return True
        else:
            print(f"❌ Download failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Download error: {e}")
        return False


def main():
    print("=" * 60)
    print("Azure Speech API Command-Line Test")
    print("=" * 60)

    # Test health
    if not test_health():
        print("\n⚠️  API is not running. Start it with: python app.py")
        return

    # Check if file path provided
    if len(sys.argv) < 2:
        print("\nUsage: python test_api.py <audio_file.wav>")
        print("Example: python test_api.py ../audio/sample.wav")
        return

    file_path = sys.argv[1]

    # Upload file
    job_id = test_upload(file_path)
    if not job_id:
        return

    # Stream transcription
    output_file = f"test_output_{job_id}.txt"
    stream_transcription(job_id, output_file)

    # Check final status
    test_status(job_id)

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
