"""
Voice Interface Component
Provides speech-to-text and text-to-speech capabilities
"""

import streamlit as st
from typing import Optional, Callable
import json


class VoiceInterface:
    """Manages voice input/output functionality"""
    
    def __init__(self):
        self.initialize_voice_state()
    
    def initialize_voice_state(self):
        """Initialize voice-related session state"""
        if 'voice_mode_enabled' not in st.session_state:
            st.session_state.voice_mode_enabled = False
        
        if 'voice_input_text' not in st.session_state:
            st.session_state.voice_input_text = ""
        
        if 'last_voice_input' not in st.session_state:
            st.session_state.last_voice_input = None
    
    def render_voice_controls(self):
        """Render voice mode toggle and controls"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            voice_enabled = st.checkbox(
                "🎤 Enable Voice Mode",
                value=st.session_state.voice_mode_enabled,
                help="Enable speech-to-text input and text-to-speech output"
            )
            st.session_state.voice_mode_enabled = voice_enabled
        
        with col2:
            if voice_enabled:
                if st.button("🎙️ Start Recording", key="start_voice_recording"):
                    st.session_state.recording = True
                    st.info("🎤 Recording... Click 'Stop Recording' when done.")
    
    def render_voice_input_interface(self, on_voice_input: Optional[Callable] = None):
        """
        Render voice input interface using Web Speech API (browser-based)
        
        Note: This uses JavaScript/HTML for browser-based speech recognition
        """
        if not st.session_state.voice_mode_enabled:
            return None
        
        st.markdown("### 🎤 Voice Input")
        
        # Voice input using HTML/JavaScript (Web Speech API)
        voice_input_html = """
        <div id="voice-input-container">
            <button id="start-recording" onclick="startVoiceRecognition()" style="
                padding: 10px 20px;
                font-size: 16px;
                background-color: #1E88E5;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin: 5px;
            ">🎙️ Start Recording</button>
            
            <button id="stop-recording" onclick="stopVoiceRecognition()" style="
                padding: 10px 20px;
                font-size: 16px;
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin: 5px;
            ">⏹️ Stop Recording</button>
            
            <div id="recording-status" style="margin: 10px 0; padding: 10px; background-color: #f5f5f5; border-radius: 5px;">
                Status: Ready
            </div>
            
            <textarea id="voice-text-output" readonly style="
                width: 100%;
                min-height: 100px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                margin-top: 10px;
            " placeholder="Your voice input will appear here..."></textarea>
            
            <button id="submit-voice-input" onclick="submitVoiceInput()" style="
                padding: 10px 20px;
                font-size: 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 10px;
            ">✅ Submit Voice Input</button>
        </div>
        
        <script>
        let recognition = null;
        let isRecording = false;
        
        function initializeSpeechRecognition() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.continuous = false;
                recognition.interimResults = true;
                recognition.lang = 'en-US';
                
                recognition.onstart = function() {
                    isRecording = true;
                    document.getElementById('recording-status').textContent = 'Status: Recording...';
                    document.getElementById('start-recording').disabled = true;
                    document.getElementById('stop-recording').disabled = false;
                };
                
                recognition.onresult = function(event) {
                    let interimTranscript = '';
                    let finalTranscript = '';
                    
                    for (let i = event.resultIndex; i < event.results.length; i++) {
                        const transcript = event.results[i][0].transcript;
                        if (event.results[i].isFinal) {
                            finalTranscript += transcript + ' ';
                        } else {
                            interimTranscript += transcript;
                        }
                    }
                    
                    document.getElementById('voice-text-output').value = finalTranscript + interimTranscript;
                };
                
                recognition.onerror = function(event) {
                    console.error('Speech recognition error:', event.error);
                    document.getElementById('recording-status').textContent = 'Status: Error - ' + event.error;
                    isRecording = false;
                    document.getElementById('start-recording').disabled = false;
                    document.getElementById('stop-recording').disabled = true;
                };
                
                recognition.onend = function() {
                    isRecording = false;
                    document.getElementById('recording-status').textContent = 'Status: Stopped';
                    document.getElementById('start-recording').disabled = false;
                    document.getElementById('stop-recording').disabled = true;
                };
            } else {
                document.getElementById('recording-status').textContent = 'Status: Speech recognition not supported in this browser';
            }
        }
        
        function startVoiceRecognition() {
            if (!recognition) {
                initializeSpeechRecognition();
            }
            if (recognition && !isRecording) {
                recognition.start();
            }
        }
        
        function stopVoiceRecognition() {
            if (recognition && isRecording) {
                recognition.stop();
            }
        }
        
        function submitVoiceInput() {
            const text = document.getElementById('voice-text-output').value;
            if (text.trim()) {
                // Store in session storage for Streamlit to pick up
                sessionStorage.setItem('streamlit_voice_input', text);
                
                // Also try to set via input field that Streamlit can read
                const hiddenInput = document.getElementById('voice-text-fallback');
                if (hiddenInput) {
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(hiddenInput, text);
                    hiddenInput.dispatchEvent(new Event('input', { bubbles: true }));
                    hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
                
                // Clear the text area
                document.getElementById('voice-text-output').value = '';
                
                // Notify user
                document.getElementById('recording-status').textContent = 'Status: Text submitted! Use the input field below or refresh.';
            }
        }
        
        // Initialize on page load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeSpeechRecognition);
        } else {
            initializeSpeechRecognition();
        }
        </script>
        """
        
        # Use markdown with HTML for voice input (browser-based)
        st.markdown(voice_input_html, unsafe_allow_html=True)
        
        # Alternative: Simple text input for voice (fallback)
        st.markdown("**Or manually enter voice text:**")
        
        # Check for voice input from session storage
        voice_check_js = """
        <script>
        const voiceInput = sessionStorage.getItem('streamlit_voice_input');
        if (voiceInput) {
            sessionStorage.removeItem('streamlit_voice_input');
            const input = document.getElementById('voice-manual-input');
            if (input) {
                input.value = voiceInput;
            }
        }
        </script>
        """
        st.markdown(voice_check_js, unsafe_allow_html=True)
        
        voice_text_input = st.text_input(
            "Voice Input",
            key="voice_manual_input",
            placeholder="Type or use voice recognition above...",
            label_visibility="collapsed"
        )
        
        if st.button("✅ Submit Voice Message", use_container_width=True, key="submit_voice_text"):
            if voice_text_input:
                st.session_state.voice_input_submitted = voice_text_input
                st.session_state.voice_input_text = voice_text_input
                if on_voice_input:
                    on_voice_input(voice_text_input)
                st.rerun()
        
        return None
    
    def speak_text(self, text: str, use_browser_tts: bool = True):
        """
        Convert text to speech
        
        Args:
            text: Text to speak
            use_browser_tts: Use browser's built-in TTS (default) or Python TTS
        """
        if not st.session_state.voice_mode_enabled:
            return
        
        if use_browser_tts:
            # Use browser's Web Speech API for TTS
            tts_html = f"""
            <script>
            function speakText() {{
                if ('speechSynthesis' in window) {{
                    const utterance = new SpeechSynthesisUtterance({json.dumps(text)});
                    utterance.lang = 'en-US';
                    utterance.rate = 1.0;
                    utterance.pitch = 1.0;
                    utterance.volume = 1.0;
                    window.speechSynthesis.speak(utterance);
                }} else {{
                    console.log('Text-to-speech not supported in this browser');
                }}
            }}
            speakText();
            </script>
            """
            # Use markdown with HTML for TTS (browser-based)
            st.markdown(tts_html, unsafe_allow_html=True)
        else:
            # Fallback: Use Python TTS (requires pyttsx3)
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
            except ImportError:
                st.warning("pyttsx3 not installed. Install with: pip install pyttsx3")
            except Exception as e:
                st.warning(f"TTS error: {str(e)}")
    
    def render_voice_output_controls(self, text: str):
        """Render controls for voice output"""
        if not st.session_state.voice_mode_enabled:
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔊 Read Aloud", key="read_aloud_button"):
                self.speak_text(text)
        
        with col2:
            # Voice settings
            with st.expander("⚙️ Voice Settings"):
                voice_rate = st.slider("Speech Rate", 0.5, 2.0, 1.0, 0.1)
                voice_pitch = st.slider("Pitch", 0.5, 2.0, 1.0, 0.1)
                voice_volume = st.slider("Volume", 0.0, 1.0, 1.0, 0.1)
                
                if st.button("Apply Settings"):
                    st.session_state.voice_settings = {
                        'rate': voice_rate,
                        'pitch': voice_pitch,
                        'volume': voice_volume
                    }
                    st.success("Voice settings saved!")
    
    def get_voice_input(self) -> Optional[str]:
        """Get the last voice input text"""
        return st.session_state.get('voice_input_text')
    
    def clear_voice_input(self):
        """Clear voice input"""
        st.session_state.voice_input_text = ""
        st.session_state.last_voice_input = None

