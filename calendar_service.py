import os
import pickle
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import logging
from pathlib import Path
import pytz
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

class CalendarService:
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        load_dotenv()
        
        # Set up paths
        self.base_dir = Path(__file__).parent
        self.token_path = self.base_dir / 'token.pickle'
        self.credentials_path = self.base_dir / 'credentials.json'
        
        # Calendar settings
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.timezone = pytz.timezone('America/New_York')  # Set to New York timezone
        self.calendar_id = 'primary'
        
        # Initialize the calendar service
        self.service = self._get_calendar_service()
        
    def clear_token(self):
        """Clear the stored token to force re-authentication."""
        if self.token_path.exists():
            self.token_path.unlink()
            self.logger.info("Token file cleared. Next authentication will require new OAuth flow.")
        else:
            self.logger.info("No token file found to clear.")
    
    def _get_calendar_service(self):
        """Get or refresh the calendar service."""
        creds = None
        
        # Load existing token
        if self.token_path.exists():
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                self.logger.warning(f"Error loading existing token: {e}")
                creds = None
        
        # Refresh token if needed
        if creds and creds.expired and creds.refresh_token:
            try:
                self.logger.info("Refreshing expired credentials...")
                creds.refresh(Request())
                self.logger.info("Credentials refreshed successfully")
                
                # Save the refreshed token
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
                    
            except Exception as e:
                self.logger.error(f"Error refreshing credentials: {e}")
                self.logger.info("Removing invalid token file and requesting new authentication...")
                # Remove the invalid token file
                if self.token_path.exists():
                    self.token_path.unlink()
                creds = None
        
        # Create new token if needed
        if not creds:
            if not self.credentials_path.exists():
                raise FileNotFoundError(
                    "credentials.json not found. Please ensure you have downloaded the OAuth credentials "
                    "from Google Cloud Console and placed them in the same directory as this script."
                )
            
            self.logger.info("Starting OAuth flow for new authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path), self.SCOPES)
            
            # Run the OAuth flow
            creds = flow.run_local_server(port=0)
            
            # Save the token
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
            
            self.logger.info("New authentication completed and token saved")
        
        return build('calendar', 'v3', credentials=creds)
    
    def _parse_time(self, time_str):
        """Parse time string into datetime object."""
        try:
            now = datetime.now(self.timezone)
            self.logger.info(f"Current time: {now}")
            self.logger.info(f"Parsing time string: {time_str}")
            
            
            # Clean the input string - remove quotes and normalize
            time_str = time_str.strip().lower()
            time_str = time_str.replace('at', '').replace('for', '').replace('"', '').replace("'", '').strip()
            
            # Handle "tomorrow"
            if 'tomorrow' in time_str:
                base_date = now.date() + timedelta(days=1)
                time_str = time_str.replace('tomorrow', '').strip()
                self.logger.info(f"Scheduling for tomorrow: {base_date}")
            else:
                base_date = now.date()
            
            # Handle time range — take the first part only
            if 'to' in time_str:
                time_str = time_str.split('to')[0].strip()

            # Try parsing with multiple formats
            parsed_time = None
            formats_to_try = [
                "%I %p",      # "2 pm"
                "%I:%M %p",   # "2:30 pm"
                "%I%p",       # "2pm"
                "%I:%M%p",    # "2:30pm"
                "%H:%M",      # "14:30"
                "%H",         # "14"
            ]
            
            for fmt in formats_to_try:
                try:
                    parsed_time = datetime.strptime(time_str, fmt).time()
                    self.logger.info(f"Successfully parsed with format: {fmt}")
                    break
                except ValueError:
                    continue
            
            if not parsed_time:
                # Try to extract hour and minute manually
                parts = time_str.split()
                hour = None
                minutes = 0
                
                for part in parts:
                    if part.endswith('pm'):
                        hour = int(part.replace('pm', ''))
                        if hour != 12:
                            hour += 12
                    elif part.endswith('am'):
                        hour = int(part.replace('am', ''))
                        if hour == 12:
                            hour = 0
                    elif part.isdigit():
                        if hour is None:
                            hour = int(part)
                        else:
                            minutes = int(part)
                
                if hour is not None:
                    parsed_time = datetime.min.time().replace(hour=hour, minute=minutes)
                    self.logger.info(f"Manually parsed: hour={hour}, minutes={minutes}")
                else:
                    raise ValueError(f"Could not extract time from: {time_str}")
            
            # Combine date and time
            event_time = datetime.combine(base_date, parsed_time)
            event_time = self.timezone.localize(event_time)

            self.logger.info(f"Created event time: {event_time}")
            
            if event_time <= now:
                raise ValueError("Cannot schedule time in the past")
            
            return event_time

        except Exception as e:
            self.logger.error(f"Error parsing time: {e}")
            self.logger.error(f"Original time string: {time_str}")
            raise ValueError(f"Could not parse time string: {time_str}. Please use format like '2 PM' or '2:30 PM'")


    def get_user_email(self):
        try:
            # Get user info service
            user_info_service = build('oauth2', 'v2', credentials=self.service.credentials)
            user_info = user_info_service.userinfo().get().execute()
            return user_info.get('email')
        except Exception as e:
            self.logger.error(f"Error getting user email: {str(e)}")
            return None

    def schedule_call(self, time_str):
        """Schedule a consultation call."""
        try:
            # Parse the requested time
            start_time = self._parse_time(time_str)
            end_time = start_time + timedelta(minutes=30)  # 30-minute calls
            
            self.logger.info(f"Scheduling call from {start_time} to {end_time} (New York Time)")
            
            # Create event details
            event = {
                'summary': 'NFL Insights Assistant Consultation Call',
                'description': 'A consultation call with NFL Insights Team.\n\nThis is a consultation call to discuss your issues with the assistant insights.\n\nNote: All times are in New York (ET) timezone.',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'organizer': {
                    'email': 'utkarsh.gsb@gmail.com',
                    'self': True
                },
                'attendees': [
                    {
                        'email': 'utkarsh.gsb@gmail.com',
                        'responseStatus': 'accepted',
                        'organizer': True
                    },
                    {
                        'email': 'utkarsh.gsb@outlook.com',
                        'responseStatus': 'needsAction'
                    }
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                        {'method': 'email', 'minutes': 60},       # 1 hour before
                        {'method': 'popup', 'minutes': 10}        # 10 minutes before
                    ]
                },
                'guestsCanModify': False,
                'guestsCanInviteOthers': False,
                'guestsCanSeeOtherGuests': True,
                'sendUpdates': 'all',  # This ensures notifications are sent
                'status': 'confirmed'
            }
            
            # Create the event
            self.logger.info(f"Creating event for {start_time}")
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                conferenceDataVersion=1,
                sendNotifications=True,
                sendUpdates='all'
            ).execute()
            
            self.logger.info(f"Event created successfully: {event.get('htmlLink')}")
            
            # Format the response
            formatted_time = start_time.strftime("%B %d, %Y at %I:%M %p")
            return {
                'success': True,
                'event_time': formatted_time,
                'event_link': event.get('htmlLink', ''),
                'message': 'Perfect! Your consultation call has been scheduled and calendar invites have been sent. You will receive email notifications 24 hours and 1 hour before the call.'
            }
            
        except ValueError as ve:
            self.logger.error(f"Value error: {ve}")
            return {'success': False, 'error': str(ve)}
        except Exception as e:
            self.logger.error(f"Error scheduling call: {e}")
            return {'success': False, 'error': "Failed to schedule the call. Please try again."}
    
    def get_available_slots(self, date_str):
        """Get available time slots for a given date."""
        try:
            # Parse the date
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            now = datetime.now(self.timezone)
            
            # Ensure date is not in the past
            if target_date < now.date():
                return {'success': False, 'error': 'Cannot check availability for past dates'}
            
            # Get events for the target date
            start = datetime.combine(target_date, datetime.min.time())
            end = datetime.combine(target_date, datetime.max.time())
            
            start = self.timezone.localize(start)
            end = self.timezone.localize(end)
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Business hours: 9 AM to 5 PM
            business_hours = {
                'start': 9,
                'end': 17,
                'slot_duration': 30  # minutes
            }
            
            # Generate all possible slots
            all_slots = []
            slot_time = start.replace(hour=business_hours['start'], minute=0)
            
            while slot_time.hour < business_hours['end']:
                if slot_time > now:  # Only include future slots
                    all_slots.append({
                        'start': slot_time,
                        'end': slot_time + timedelta(minutes=business_hours['slot_duration'])
                    })
                slot_time += timedelta(minutes=business_hours['slot_duration'])
            
            # Remove booked slots
            available_slots = []
            for slot in all_slots:
                is_available = True
                for event in events:
                    event_start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
                    event_end = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')))
                    
                    if (slot['start'] < event_end and slot['end'] > event_start):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append(slot['start'].strftime("%I:%M %p"))
            
            return {
                'success': True,
                'date': target_date.strftime("%B %d, %Y"),
                'available_slots': available_slots
            }
            
        except Exception as e:
            self.logger.error(f"Error getting available slots: {e}")
            return {'success': False, 'error': str(e)} 