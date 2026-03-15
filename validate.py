#!/usr/bin/env python3
"""
Validation script for Azure Speech-to-Text Streaming Transcription
"""

import os
import sys
from pathlib import Path


def check_file(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False


def check_directory(dirpath, description):
    """Check if a directory exists"""
    if Path(dirpath).exists() and Path(dirpath).is_dir():
        print(f"✅ {description}: {dirpath}")
        return True
    else:
        print(f"❌ {description}: {dirpath} NOT FOUND")
        return False


def main():
    print("=" * 60)
    print("Azure Speech-to-Text Implementation Validation")
    print("=" * 60)
    print()

    all_passed = True

    # Flask API Files
    print("🔍 Checking Flask API files...")
    all_passed &= check_file("api/app.py", "Main Flask application")
    all_passed &= check_file("api/transcription_service.py", "Transcription service")
    all_passed &= check_file("api/utils.py", "Utilities (logging, cleanup)")
    all_passed &= check_file("api/requirements.txt", "Python dependencies")
    all_passed &= check_file("api/gunicorn_config.py", "Gunicorn configuration")
    all_passed &= check_file("api/.env.example", "Environment template")
    all_passed &= check_file("api/.gitignore", "API gitignore")
    all_passed &= check_file("api/README.md", "API documentation")
    all_passed &= check_file("api/install.bat", "Windows installer")
    all_passed &= check_file("api/install.sh", "Unix installer")
    print()

    # Required directories
    print("🔍 Checking required directories...")
    all_passed &= check_directory("api/uploads", "Upload directory")
    all_passed &= check_directory("api/out", "Output directory")
    print()

    # WordPress Plugin Files
    print("🔍 Checking WordPress plugin files...")
    plugin_base = "wordpress-plugin/azure-speech-transcribe"
    all_passed &= check_file(
        f"{plugin_base}/azure-speech-transcribe.php", "Main plugin file"
    )
    all_passed &= check_file(
        f"{plugin_base}/includes/class-admin-settings.php", "Admin settings"
    )
    all_passed &= check_file(
        f"{plugin_base}/includes/class-shortcode.php", "Shortcode handler"
    )
    all_passed &= check_file(
        f"{plugin_base}/includes/class-ajax-handler.php", "AJAX handler"
    )
    all_passed &= check_file(
        f"{plugin_base}/assets/js/transcribe.js", "Frontend JavaScript"
    )
    all_passed &= check_file(f"{plugin_base}/assets/css/transcribe.css", "Frontend CSS")
    all_passed &= check_file(
        f"{plugin_base}/templates/transcribe-form.php", "Form template"
    )
    all_passed &= check_file(f"{plugin_base}/README.md", "Plugin documentation")
    print()

    # Documentation Files
    print("🔍 Checking documentation files...")
    all_passed &= check_file("PROJECT_README.md", "Main project documentation")
    all_passed &= check_file("QUICKSTART.md", "Quick start guide")
    all_passed &= check_file(".gitignore", "Root gitignore")
    print()

    # Startup Scripts
    print("🔍 Checking startup scripts...")
    all_passed &= check_file("start-api.bat", "Windows startup script")
    all_passed &= check_file("start-api.sh", "Unix startup script")
    print()

    # Original source files
    print("🔍 Checking original source files...")
    all_passed &= check_file("src/continuous_recog.py", "Original Azure Speech code")
    all_passed &= check_file("src/m4a_to_wav_converter.py", "Audio converter")
    print()

    # Summary
    print("=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print()
        print("Next steps:")
        print("1. cd api && python -m pip install -r requirements.txt")
        print("2. Copy api/.env.example to api/.env and add Azure credentials")
        print("3. Run: python api/app.py")
        print("4. Copy wordpress-plugin/azure-speech-transcribe to WordPress")
        print("5. Configure plugin settings in WordPress admin")
        print()
        print("See QUICKSTART.md for detailed instructions")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("Please review the missing files above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
