#!/usr/bin/env python3
"""
Simple script to generate a fresh token.pickle file
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from calendar_service import CalendarService
import logging

def main():
    print("Generating fresh Google Calendar token...")
    print("=" * 40)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Check if credentials file exists
        credentials_path = Path(__file__).parent / 'credentials.json'
        if not credentials_path.exists():
            print("❌ ERROR: credentials.json not found!")
            return
        
        print("✅ credentials.json found")
        
        # Remove any existing token file
        token_path = Path(__file__).parent / 'token.pickle'
        if token_path.exists():
            token_path.unlink()
            print("✅ Removed old token.pickle")
        
        print("\nStarting OAuth authentication...")
        print("A browser window will open for you to authorize the application.")
        print("After authorization, the token will be saved automatically.")
        
        # Create new service (this will trigger OAuth flow)
        calendar_service = CalendarService()
        
        # Test the authentication
        email = calendar_service.get_user_email()
        if email:
            print(f"✅ Authentication successful!")
            print(f"✅ User email: {email}")
            print(f"✅ Token saved to: {token_path}")
            print("\nYour calendar service is now ready to use!")
        else:
            print("❌ Authentication failed - could not get user email")
            
    except Exception as e:
        print(f"❌ Error during authentication: {e}")

if __name__ == "__main__":
    main() 