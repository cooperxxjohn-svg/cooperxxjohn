#!/bin/bash
# Upload to Google Drive using rclone
# This will guide you through OAuth authentication

echo "================================================================="
echo "GOOGLE DRIVE UPLOAD WITH RCLONE"
echo "================================================================="
echo ""
echo "We'll set up Google Drive access and upload your training files."
echo ""

# Create rclone config directory
mkdir -p ~/.config/rclone

# Create a minimal rclone config
cat > ~/.config/rclone/rclone.conf << 'EOF'
[gdrive]
type = drive
scope = drive
EOF

echo "Opening browser for Google Drive authorization..."
echo ""
echo "Steps:"
echo "1. A browser window will open (or copy the URL)"
echo "2. Sign in to cooperxxjohn@gmail.com"
echo "3. Click 'Allow' to grant access"
echo "4. Authorization will complete automatically"
echo ""
echo "================================================================="
echo ""

# Run rclone authorize to get token
echo "Getting authorization token..."
rclone authorize "drive" "client_id" "client_secret"

echo ""
echo "If the above didn't work, we'll use manual config..."
echo ""
echo "Please run this command and follow the prompts:"
echo ""
echo "    rclone config"
echo ""
echo "Then:"
echo "  - Choose: n (new remote)"
echo "  - Name: gdrive"
echo "  - Storage: drive"
echo "  - Client ID: (leave blank, press Enter)"
echo "  - Client Secret: (leave blank, press Enter)"
echo "  - Scope: 1 (full access)"
echo "  - Root folder: (leave blank)"
echo "  - Service account: (leave blank)"
echo "  - Advanced config: n"
echo "  - Auto config: y"
echo ""
echo "This will open a browser for authorization."
echo ""
