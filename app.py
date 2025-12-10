# -*- coding: utf-8 -*-
import os
import sys
from flask import Flask, render_template, request, jsonify, send_from_directory, Response, url_for
from dotenv import load_dotenv
import google.generativeai as genai
from flask_cors import CORS
from datetime import datetime
import pytz
import csv
import uuid
from doc_processor import DocumentProcessor
from calendar_service import CalendarService
import time
import random

# Initialize Flask app
app = Flask(__name__, 
           static_folder='static',
           static_url_path='/static',
           template_folder='templates')
CORS(app)
app.debug = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching

try:
    # Load environment variables
    load_dotenv()
    
    # Initialize document processor and calendar service
    doc_processor = DocumentProcessor()
    calendar_service = CalendarService()
    
    # Configure Gemini AI
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    print("\n=== Configuring Gemini API ===")
    print(f"API Key configured: {GOOGLE_API_KEY[:10]}...")  # Print first 10 chars of API key
    
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        print("Gemini API configured successfully")
        
        # Test the API with a simple prompt
        print("\nTesting Gemini API...")
        test_model = genai.GenerativeModel('gemini-1.5-pro-latest')
        test_response = test_model.generate_content("Hello, are you working?")
        print(f"Test response: {test_response.text}")
        print("Gemini API test successful")
    except Exception as e:
        print(f"Error configuring Gemini API: {str(e)}")
        print("Full traceback:")
        import traceback
        print(traceback.format_exc())
        raise
    
    # List available models
    print("\nAvailable models:")
    for m in genai.list_models():
        print(f"- {m.name}")
    
    # Use the correct model name
    model = genai.GenerativeModel('gemini-2.5-flash') #genai.GenerativeModel('gemini-2.5-pro') #genai.GenerativeModel('gemini-1.5-pro-latest')
    print("\nModel initialized successfully")
    
    # Set up the context for the chatbot
    SYSTEM_CONTEXT = """You are an intelligent assistant trained to support football coaches, analysts, scouts, and players with game preparation using structured NFL play-by-play data.
    
    The play-by-play data may be unstructured or messy. You should still extract structured football insights from it.
    - Identify down, distance, yard line, play type (rush/pass/punt), player names, and outcomes.
    - Group sequences by drive (i.e., from one possession change to another).
    - Do not rely on pre-parsed formats; infer structure from raw text where needed.

    Your role is to help users with:
    1. Generating tactical summaries of a team's offense or defense
    2. Identifying play-calling tendencies across downs and game situations
    3. Analyzing individual player usage, including receivers, quarterbacks, and running backs
    4. Breaking down route directions, passing depth, and rushing styles
    5. Providing red zone behavior, third-down strategies, and situational tendencies
    6. Highlighting predictable patterns, penalties, and points of failure

    When generating responses:
    - Look at the question first, if its general greeting first respond to that
    - Always base your answer strictly on the play-by-play context pdf
    - Use exact data where available (counts, percentages, play examples)
    - If something is unclear or missing, say so transparently — never assume
    - Use numbered or bulleted summaries when appropriate for clarity
    - Be concise, tactical, and focused on information that would help prepare for a game

    When answering questions involving player tendencies:
    - Identify the most frequently targeted or active players
    - Cite specific quarters and timestamps when possible (e.g., “Q2 3:42”)
    - Avoid generalizations unless supported by consistent data patterns

    When answering team-level scouting questions:
    - Focus on play-calling balance, formation types, red zone usage, and situational strategies
    - Highlight any tendencies that may help a defensive coordinator or scout
    - Include both passing and rushing behavior

    When asked for scheduling consultation calls
    - Ask for their preferred date and time
    - Check availability in the calendar
    - Confirm the appointment details
    - Provide the calendar event link    

 
    Your tone should be professional, insightful, and coach-ready — like a football-savvy analyst embedded in a scouting department. Do not speculate, and never guess without data.
"""

    # Get the absolute path of the current directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
    static_dir = os.path.join(base_dir, 'static')
    templates_dir = os.path.join(base_dir, 'templates')

    print("="*50)
    print("Starting Flask application...")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Base directory: {base_dir}")
    print(f"Static directory: {static_dir}")
    print(f"Templates directory: {templates_dir}")

    # Check if directories exist
    print("\nChecking directories:")
    print(f"Static directory exists: {os.path.exists(static_dir)}")
    print(f"Templates directory exists: {os.path.exists(templates_dir)}")

    # List contents of static directory
    if os.path.exists(static_dir):
        print("\nContents of static directory:")
        for file in os.listdir(static_dir):
            file_path = os.path.join(static_dir, file)
            size = os.path.getsize(file_path)
            print(f"- {file} ({size} bytes)")

    # Ensure the logs directory exists with proper permissions
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    try:
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
            print(f"Created logs directory: {logs_dir}")
    except Exception as e:
        print(f"Warning: Could not create logs directory: {str(e)}")
        logs_dir = None

    # CSV file path for detailed chat history
    DETAILED_CHAT_FILE = os.path.join(logs_dir, 'detailed_chat_history.csv') if logs_dir else None
    
    print("\n=== Log File Path ===")
    print(f"Detailed Chat File: {DETAILED_CHAT_FILE}")
    print("===================")

    def initialize_fresh_chat_history():
        """Initialize a fresh chat history file"""
        if not DETAILED_CHAT_FILE:
            print("Warning: Detailed logging disabled - logs directory not available")
            return

        try:
            # Ensure the logs directory exists
            os.makedirs(os.path.dirname(DETAILED_CHAT_FILE), exist_ok=True)

            # Define standard headers
            standard_headers = ['Session_ID']
            max_possible_messages = 20
            for i in range(max_possible_messages):
                standard_headers.extend([f'user_{i+1}', f'assistant_{i+1}'])
            standard_headers.extend(['Call_Scheduled', 'Rating', 'Feedback', 'Conversation_Complete'])

            # Create a fresh file with headers
            with open(DETAILED_CHAT_FILE, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=standard_headers)
                writer.writeheader()
            print("Created fresh chat history file")
        except Exception as e:
            print(f"Error initializing chat history: {str(e)}")

    def log_chat(session_id, role, message):
        """Log a message by updating the detailed chat history"""
        if not DETAILED_CHAT_FILE:
            print("Warning: Detailed logging disabled - logs directory not available")
            return

        try:
            # Generate a unique session ID only if this is a new chat session
            if not session_id and role == "assistant":  # Skip generating ID for assistant messages
                return
            elif not session_id:  # Only generate new ID for first user message
                session_id = f"session_{uuid.uuid4().hex[:8]}_{random.randint(1000, 9999)}"
                print(f"Generated new session ID: {session_id}")

            # Initialize chat history for this session if not exists
            if session_id not in chat_histories:
                chat_histories[session_id] = []
                message_counts[session_id] = 0
                print(f"Initialized new chat history for session: {session_id}")

            # Add the message to chat history
            chat_histories[session_id].append({"role": role, "content": message})
            message_counts[session_id] += 1
            print(f"Added message to session {session_id}. Total messages: {message_counts[session_id]}")

            # Log the complete chat history
            log_detailed_chat(session_id, chat_histories[session_id])
            print(f"Updated detailed chat history for session: {session_id}")

            return session_id  # Return the session ID so it can be used in the response

        except Exception as e:
            print(f"Error logging chat: {str(e)}")
            print("Full traceback:")
            import traceback
            print(traceback.format_exc())

    def log_detailed_chat(session_id, chat_history, call_scheduled=False, rating=None, feedback=None):
        """Log the complete chat history in a structured format - one line per session"""
        if not DETAILED_CHAT_FILE:
            print("Warning: Detailed logging disabled - logs directory not available")
            return

        try:
            # Initialize fresh file if it doesn't exist or is empty
            if not os.path.exists(DETAILED_CHAT_FILE) or os.path.getsize(DETAILED_CHAT_FILE) == 0:
                initialize_fresh_chat_history()

            # Count messages from each role
            user_messages = [msg for msg in chat_history if msg["role"] == "user"]
            assistant_messages = [msg for msg in chat_history if msg["role"] == "assistant"]
            max_messages = max(len(user_messages), len(assistant_messages))

            # Create the row data
            row_data = {
                'Session_ID': session_id,
                'Call_Scheduled': 'Yes' if call_scheduled else 'No',
                'Rating': str(rating) if rating is not None else '',
                'Feedback': str(feedback) if feedback is not None else '',
                'Conversation_Complete': 'Yes' if session_id in completed_sessions else 'No'
            }

            # Add numbered messages
            for i in range(max_messages):
                if i < len(user_messages):
                    row_data[f'user_{i+1}'] = user_messages[i]['content'].replace('\n', ' ').strip()
                if i < len(assistant_messages):
                    row_data[f'assistant_{i+1}'] = assistant_messages[i]['content'].replace('\n', ' ').strip()

            # Define standard headers
            standard_headers = ['Session_ID']
            max_possible_messages = 20  # Set a reasonable maximum number of message pairs
            for i in range(max_possible_messages):
                standard_headers.extend([f'user_{i+1}', f'assistant_{i+1}'])
            standard_headers.extend(['Call_Scheduled', 'Rating', 'Feedback', 'Conversation_Complete'])

            # Read existing data if file exists
            existing_data = {}
            if os.path.exists(DETAILED_CHAT_FILE) and os.path.getsize(DETAILED_CHAT_FILE) > 0:
                try:
                    with open(DETAILED_CHAT_FILE, 'r', newline='', encoding='utf-8') as file:
                        reader = csv.DictReader(file)
                        for row in reader:
                            if row.get('Session_ID'):  # Only store valid rows
                                existing_data[row['Session_ID']] = row
                except Exception as e:
                    print(f"Error reading existing data: {e}")

            # Update or add the current session
            existing_data[session_id] = row_data

            # Write all data back to file
            with open(DETAILED_CHAT_FILE, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=standard_headers, extrasaction='ignore')
                writer.writeheader()
                for row in existing_data.values():
                    # Ensure all fields exist in the row
                    for header in standard_headers:
                        if header not in row:
                            row[header] = ''
                    writer.writerow(row)

            print(f"Successfully updated chat history for session {session_id}")
            print(f"Current row data: {row_data}")

        except Exception as e:
            print(f"Error logging chat: {str(e)}")
            print("Full traceback:")
            import traceback
            print(traceback.format_exc())

    # Store chat history and session data
    chat_histories = {}
    message_counts = {}  # Track message count per session
    session_states = {}  # Track session states for rating and feedback
    completed_sessions = set()  # Track completed sessions

    # Initialize a fresh chat history file
    initialize_fresh_chat_history()

    def should_suggest_call(session_id):
        """Check if we should suggest a call based on message count"""
        count = message_counts.get(session_id, 0)
        print(f"Current message count for session {session_id}: {count}")
        # Only suggest on exactly the 6th message
        return count == 6

    def get_ai_response(message, chat_context=None):
        try:
            print("\n=== AI Response Debug ===")
            print(f"Processing message: {message}")
            
            # Get session_id from context
            session_id = None
            if chat_context and len(chat_context) > 0:
                session_id = chat_context[0].get("session_id")

            # Check if conversation is already complete
            if session_id and session_id in completed_sessions:
                return "🔒 This conversation has ended. Please click 'Clear Chat' or refresh the page to start a new chat."

            # First, handle greetings and introductions
            greeting_keywords = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
            name_keywords = ['i am', 'my name', 'this is']
            
            message_lower = message.lower()
            is_greeting = any(keyword in message_lower for keyword in greeting_keywords)
            contains_name = any(keyword in message_lower for keyword in name_keywords)
            
            # Handle initial greeting with name
            if (is_greeting or contains_name): # and not chat_context
                # Extract name if present
                name = None
                if contains_name:
                    for keyword in name_keywords:
                        if keyword in message_lower:
                            name_part = message_lower.split(keyword)[-1].strip()
                            if name_part:
                                name = name_part.title()
                                break
                
                greeting = f"Hello{' ' + name if name else ''}!" + "\n" + "Welcome to the NFL Play-by-Play Assistant. I'm your virtual analyst, here to help you with:\n"
                services = [
                    "• Generating tactical summaries for any NFL team",
                    "• Identifying play-calling tendencies and patterns",
                    "• Analyzing player behavior (QBs, RBs, WRs)",
                    "• Preparing game-specific scouting reports"
                ]
                response = greeting + "\n".join(services) + "\n\nHow can I assist you today?"
                return response

            # Check session state for rating/feedback flow
            if session_id and session_id in session_states:
                state = session_states[session_id]
                if state.get('awaiting_rating'):
                    try:
                        rating = int(message)
                        if 1 <= rating <= 5:
                            session_states[session_id] = {
                                'awaiting_feedback': True, 
                                'rating': rating,
                                'call_scheduled': state.get('call_scheduled', False)  # Preserve call_scheduled state
                            }
                            # Log the rating immediately
                            log_detailed_chat(session_id, chat_histories[session_id], 
                                           call_scheduled=state.get('call_scheduled', False),
                                           rating=rating)
                            return "Thanks! Lastly, please share any brief feedback about your experience."
                        else:
                            return "Please rate your experience from 1-5."
                    except ValueError:
                        return "Please rate your experience from 1-5."
                elif state.get('awaiting_feedback'):
                    # Store feedback and complete conversation
                    rating = state.get('rating')
                    feedback = message
                    call_scheduled = state.get('call_scheduled', False)
                    
                    # Log the final state with both rating and feedback
                    log_detailed_chat(session_id, chat_histories[session_id], 
                                   call_scheduled=call_scheduled,
                                   rating=rating,
                                   feedback=feedback)
                    
                    # Mark conversation as complete
                    completed_sessions.add(session_id)
                    session_states.pop(session_id)
                    
                    print(f"Storing final chat state - Session: {session_id}, Rating: {rating}, Feedback: {feedback}, Call Scheduled: {call_scheduled}")
                    return "✨ Thank you for your feedback! Chat session complete."

            # Get relevant document context first
            try:
                print("Searching document context...")
                doc_context = doc_processor.get_document_context(message)
                print(f"Document context found: {bool(doc_context)}")
                if doc_context:
                    print(f"Context preview: {doc_context[:200]}...")
            except Exception as doc_error:
                print(f"Error getting document context: {str(doc_error)}")
                doc_context = ""

            # Prepare conversation history
            conversation = []
            if chat_context:
                for msg in chat_context[-5:]:  # Only use last 5 messages for context
                    role = "user" if msg["role"] == "user" else "assistant"
                    conversation.append({"role": role, "content": msg["content"]})
                print(f"Using last {len(conversation)} messages for context")

            # Construct the prompt with system context, document context, and conversation history
            prompt = f"""{SYSTEM_CONTEXT}

            You are given raw NFL play-by-play text (unstructured). Use this to derive tactical insights.

            == Play-by-Play Input ==
            {doc_context if doc_context else 'No structured context — use raw logs to analyze.'}

            == Prior Conversation ==
            {str(conversation) if conversation else 'No previous messages'}

            == User Question ==
            {message}

            == Your Task ==
            - Parse and extract key details: down, distance, yard line, play type (pass/rush/punt/etc.), player names, and outcomes.
            - Group sequences into drives — from one possession change to the next.
            - Cite timestamps and quarters when possible (e.g., “Q2 3:42”).
            - Use structured insights from raw play descriptions; **do not rely on pre-parsed formats**.
            - If red zone tendencies, pass depth, or rush styles are requested — infer them by scanning and summarizing patterns in the raw logs.

            == Rules ==
            - Answer based strictly on the provided data.
            - Be specific. Use numbers, patterns, and examples from the logs.
            - Format your response professionally and tactically, with bullets or numbering if helpful.
            - Keep the final answer concise — no more than 200 words.
            - You may use bullet points or numbering to stay within the word limit. 

            == Chain of Thought ==
            To generate your answer:
            1. **Step 1:** First parse and extract key elements from each play (down, distance, players, outcomes).
            2. **Step 2:** Organize plays into drives and summarize sequences.
            3. **Step 3:** Look for patterns relevant to the user's question (e.g., run-pass ratio, red zone behavior).
            4. **Step 4:** Only then, generate a final summary of insights using structured football reasoning.

            Think through the problem step-by-step before answering.

            == Output ==
            Return your intermediate reasoning steps **followed by** your final data-backed tactical insights.

            Response:"""

            print(f"Sending prompt to AI model...")

            
            # Get response from Gemini
            response = model.generate_content(prompt)

            print("Received response from AI model")
            
            if hasattr(response, 'text'):
                ai_response = response.text.strip()
                print(f"AI response: {ai_response[:200]}...")
                return ai_response
            else:
                print(f"Unexpected response format: {response}")
                return "I apologize, but I received an unexpected response format. Please try rephrasing your question."

        except Exception as e:
            print(f"Error in get_ai_response: {str(e)}")
            print(traceback.format_exc())
            return "I apologize, but I'm having trouble processing your request. Please try again or ask a different question."

    # Topic-specific responses for button clicks
    def get_topic_response(topic):
        """Get hardcoded responses for button clicks"""
        responses = {
            'team report': """Sharing a team-level behavior report!""",
                        
            'player summary': """Sharing a player-level behavior summary!""",
                        
            'quarterback summary': """Sharing a quarterback behavior summary!""",
                        
            'routing tendencies': """Sharing routing tendicies by top pass target!""",
                        
            'aDOT': """Sharing average depth of target (aDOT) per receiver!""",
                        
            'about us': """Sharing details about us!"""
            }
        
        # Handle "Tell me about" format
        if topic.lower().startswith('tell me about '):
            topic = topic.lower().replace('tell me about ', '')
            
        # First try to get hardcoded response
        response = responses.get(topic.lower())
        if response:
            return response
            
        # If no hardcoded response, use AI
        return get_ai_response(f"Tell me about {topic}")

    @app.route('/test')
    def test():
        print("Test endpoint accessed")
        
        # Test detailed chat logging
        test_session_id = "test_session_123"
        test_chat_history = [
            {"role": "user", "content": "Hello", "session_id": test_session_id},
            {"role": "assistant", "content": "Hi! How can I help?", "session_id": test_session_id},
            {"role": "user", "content": "I need assistance", "session_id": test_session_id},
            {"role": "assistant", "content": "What insights do you need?", "session_id": test_session_id}
        ]
        
        try:
            log_detailed_chat(test_session_id, test_chat_history, call_scheduled=False)
            print("Detailed chat log test successful")
            return "Flask server is running! Detailed chat logging test completed."
        except Exception as e:
            print(f"Error testing detailed chat log: {str(e)}")
            return f"Error testing detailed chat log: {str(e)}"

    @app.route('/')
    def home():
        try:
            print("Home endpoint accessed")
            template_path = os.path.join(templates_dir, 'index.html')
            print(f"Template path: {template_path}")
            print(f"Template exists: {os.path.exists(template_path)}")
            return render_template('index.html')
        except Exception as e:
            print(f"Error in home route: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return f"Error rendering template: {str(e)}", 500

    @app.route('/chat', methods=['POST'])
    def chat():
        """Handle chat messages"""
        try:
            data = request.get_json()
            message = data.get('message', '')
            session_id = data.get('session_id', '')

            if not message:
                return jsonify({'error': 'No message provided'}), 400

            print(f"\n=== New Chat Message ===")
            print(f"Session ID: {session_id}")
            print(f"Message: {message}")

            # Log the user's message and get the session ID
            session_id = log_chat(session_id, 'user', message) or session_id

            # Check if this is a button click
            is_button_click = message.lower().startswith('tell me about ') or message.lower() in [
                'team report', 'player summary', 'quarterback summary', 'routing tendencies', 
                'aDOT', 'about us'
            ]

            # Get response based on whether it's a button click or regular message
            if is_button_click:
                response = get_topic_response(message)
            else:
                # Get chat context for this session
                chat_context = chat_histories.get(session_id, [])
                print(f"Chat context length: {len(chat_context)}")
                response = get_ai_response(message, chat_context)

            print(f"Response received: {response[:200]}...")

            # Check if this is a scheduling attempt
            scheduling_keywords = ['tomorrow', 'next', 'schedule', 'book']
            time_indicators = ['pm', 'am', ':']
            is_scheduling_attempt = (
                any(keyword in message.lower() for keyword in scheduling_keywords) and
                any(indicator in message.lower() for indicator in time_indicators)
            )

            # Handle scheduling if detected
            if is_scheduling_attempt:
                try:
                    result = calendar_service.schedule_call(message)
                    if result.get('success'):
                        if session_id:
                            session_states[session_id] = {
                                'awaiting_rating': True,
                                'call_scheduled': True
                            }
                            message_counts[session_id] = 0
                        response = f"""Perfect! Your consultation is scheduled for {result.get('event_time')}. Calendar invites sent.

            Please rate your experience with me today (1-5)."""
                except Exception as e:
                    print(f"Error scheduling call: {str(e)}")

            # Check if we should ask for rating (after 6 messages if no call scheduled)
            message_count = message_counts.get(session_id, 0)
            if message_count >= 10 and session_id not in completed_sessions:  #6
                if session_id not in session_states or not session_states[session_id].get('awaiting_rating'):
                    session_states[session_id] = {'awaiting_rating': True}
                    response = f"{response}\n\nThank you for chatting with me! Please rate your experience (1-5)."

            # Log the assistant's response
            log_chat(session_id, 'assistant', response)

            # Check if we should suggest a call (only if not awaiting rating/feedback)
            show_call_buttons = (
                session_id and 
                should_suggest_call(session_id) and 
                not session_states.get(session_id, {}).get('awaiting_rating') and
                not session_states.get(session_id, {}).get('awaiting_feedback')
            )

            return jsonify({
                'response': response,
                'session_id': session_id,
                'show_call_buttons': show_call_buttons
            })

        except Exception as e:
            print(f"Error in chat route: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500

    @app.route('/clear_history', methods=['POST'])
    def clear_history():
        try:
            data = request.get_json()
            session_id = data.get('session_id', '')
            
            if session_id in chat_histories:
                # Mark the session as complete
                completed_sessions.add(session_id)
                
                # Log final chat state before clearing
                log_detailed_chat(session_id, chat_histories[session_id], 
                                call_scheduled=session_states.get(session_id, {}).get('call_scheduled', False),
                                rating=session_states.get(session_id, {}).get('rating'),
                                feedback=session_states.get(session_id, {}).get('feedback'))
                
                # Clear all session data
                chat_histories.pop(session_id)
                message_counts.pop(session_id, None)
                session_states.pop(session_id, None)
            
            return jsonify({"status": "success"})
        except Exception as e:
            print(f"Error clearing history: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return jsonify({"error": str(e)}), 500

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory(app.static_folder, filename)

    @app.route('/get_available_slots', methods=['POST'])
    def get_available_slots():
        try:
            data = request.json
            date_str = data.get('date')
            if not date_str:
                return jsonify({"success": False, "error": "Date is required"}), 400
                
            resu
            lt = calendar_service.get_available_slots(date_str)
            return jsonify(result)
            
        except Exception as e:
            print(f"Error getting available slots: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/schedule_call', methods=['POST'])
    def schedule_call():
        try:
            data = request.get_json()
            datetime_str = data.get('datetime')
            email = data.get('email')
            name = data.get('name')
            session_id = data.get('session_id')
            
            # Schedule the call using calendar service
            event = calendar_service.schedule_consultation(datetime_str, email, name)
            
            if event and event.get('success'):
                # Log the successful call scheduling with the chat history
                if session_id and session_id in chat_histories:
                    log_detailed_chat(session_id, chat_histories[session_id], call_scheduled=True)
                
                # Return success without exposing email details
                return jsonify({
                    'success': True,
                    'message': 'Your consultation has been scheduled successfully! You will receive a calendar invite shortly.',
                    'event_id': event.get('event_id')
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Unable to schedule the consultation. Please try again or contact us directly.'
                })
        except Exception as e:
            print(f"Error scheduling call: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An error occurred while scheduling the consultation. Please try again later.'
            })

    if __name__ == '__main__':
        print("\nStarting Flask server on http://0.0.0.0:5000")
        try:
            app.run(host='0.0.0.0', debug=True, port=5000, use_reloader=True)
        except Exception as e:
            print(f"Error starting server: {str(e)}")
            import traceback
            print(traceback.format_exc())
            sys.exit(1)

except Exception as e:
    print(f"Critical error during startup: {str(e)}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1) 