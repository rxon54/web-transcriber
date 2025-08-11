#!/bin/bash
# upload_audio.sh: Upload an audio file to a transcription API endpoint using curl
# Usage: ./upload_audio.sh <audio_file> <api_url>

set -euo pipefail

# Function to print usage
usage() {
    echo "Usage: $0 <audio_file> <api_url>"
    exit 1
}

# Check arguments
if [ "$#" -ne 2 ]; then
    usage
fi

AUDIO_FILE="$1"
API_URL="$2"

# Check if file exists and is readable
if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: File '$AUDIO_FILE' does not exist." >&2
    exit 2
fi
if [ ! -r "$AUDIO_FILE" ]; then
    echo "Error: File '$AUDIO_FILE' is not readable." >&2
    exit 3
fi

# Detect MIME type
if command -v mimetype >/dev/null 2>&1; then
    MIME_TYPE=$(mimetype -b "$AUDIO_FILE")
else
    MIME_TYPE=$(file --mime-type -b "$AUDIO_FILE")
fi

if [ -z "$MIME_TYPE" ]; then
    echo "Error: Could not detect MIME type for '$AUDIO_FILE'." >&2
    exit 4
fi

echo "Uploading '$AUDIO_FILE' (type: $MIME_TYPE) to $API_URL ..."

# Perform the upload with progress bar
HTTP_RESPONSE=$(curl --progress-bar -w "%{http_code}" -o /tmp/upload_audio_response.txt -s -F "file=@$AUDIO_FILE;type=$MIME_TYPE" "$API_URL" || true)
CURL_EXIT=$?

if [ $CURL_EXIT -ne 0 ]; then
    echo "Error: Network or curl failure (exit code $CURL_EXIT)." >&2
    exit 5
fi

# Extract HTTP status code
HTTP_CODE="${HTTP_RESPONSE: -3}"
RESPONSE_BODY=$(cat /tmp/upload_audio_response.txt)

if [[ "$HTTP_CODE" =~ ^2 ]]; then
    echo "Upload successful! Server response:"
    echo "$RESPONSE_BODY"
    exit 0
else
    echo "Error: Server returned HTTP $HTTP_CODE" >&2
    echo "Response body:" >&2
    echo "$RESPONSE_BODY" >&2
    exit 6
fi
