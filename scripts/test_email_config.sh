#!/bin/bash
# Test script for email configuration functionality

set -e

echo "=========================================="
echo "Email Configuration Test Script"
echo "=========================================="
echo

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please run: python3 scripts/setup_env.py"
    exit 1
fi

# Source .env
set -a
source .env
set +a

# Check required variables
echo "📋 Checking environment variables..."

if [ -z "$PASSWORD_ENCRYPTION_KEY" ]; then
    echo "❌ PASSWORD_ENCRYPTION_KEY is not set!"
    echo "This is required for email configuration functionality."
    exit 1
fi

if [[ "$PASSWORD_ENCRYPTION_KEY" == *"your-"* ]] || [[ "$PASSWORD_ENCRYPTION_KEY" == *"change-this"* ]]; then
    echo "❌ PASSWORD_ENCRYPTION_KEY is using placeholder value!"
    echo "Please set a real value in .env file."
    exit 1
fi

echo "✅ PASSWORD_ENCRYPTION_KEY is configured"
echo

# Test password encryption
echo "🔐 Testing password encryption..."
python3 << 'EOF'
import sys
import os
sys.path.insert(0, '.')

try:
    from src.utils.crypto import PasswordEncryption

    # Test encryption/decryption
    crypto = PasswordEncryption()
    test_password = "TestPassword123!"
    encrypted = crypto.encrypt(test_password)
    decrypted = crypto.decrypt(encrypted)

    if test_password == decrypted:
        print("✅ Password encryption/decryption working correctly")
        print(f"   Original: {test_password}")
        print(f"   Encrypted: {encrypted[:40]}...")
        print(f"   Decrypted: {decrypted}")
    else:
        print("❌ Password encryption/decryption mismatch!")
        sys.exit(1)

except Exception as e:
    print(f"❌ Password encryption test failed: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ Encryption test failed!"
    exit 1
fi

echo
echo "=========================================="
echo "✅ All tests passed!"
echo "=========================================="
echo
echo "Email configuration is ready to use."
echo "You can now start the service with:"
echo "  ./scripts/start.sh"
echo "  or"
echo "  python3 -m web_service.main"
