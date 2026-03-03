#!/usr/bin/env python3
"""Environment setup helper for Bill Import Service.

This script helps generate the required .env file with secure random keys.
"""

import os
import secrets
import sys
from pathlib import Path


def generate_env_file(env_path: Path, force: bool = False) -> None:
    """Generate a .env file with secure random keys.

    Args:
        env_path: Path where the .env file should be created
        force: If True, overwrite existing .env file
    """
    if env_path.exists() and not force:
        print(f"⚠️  {env_path} already exists.")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Aborted.")
            sys.exit(1)

    # Generate secure random keys
    secret_key = secrets.token_urlsafe(48)
    password_encryption_key = secrets.token_urlsafe(32)

    # Read example file if exists
    example_path = env_path.parent / ".env.example"
    example_content = ""
    if example_path.exists():
        with open(example_path, 'r') as f:
            example_content = f.read()

    # Replace placeholder values
    env_content = example_content.replace("your-secret-key-here-change-this-in-production", secret_key)
    env_content = env_content.replace("your-password-encryption-key-here-change-this", password_encryption_key)

    # Enable multi-tenant mode by default
    env_content = env_content.replace("MULTI_TENANT_ENABLED=auto", "MULTI_TENANT_ENABLED=true")

    # Write .env file
    with open(env_path, 'w') as f:
        f.write(env_content)

    # Set file permissions (read/write for owner only)
    os.chmod(env_path, 0o600)

    print(f"✅ .env file created successfully at {env_path}")
    print(f"\n📝 Generated keys:")
    print(f"   - SECRET_KEY: {secret_key[:20]}...")
    print(f"   - PASSWORD_ENCRYPTION_KEY: {password_encryption_key[:20]}...")
    print(f"\n⚠️  Please keep these keys secure and do not share them!")
    print(f"\n📋 Next steps:")
    print(f"   1. Edit .env and configure your Notion API credentials")
    print(f"   2. Run: python3 -m web_service.main")
    print(f"   3. Open http://localhost:8000 in your browser")


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent.parent
    env_path = script_dir / ".env"

    print("=" * 60)
    print("Bill Import Service - Environment Setup")
    print("=" * 60)
    print()

    force = "--force" in sys.argv or "-f" in sys.argv
    generate_env_file(env_path, force)


if __name__ == "__main__":
    main()
