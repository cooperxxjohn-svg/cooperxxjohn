#!/usr/bin/env python3
"""
Upload files to Google Drive from server
Simple OAuth flow for headless server
"""

import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes for Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_credentials():
    """Get Google Drive credentials via OAuth"""
    creds = None
    token_file = 'token.pickle'

    # Check if we have saved credentials
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Create credentials without client_secrets file
            # Using installed app flow with manual entry
            print("\n" + "="*70)
            print("GOOGLE DRIVE AUTHENTICATION")
            print("="*70)
            print("\nWe need to authorize access to your Google Drive.")
            print("Since this is a headless server, we'll use device flow.\n")

            # Use rclone's OAuth client which is verified
            client_config = {
                "installed": {
                    "client_id": "202264815644.apps.googleusercontent.com",
                    "project_id": "rclone-1-oauth",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": "X4Z3ca8xfWDb1Voo-F9a7ZxJ",
                    "redirect_uris": ["http://localhost"]
                }
            }

            flow = InstalledAppFlow.from_client_config(
                client_config,
                SCOPES,
                redirect_uri='http://localhost:8080'
            )

            print("Opening authorization URL...\n")
            auth_url, _ = flow.authorization_url(prompt='consent')

            print("=" * 70)
            print("OPEN THIS URL IN YOUR BROWSER:")
            print("=" * 70)
            print(f"\n{auth_url}\n")
            print("=" * 70)
            print("\nSteps:")
            print("1. Click the URL above (or copy/paste into browser)")
            print("2. Sign in to your Google account")
            print("3. Click 'Allow' to grant access")
            print("4. Copy the authorization code")
            print("5. Paste it below\n")

            code = input("Enter the authorization code: ").strip()

            flow.fetch_token(code=code)
            creds = flow.credentials

        # Save credentials for next time
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

        print("\n✅ Authentication successful!")

    return creds

def create_folder(service, folder_name, parent_id=None):
    """Create a folder in Google Drive"""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    if parent_id:
        file_metadata['parents'] = [parent_id]

    folder = service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()

    return folder.get('id')

def upload_file(service, file_path, folder_id=None):
    """Upload a file to Google Drive"""
    file_name = Path(file_path).name
    file_metadata = {'name': file_name}

    if folder_id:
        file_metadata['parents'] = [folder_id]

    # Determine MIME type
    if file_name.endswith('.zip'):
        mime_type = 'application/zip'
    elif file_name.endswith('.ipynb'):
        mime_type = 'application/x-ipynb+json'
    elif file_name.endswith('.md'):
        mime_type = 'text/markdown'
    else:
        mime_type = 'application/octet-stream'

    media = MediaFileUpload(
        file_path,
        mimetype=mime_type,
        resumable=True
    )

    print(f"\n📤 Uploading {file_name}...")

    # Get file size for progress
    file_size = Path(file_path).stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f"   Size: {size_mb:.1f} MB")

    request = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id,name,webViewLink'
    )

    response = None
    last_progress = 0

    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            if progress > last_progress + 10 or progress == 100:
                print(f"   Progress: {progress}%")
                last_progress = progress

    print(f"   ✅ Uploaded: {response.get('name')}")
    print(f"   🔗 Link: {response.get('webViewLink')}")

    return response

def main():
    print("\n" + "="*70)
    print("UPLOAD TO GOOGLE DRIVE")
    print("="*70)

    # Authenticate
    creds = get_credentials()

    # Build Drive service
    service = build('drive', 'v3', credentials=creds)

    # Create folder structure
    print("\n📁 Creating folder: floor_plan_training/")
    folder_id = create_folder(service, 'floor_plan_training')
    print(f"   ✅ Folder created (ID: {folder_id})")

    # Files to upload
    files_to_upload = [
        'training_data.zip',
        'train_floor_plan_model.ipynb',
        'TRAINING_SETUP.md'
    ]

    print("\n" + "="*70)
    print("UPLOADING FILES")
    print("="*70)

    uploaded_files = []
    for file_name in files_to_upload:
        file_path = Path(file_name)
        if file_path.exists():
            result = upload_file(service, str(file_path), folder_id)
            uploaded_files.append(result)
        else:
            print(f"\n⚠️  File not found: {file_name}")

    print("\n" + "="*70)
    print("✅ UPLOAD COMPLETE!")
    print("="*70)
    print(f"\nUploaded {len(uploaded_files)} files to:")
    print("My Drive/floor_plan_training/")
    print("\nNext steps:")
    print("1. Go to https://colab.research.google.com")
    print("2. File → Open → Google Drive")
    print("3. Navigate to floor_plan_training/")
    print("4. Open train_floor_plan_model.ipynb")
    print("5. Runtime → Change runtime type → T4 GPU")
    print("6. Runtime → Run all")
    print("\n🚀 Training will start in ~30 minutes!")
    print("="*70 + "\n")

if __name__ == '__main__':
    os.chdir('/home/user/cooperxxjohn/data-collection')
    main()
