"""
Conversational Chat Interface Component
Provides a natural chat-based interaction for the Company Research Assistant
"""

import streamlit as st
from typing import List, Dict, Optional, Any
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
try:
    import assemblyai as aai
    ASSEMBLYAI_AVAILABLE = True
except ImportError:
    ASSEMBLYAI_AVAILABLE = False
    aai = None

import os
from dotenv import load_dotenv
import tempfile
import time

try:
    from elevenlabs import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    ElevenLabs = None
import base64

# Load environment variables
load_dotenv()


class ChatMessage:
    """Represents a single chat message"""
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None, metadata: Optional[Dict] = None):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatMessage':
        timestamp = datetime.fromisoformat(data['timestamp']) if isinstance(data.get('timestamp'), str) else datetime.now()
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=timestamp,
            metadata=data.get('metadata', {})
        )


class ChatInterface:
    """Manages conversational chat interface"""
    
    def __init__(self):
        self.initialize_chat_state()
    
    def initialize_chat_state(self):
        """Initialize chat-related session state"""
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        if 'chat_mode' not in st.session_state:
            st.session_state.chat_mode = True  # Default to chat mode
        
        if 'current_research_context' not in st.session_state:
            st.session_state.current_research_context = None
        
        if 'research_in_progress' not in st.session_state:
            st.session_state.research_in_progress = False
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to chat history"""
        message = ChatMessage(role=role, content=content, metadata=metadata)
        st.session_state.chat_messages.append(message)
        return message
    
    def get_chat_history(self) -> List[ChatMessage]:
        """Get all chat messages"""
        return [ChatMessage.from_dict(msg) if isinstance(msg, dict) else msg 
                for msg in st.session_state.chat_messages]
    
    def clear_chat(self):
        """Clear chat history"""
        st.session_state.chat_messages = []
        st.session_state.current_research_context = None
    
    def _generate_elevenlabs_voice(self, text: str) -> Optional[bytes]:
        """Generate human-like voice using ElevenLabs API"""
        if not ELEVENLABS_AVAILABLE:
            return None
            
        try:
            elevenlabs_api_key = os.getenv('ELEVENLABS_API')
            if not elevenlabs_api_key:
                return None
            
            # Initialize ElevenLabs client
            client = ElevenLabs(api_key=elevenlabs_api_key)
            
            # Get selected voice from settings
            voice_settings = st.session_state.get('voice_settings', {})
            voice_id = voice_settings.get('voice_id', "21m00Tcm4TlvDq8ikWAM")  # Default to Rachel
            
            # Clean text for TTS (remove markdown, limit length)
            clean_text = text.replace('*', '').replace('#', '').replace('`', '').replace('**', '')
            clean_text = ' '.join(clean_text.split())  # Clean whitespace
            clean_text = clean_text[:2500]  # Limit to 2500 chars
            
            # Generate audio using ElevenLabs with selected voice
            audio_generator = client.text_to_speech.convert(
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                text=clean_text,
            )
            
            # Collect audio chunks
            audio_bytes = b""
            for chunk in audio_generator:
                audio_bytes += chunk
            
            return audio_bytes
            
        except Exception as e:
            st.warning(f"⚠️ ElevenLabs error: {str(e)[:100]}... Using fallback TTS.")
            return None
    
    def _render_tts_for_message(self, text: str):
        """Render text-to-speech for a message using ElevenLabs"""
        # Try ElevenLabs first
        audio_bytes = self._generate_elevenlabs_voice(text)
        
        if audio_bytes:
            # Encode audio to base64 for embedding
            audio_b64 = base64.b64encode(audio_bytes).decode()
            
            # Create autoplay audio element
            audio_html = f"""
            <audio autoplay style="display:none;">
                <source src="data:audio/mpeg;base64,{audio_b64}" type="audio/mpeg">
            </audio>
            <script>
                console.log('🔊 Playing ElevenLabs voice...');
            </script>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
        else:
            # Fallback to browser TTS
            import json
            voice_settings = st.session_state.get('voice_settings', {'rate': 1.0, 'pitch': 1.0})
            rate = voice_settings.get('rate', 1.0)
            pitch = voice_settings.get('pitch', 1.0)
            
            clean_text = text.replace('*', '').replace('#', '').replace('`', '').replace('**', '')
            clean_text = ' '.join(clean_text.split())[:1500]
            
            tts_html = f"""
            <script>
            (function() {{
                if ('speechSynthesis' in window) {{
                    window.speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance({json.dumps(clean_text)});
                    utterance.lang = 'en-US';
                    utterance.rate = {rate};
                    utterance.pitch = {pitch};
                    setTimeout(() => window.speechSynthesis.speak(utterance), 100);
                }}
            }})();
            </script>
            """
            st.markdown(tts_html, unsafe_allow_html=True)
    
    def _auto_speak_last_response(self):
        """Automatically speak the last AI response if voice mode is enabled"""
        if st.session_state.get('voice_conversation_mode', False):
            messages = self.get_chat_history()
            if messages and messages[-1].role == 'assistant':
                # Check if we haven't already spoken this message
                last_msg_id = f"{messages[-1].timestamp.timestamp()}"
                if st.session_state.get('last_spoken_message') != last_msg_id:
                    st.session_state.last_spoken_message = last_msg_id
                    self._render_tts_for_message(messages[-1].content)
    
    def _render_voice_input_assemblyai(self):
        """Render voice input using audio recorder and AssemblyAI transcription"""
        try:
            from st_audiorec import st_audiorec
        except ImportError:
            st.error("❌ Audio recorder not installed. Run: pip install streamlit-audiorec")
            return
        
        # Check for AssemblyAI availability
        if not ASSEMBLYAI_AVAILABLE:
            st.error("❌ AssemblyAI is not installed. Run: pip install assemblyai")
            return
            
        # Initialize AssemblyAI
        assembly_api_key = os.getenv('ASSEMBLY_API')
        if not assembly_api_key:
            st.error("❌ AssemblyAI API key not found in .env file")
            return
        
        aai.settings.api_key = assembly_api_key
        
        # Voice input header
        st.markdown("### 🎤 Voice Input with AssemblyAI")
        st.info("🎙️ Click START to begin recording. The recording will continue until you click STOP.")
        
        # Auto-send setting
        auto_send = st.checkbox("Auto-send message after transcription", value=False, key="voice_auto_send")
        
        # Initialize session state for voice
        if 'voice_transcript' not in st.session_state:
            st.session_state.voice_transcript = ""
        if 'last_audio_bytes' not in st.session_state:
            st.session_state.last_audio_bytes = None
        if 'transcription_complete' not in st.session_state:
            st.session_state.transcription_complete = False
        
        # Audio recorder component with better control
        st.markdown("**Press START to begin recording, STOP when finished:**")
        audio_bytes = st_audiorec()
        
        # Check if we have a new recording (different from the last one)
        if audio_bytes and audio_bytes != st.session_state.last_audio_bytes:
            # Store the new audio bytes
            st.session_state.last_audio_bytes = audio_bytes
            st.session_state.transcription_complete = False
            
            st.success("🎤 Recording captured! Processing...")
            
            # Display audio player
            st.audio(audio_bytes, format="audio/wav")
            
            # Save audio to temporary file
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_path = tmp_file.name
                
                # Start transcription with status message
                with st.spinner("🔄 Transcribing with AssemblyAI..."):
                    # Transcribe with AssemblyAI
                    if ASSEMBLYAI_AVAILABLE and aai:
                        transcriber = aai.Transcriber()
                        transcript = transcriber.transcribe(tmp_path)
                        
                        # Wait for transcription to complete with timeout
                        max_wait = 30  # Maximum 30 seconds
                        wait_time = 0
                        while transcript.status not in [aai.TranscriptStatus.completed, aai.TranscriptStatus.error] and wait_time < max_wait:
                            time.sleep(0.5)
                            wait_time += 0.5
                            transcript = transcriber.get_transcript(transcript.id)
                        
                        # Clean up temp file
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                        
                        if transcript.status == aai.TranscriptStatus.completed:
                            transcribed_text = transcript.text
                            st.session_state.voice_transcript = transcribed_text
                            st.session_state.transcription_complete = True
                            st.rerun()  # Rerun to show the transcription
                        else:
                            st.error(f"❌ Transcription failed: {transcript.error if hasattr(transcript, 'error') else 'Unknown error'}")
                    else:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                        st.error("❌ AssemblyAI not available for transcription")
                
            except Exception as e:
                st.error(f"❌ Error during transcription: {str(e)}")
        
        # Display transcription if complete
        elif st.session_state.transcription_complete and st.session_state.voice_transcript:
            st.markdown("### 📝 Transcribed Text:")
            st.info(st.session_state.voice_transcript)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                if st.button("💬 Send to Chat", type="primary", use_container_width=True):
                    # Add message to chat
                    self.add_message('user', st.session_state.voice_transcript)
                    # Clear the transcript
                    st.session_state.voice_transcript = ""
                    st.session_state.transcription_complete = False
                    st.rerun()
            with col3:
                if st.button("🗑️ Clear", use_container_width=True):
                    st.session_state.voice_transcript = ""
                    st.session_state.transcription_complete = False
                    st.rerun()
                    if 'tmp_path' in locals() and os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    
    def _render_voice_input_html(self):
        """Render simple voice input using Chrome's microphone"""
        voice_html = """
        <style>
        .voice-container {
            padding: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            margin: 10px 0;
            text-align: center;
        }
        .voice-btn {
            background: white;
            color: #667eea;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin: 5px;
            transition: all 0.3s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .voice-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        }
        .voice-btn:active {
            transform: translateY(0);
        }
        .voice-btn.recording {
            background: #ff4444;
            color: white;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .voice-status {
            color: white;
            font-size: 14px;
            margin: 10px 0;
            font-weight: 500;
        }
        .voice-text-display {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            min-height: 60px;
            color: #333;
            font-size: 15px;
            text-align: left;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
        
        <div class="voice-container">
            <div class="voice-status" id="voice-status">🎤 Click the button to start voice input</div>
            <button class="voice-btn" id="voice-btn">
                🎙️ Start Voice Input
            </button>
            <div class="voice-text-display" id="voice-text-display">Your speech will appear here...</div>
            <input type="hidden" id="voice-output-field" />
        </div>
        
        <script>
        (function() {
        let recognition = null;
        let isRecording = false;
        let finalTranscript = '';
        
        function initSpeechRecognition() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.lang = 'en-US';
                recognition.maxAlternatives = 1;
                
                console.log('Speech recognition initialized successfully');
                
                recognition.onstart = function() {
                    isRecording = true;
                    console.log('🟢 SPEECH RECOGNITION STARTED - MIC IS ACTIVE');
                    
                    const statusElement = document.getElementById('voice-status');
                    const btnElement = document.getElementById('voice-btn');
                    const displayElement = document.getElementById('voice-text-display');
                    
                    if (statusElement) statusElement.textContent = '🎤 Listening... Speak now!';
                    if (btnElement) {
                        btnElement.textContent = '⏹️ Stop & Send';
                        btnElement.classList.add('recording');
                    }
                    if (displayElement) {
                        displayElement.textContent = '🎤 Listening... Say something!';
                        displayElement.style.color = '#00ff00';
                    }
                    
                    console.log('All UI elements updated for recording state');
                };
                
                recognition.onresult = function(event) {
                    console.log('🎤 SPEECH DETECTED! Results count:', event.results.length);
                    
                    // Clear and rebuild transcripts from all results
                    let interimTranscript = '';
                    finalTranscript = '';  // Reset final transcript
                    
                    for (let i = 0; i < event.results.length; i++) {
                        const transcript = event.results[i][0].transcript;
                        console.log('Result [' + i + '] - Final:', event.results[i].isFinal, 'Text: "' + transcript + '"');
                        
                        if (event.results[i].isFinal) {
                            finalTranscript += transcript + ' ';
                        } else {
                            interimTranscript += transcript;
                        }
                    }
                    
                    // Combine final and interim
                    const displayText = finalTranscript + interimTranscript;
                    console.log('📝 UPDATING DISPLAY with:', displayText);
                    
                    // Update the display element
                    const displayElement = document.getElementById('voice-text-display');
                    if (displayElement) {
                        displayElement.textContent = displayText || 'Listening...';
                        displayElement.style.color = '#333333';
                        displayElement.style.fontWeight = 'normal';
                        console.log('✅ Display element updated!');
                    } else {
                        console.error('❌ Display element NOT FOUND!');
                    }
                    
                    // Update the Streamlit text area if it exists
                    const textArea = window.parent.document.querySelector('textarea[aria-label*="Voice Transcription"]') ||
                                    window.parent.document.querySelector('#voice_text_area') ||
                                    window.parent.document.querySelector('textarea');
                    if (textArea) {
                        console.log('📝 Updating Streamlit text area with:', displayText);
                        textArea.value = displayText;
                        textArea.dispatchEvent(new Event('input', { bubbles: true }));
                        textArea.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    
                    // Update hidden field
                    const hiddenField = document.getElementById('voice-output-field');
                    if (hiddenField) {
                        hiddenField.value = finalTranscript;
                    }
                };
                
                recognition.onerror = function(event) {
                    console.error('Speech recognition error:', event.error);
                    const statusElement = document.getElementById('voice-status');
                    if (statusElement) {
                        statusElement.textContent = '❌ Error: ' + event.error + ' - Check browser permissions';
                    }
                    // Alert user with helpful troubleshooting info
                    alert('Microphone error: ' + event.error + '\\n\\nPlease ensure:\\n1. You granted microphone permission when prompted\\n2. Using Chrome, Edge, or Safari\\n3. Your microphone is working\\n4. Not already using mic in another tab');
                    stopRecording();
                };
                
                recognition.onend = function() {
                    if (isRecording) {
                        // Automatically submit the text when recording ends
                        submitVoiceText();
                    }
                };
                
                return true;
            } else {
                document.getElementById('voice-status').textContent = '❌ Voice input not supported in this browser. Use Chrome, Edge, or Safari.';
                document.getElementById('voice-btn').disabled = true;
                return false;
            }
        }
        
        function toggleVoiceRecording() {
            console.log('Voice button clicked. isRecording:', isRecording);
            
            if (!recognition) {
                console.log('Initializing speech recognition...');
                if (!initSpeechRecognition()) {
                    console.error('Failed to initialize speech recognition');
                    return;
                }
            }
            
            if (!isRecording) {
                console.log('🎬 STARTING RECORDING...');
                finalTranscript = '';
                const displayEl = document.getElementById('voice-text-display');
                if (displayEl) {
                    displayEl.textContent = '🎤 Listening... Speak now!';
                    displayEl.style.color = '#00ff00';
                    console.log('Display element found and updated to listening state');
                } else {
                    console.error('❌ CRITICAL: Display element not found!');
                }
                
                try {
                    recognition.start();
                    console.log('✅ recognition.start() called successfully');
                } catch (error) {
                    console.error('❌ Error starting recognition:', error);
                    alert('Failed to start voice recognition: ' + error.message);
                }
            } else {
                console.log('⏹️ STOPPING RECORDING...');
                stopRecording();
            }
        }
        
        function stopRecording() {
            if (recognition && isRecording) {
                isRecording = false;
                recognition.stop();
                document.getElementById('voice-btn').textContent = '🎙️ Start Voice Input';
                document.getElementById('voice-btn').classList.remove('recording');
                document.getElementById('voice-status').textContent = '✅ Processing your message...';
            }
        }
        
        function submitVoiceText() {
            if (finalTranscript.trim()) {
                const text = finalTranscript.trim();
                console.log('🚀 Submitting voice text:', text);
                
                // Update display
                document.getElementById('voice-status').textContent = '✅ Sending: "' + text.substring(0, 50) + '..."';
                
                // Method 1: Try to inject into Streamlit's chat input
                setTimeout(() => {
                    // Look for chat input in the parent window
                    const chatInput = window.parent.document.querySelector('textarea[placeholder*="Type your message"]') || 
                                     window.parent.document.querySelector('[data-testid="stChatInput"] textarea') ||
                                     window.parent.document.querySelector('textarea');
                    
                    if (chatInput) {
                        console.log('📝 Found chat input, injecting text');
                        // Set the value
                        chatInput.value = text;
                        // Trigger various events to ensure Streamlit detects the change
                        chatInput.dispatchEvent(new Event('input', { bubbles: true }));
                        chatInput.dispatchEvent(new Event('change', { bubbles: true }));
                        chatInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', keyCode: 13, bubbles: true }));
                        chatInput.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', keyCode: 13, bubbles: true }));
                        
                        // Also try clicking send button
                        const sendBtn = window.parent.document.querySelector('[data-testid="stChatInput"] button') ||
                                       window.parent.document.querySelector('button[kind="primary"]');
                        if (sendBtn) {
                            console.log('🔘 Clicking send button');
                            sendBtn.click();
                        }
                    } else {
                        console.warn('⚠️ Chat input not found, using fallback');
                    }
                }, 200);
                
                // Method 2: Store in sessionStorage as fallback
                sessionStorage.setItem('streamlit_voice_input', text);
                window.localStorage.setItem('voice_input_pending', text);
                
                // Method 3: Force page reload to trigger Streamlit rerun
                setTimeout(() => {
                    // Check if message was sent
                    const chatMessages = window.parent.document.querySelectorAll('[data-testid="stChatMessage"]');
                    const lastMessage = chatMessages[chatMessages.length - 1];
                    if (!lastMessage || !lastMessage.textContent.includes(text.substring(0, 20))) {
                        console.log('🔄 Message not sent, forcing reload');
                        window.location.reload();
                    }
                }, 1000);
                
                finalTranscript = '';
                
                // Reset UI
                setTimeout(() => {
                    document.getElementById('voice-text-display').textContent = 'Your speech will appear here...';
                    document.getElementById('voice-status').textContent = '🎤 Click the button to start voice input';
                }, 3000);
            } else {
                document.getElementById('voice-status').textContent = '⚠️ No speech detected. Try again!';
                console.warn('⚠️ No transcript to submit');
            }
        }
        
        // Initialize on load
        initSpeechRecognition();
        
        // Add event listener to button
        document.getElementById('voice-btn').addEventListener('click', toggleVoiceRecording);
        })();
        </script>
        """
        
        st.markdown(voice_html, unsafe_allow_html=True)
    
    def render_chat_interface(self, on_message_sent=None):
        """Render the chat interface UI"""
        st.markdown("### 💬 Professional Research Assistant - Chat Mode")
        st.markdown("*Ask questions, request company research, or have natural conversations about business topics*")
        
        # Voice mode toggle with settings
        voice_col1, voice_col2, voice_col3 = st.columns([1, 2, 1])
        with voice_col1:
            voice_enabled = st.checkbox(
                "🎤 Voice Mode",
                value=st.session_state.get('voice_conversation_mode', False),
                help="Enable full voice conversation: speak questions + hear AI responses"
            )
            st.session_state.voice_conversation_mode = voice_enabled
        
        with voice_col2:
            if voice_enabled:
                st.success("🎙️ **Voice Conversation Active**: Speak & Listen!")
            else:
                st.info("💡 Enable voice for hands-free conversation (speech-to-text + text-to-speech)")
        
        with voice_col3:
            if voice_enabled:
                with st.popover("⚙️ Voice Settings"):
                    st.markdown("**🎙️ AI Voice Settings (ElevenLabs)**")
                    
                    # Voice selection
                    voice_options = {
                        "Rachel (Professional Female)": "21m00Tcm4TlvDq8ikWAM",
                        "Adam (Deep Male)": "pNInz6obpgDQGcFmaJgB",
                        "Bella (Soft Female)": "EXAVITQu4vr4xnSDxMaL",
                        "Antoni (British Male)": "ErXwobaYiN019PkySvjV",
                        "Elli (Conversational Female)": "MF3mGyEYCl7XYWbV9V6O",
                        "Josh (Young Male)": "TxGEqnHWrfWFTfGW9XjX",
                        "Arnold (Crisp Male)": "VR6AewLTigWG4xSOukaG",
                        "Charlotte (Warm Female)": "XB0fDUnXU5powFXDhCwa"
                    }
                    
                    selected_voice_name = st.selectbox(
                        "Select AI Voice",
                        options=list(voice_options.keys()),
                        index=0,
                        key="voice_selection",
                        help="Choose how the AI assistant sounds"
                    )
                    
                    auto_speak = st.checkbox(
                        "Auto-speak responses", 
                        value=True, 
                        key="auto_speak", 
                        help="Automatically read AI responses aloud with ElevenLabs"
                    )
                    
                    st.session_state.voice_settings = {
                        'voice_id': voice_options[selected_voice_name],
                        'voice_name': selected_voice_name,
                        'auto_speak': auto_speak
                    }
                    
                    st.caption("🔊 Using ElevenLabs for natural, human-like AI voice")
        
        # Voice input using AssemblyAI (always show if enabled)
        if voice_enabled:
            # Only use AssemblyAI for voice input
            with st.expander("🎙️ Voice Input (AssemblyAI)", expanded=True):
                self._render_voice_input_assemblyai()
        # Chat mode toggle and model selection
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown("**Chat Mode:** Natural conversation with the AI assistant")
        with col2:
            # Using Groq model for conversations
            st.session_state.chat_conversation_model = 'groq'
            st.info("🤖 Groq (Llama 3.3)")
        with col3:
            if st.button("🔄 New Chat", use_container_width=True):
                self.clear_chat()
                st.rerun()
        # Display chat history
        chat_container = st.container()
        with chat_container:
            messages = self.get_chat_history()
            if not messages:
                # Show welcome message
                st.info("👋 **Welcome to your Professional Research Assistant!**\n\n"
                       "**I can help you with:**\n"
                       "• 🔬 Research companies and generate detailed account plans\n"
                       "• 💬 Answer questions about companies, industries, and markets\n"
                       "• 📊 Analyze financial performance and strategic positioning\n"
                       "• 🎯 Identify key decision makers and organizational structure\n"
                       "• 🤝 Provide insights for sales and business development\n\n"
                       "**Example Questions:**\n"
                       "- \"Create an account plan for Microsoft\"\n"
                       "- \"What is Apple's current market position?\"\n"
                       "- \"Tell me about Tesla's Q3 2024 financial results\"\n"
                       "- \"Who are the key executives at Amazon?\"\n\n"
                       "**Voice Mode:** Enable voice input in the settings above to speak your questions!\n\n"
                       "**Get Started:** Just type your question or request below!")
            else:
                # Display all messages
                for msg in messages:
                    if msg.role == 'user':
                        with st.chat_message("user"):
                            st.write(msg.content)
                            if msg.metadata.get('timestamp'):
                                st.caption(f"Sent at {msg.timestamp.strftime('%H:%M:%S')}")
                    else:
                        with st.chat_message("assistant"):
                            st.write(msg.content)
                            
                            # Voice output button if voice mode is enabled
                            if st.session_state.get('voice_conversation_mode', False):
                                if st.button(f"🔊 Read Aloud", key=f"tts_{msg.timestamp.timestamp()}", help="Click to hear this response"):
                                    self._render_tts_for_message(msg.content)
                            
                            # Show metadata if available
                            if msg.metadata:
                                if msg.metadata.get('research_id'):
                                    st.caption(f"Research ID: {msg.metadata.get('research_id')}")
                                if msg.metadata.get('sources'):
                                    with st.expander("📎 Sources"):
                                        for source in msg.metadata.get('sources', [])[:5]:
                                            if source.startswith('http'):
                                                st.markdown(f"- [{source}]({source})")
                                            else:
                                                st.markdown(f"- {source}")
        # Check for pending TTS (auto-speak new response in voice mode)
        if st.session_state.get('pending_tts'):
            voice_settings = st.session_state.get('voice_settings', {'auto_speak': True})
            if voice_settings.get('auto_speak', True):
                self._render_tts_for_message(st.session_state.pending_tts)
            st.session_state.pending_tts = None
        
        # Check for voice input from JavaScript and localStorage
        voice_check_script = """
        <script>
        (function checkVoiceInput() {
            // Check sessionStorage
            const voiceInput = sessionStorage.getItem('streamlit_voice_input');
            if (voiceInput) {
                console.log('📨 Found voice input in sessionStorage:', voiceInput);
                sessionStorage.removeItem('streamlit_voice_input');
                
                // Submit to Streamlit by programmatically filling the chat input
                const chatInput = document.querySelector('textarea[placeholder*="Type your message"]') || 
                                 document.querySelector('[data-testid="stChatInput"] textarea');
                if (chatInput) {
                    chatInput.value = voiceInput;
                    chatInput.dispatchEvent(new Event('input', { bubbles: true }));
                    chatInput.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    // Auto-submit after a short delay
                    setTimeout(() => {
                        const enterEvent = new KeyboardEvent('keydown', { 
                            key: 'Enter', 
                            code: 'Enter', 
                            keyCode: 13, 
                            which: 13,
                            bubbles: true 
                        });
                        chatInput.dispatchEvent(enterEvent);
                    }, 100);
                }
            }
            
            // Also check localStorage as fallback
            const pendingInput = window.localStorage.getItem('voice_input_pending');
            if (pendingInput) {
                console.log('📨 Found pending voice input in localStorage:', pendingInput);
                window.localStorage.removeItem('voice_input_pending');
                
                const chatInput = document.querySelector('textarea[placeholder*="Type your message"]') || 
                                 document.querySelector('[data-testid="stChatInput"] textarea');
                if (chatInput && !chatInput.value) {
                    chatInput.value = pendingInput;
                    chatInput.dispatchEvent(new Event('input', { bubbles: true }));
                    chatInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        })();
        </script>
        """
        st.markdown(voice_check_script, unsafe_allow_html=True)
        
        # Chat input (will also accept voice input via JavaScript injection)
        user_input = st.chat_input("💬 Type your message or use voice input above...")
        if user_input:
            # Add user message (will be processed in render_with_research_integration)
            self.add_message('user', user_input)
            st.rerun()
    
    def render_with_research_integration(self, research_handler, model_service):
        """Render chat interface integrated with research handler"""
        # Render chat UI
        self.render_chat_interface()
        
        # Process new user messages after rendering
        messages = self.get_chat_history()
        if messages and len(messages) > 0:
            last_message = messages[-1]
            if last_message.role == 'user' and not last_message.metadata.get('processed'):
                # Mark as processed
                last_message.metadata['processed'] = True
                
                # Check if this is a research request
                user_message = last_message.content.lower()
                is_research_request = any(keyword in user_message for keyword in [
                    'account plan', 'research', 'analyze', 'investigate', 'find information',
                    'company', 'financial', 'strategy', 'decision maker', 'competitor',
                    'create', 'generate', 'build'
                ])
                
                if is_research_request:
                    # Show research interface
                    with st.expander("🔬 Research Configuration", expanded=True):
                        self._render_research_config(research_handler, model_service, last_message.content)
                else:
                    # Handle conversational question
                    self._handle_conversational_query(last_message.content, research_handler, model_service)
    
    def _render_research_config(self, research_handler, model_service, query: str):
        """Render research configuration for a query"""
        # Using Groq model
        selected_model = 'groq'
        st.info("🤖 Using Groq (Llama 3.3 70B) for research")
        
        # API Key
        import os
        needed_env = "GROQ_API_KEY"
        env_api_key = os.environ.get(needed_env, "")
        
        api_key_source = st.radio(
            "API Key Source",
            ["Environment Variable", "Manual Input"],
            index=0 if env_api_key else 1,
            key="chat_api_key_source"
        )
        
        if api_key_source == "Manual Input":
            api_key = st.text_input(
                f"{needed_env}",
                type="password",
                key="chat_manual_api_key"
            )
        else:
            api_key = env_api_key
        
        # Quick research settings
        col1, col2 = st.columns(2)
        with col1:
            max_iterations = st.slider("Max Iterations", 1, 3, 1, key="chat_max_iter")
        with col2:
            search_api = st.selectbox("Search API", ["duckduckgo", "tavily", "none"], index=0, key="chat_search_api")
        
        # Start research button
        if st.button("🚀 Start Research", type="primary", use_container_width=True):
            if not api_key:
                st.error(f"Please provide {needed_env}")
            else:
                st.session_state.research_in_progress = True
                # Store research config
                st.session_state.pending_research = {
                    'query': query,
                    'model': selected_model,
                    'api_key': api_key,
                    'max_iterations': max_iterations,
                    'search_api': search_api
                }
                st.rerun()
    
    def _handle_conversational_query(self, query: str, research_handler, model_service=None):
        """Handle non-research conversational queries using LLM"""
        import os
        from langchain_groq import ChatGroq
        
        try:
            # Use Groq model for all conversations
            selected_model = 'groq'
            
            # Get Groq API key
            api_key_env = 'GROQ_API_KEY'
            
            api_key = os.environ.get(api_key_env, '')
            
            if not api_key:
                response = "⚠️ Please configure your API key to use conversational mode. "
                response += f"Set {api_key_env} in your environment or switch to Form Mode for research."
                self.add_message('assistant', response, metadata={'type': 'error'})
                st.rerun()
                return
            
            # Build conversation context
            messages = self.get_chat_history()
            conversation_history = []
            
            # Add system message
            system_prompt = """You are a professional Research Assistant specializing in company research and account planning.
            
Your role is to:
- Answer questions about companies, industries, and business topics
- Provide insights on financial performance, strategy, and competitive positioning
- Help users understand research results and account plans
- Engage in natural, professional conversations
- Be helpful, accurate, and concise

If you have access to previous research results, reference them when relevant.
If you need to conduct deep research, suggest that the user ask for an account plan or research report."""
            
            conversation_history.append(HumanMessage(content=system_prompt))
            
            # Add previous messages (last 10 for context)
            for msg in messages[-10:]:
                if msg.role == 'user':
                    conversation_history.append(HumanMessage(content=msg.content))
                elif msg.role == 'assistant':
                    conversation_history.append(AIMessage(content=msg.content))
            
            # Add context from previous research if available
            if st.session_state.get('deep_research_result'):
                result = st.session_state.deep_research_result
                context = f"\n\n[Context: Previous research on '{result.query}' is available. Summary: {result.final_report[:500]}...]"
                conversation_history.append(HumanMessage(content=context))
            
            # Initialize Groq LLM
            llm = ChatGroq(api_key=api_key, model='llama-3.3-70b-versatile', temperature=0.7)
            
            # Get response from LLM
            with st.spinner('🤔 Thinking...'):
                response = llm.invoke(conversation_history)
                response_text = response.content
            
            # Add assistant response to chat
            self.add_message('assistant', response_text, metadata={'type': 'conversational', 'model': selected_model})
            
            # Auto-speak response if voice mode is enabled
            if st.session_state.get('voice_conversation_mode', False):
                # Mark this message to be spoken on next render
                st.session_state.pending_tts = response_text
            
        except Exception as e:
            error_response = f"❌ Error processing your message: {str(e)}\n\nPlease try again or switch to Form Mode for research."
            self.add_message('assistant', error_response, metadata={'type': 'error'})
        
        st.rerun()
    
    def display_research_result_in_chat(self, result):
        """Display research result as a chat message"""
        report_preview = result.final_report[:500] + "..." if len(result.final_report) > 500 else result.final_report
        
        response = f"✅ **Research Complete!**\n\n"
        response += f"**Query:** {result.query}\n\n"
        response += f"**Report Preview:**\n{report_preview}\n\n"
        response += f"*Full report available below. You can ask me questions about this research or request edits.*"
        
        self.add_message(
            'assistant',
            response,
            metadata={
                'type': 'research_result',
                'research_id': result.research_id,
                'sources': result.sources,
                'full_report': result.final_report
            }
        )
        
        # Store as current context
        st.session_state.current_research_context = result

