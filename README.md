# 🚀 Company Research Assistant

An intelligent AI-powered research assistant that helps you gather comprehensive information about companies through natural conversation and generate detailed account plans. Built with Streamlit, LangChain, and Groq's Llama 3.3 70B model.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.51.0-red)
![LangChain](https://img.shields.io/badge/langchain-1.0.8-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ Features

### 🎯 Core Capabilities
- **Interactive Company Research**: Gather information from multiple sources and synthesize findings
- **Account Plan Generation**: Create detailed, editable account plans based on research
- **Natural Language Interface**: Chat with the AI assistant about companies and industries
- **Voice Input/Output**: Speak your queries and hear responses (powered by AssemblyAI & ElevenLabs)
- **Real-time Updates**: Get progress updates during research process
- **Source Tracking**: All research includes citations and sources

### 🎙️ Voice Features
- **Voice Input**: Record queries using the built-in microphone feature
- **Text-to-Speech**: Listen to AI responses with multiple voice options
- **Seamless Integration**: Toggle between text and voice modes effortlessly

### 📊 Research Modes
1. **Chat Mode**: Natural conversation with the AI assistant
2. **Form Mode**: Structured research requests with customizable parameters

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Windows/Mac/Linux OS
- Git
- Microphone (for voice features)
- ~2GB free disk space

### Complete Setup Commands

#### Step 1: Clone the Repository
```bash
# Clone the repository
git clone https://github.com/yourusername/company-research-assistant.git
cd company-research-assistant

# Or download and extract ZIP
# Then navigate to the folder
cd account_plan_generator_project
```

#### Step 2: Create Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt)
python -m venv venv
venv\Scripts\activate.bat

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Verify activation (you should see (venv) in your terminal)
```

#### Step 3: Install All Dependencies
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# If you encounter issues, install core packages first:
pip install streamlit==1.51.0
pip install langchain==1.0.8
pip install langgraph==1.0.3
pip install langchain-groq==1.2.0

# Then install remaining packages:
pip install -r requirements.txt

# For voice features specifically:
pip install assemblyai
pip install elevenlabs
pip install streamlit-audiorec
```

#### Step 4: Set Up Environment Variables
```bash
# Windows (PowerShell)
Copy-Item .env.example .env
notepad .env

# Windows (Command Prompt)
copy .env.example .env
notepad .env

# Mac/Linux
cp .env.example .env
nano .env  # or vim .env
```

Add your API keys to the `.env` file:
```env
# Required - Get free key at https://console.groq.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional Voice Features
ASSEMBLY_API=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ELEVENLABS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional Enhanced Search
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxx
SERP_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### Step 5: Run the Application
```bash
# Standard run
streamlit run app.py

# Run on specific port if 8501 is busy
streamlit run app.py --server.port 8502

# Run with specific settings
streamlit run app.py --server.maxUploadSize 50 --server.enableXsrfProtection false

# Run in production mode
streamlit run app.py --server.headless true --server.address 0.0.0.0
```

The app will automatically open in your browser at `http://localhost:8501`

### 🔧 Troubleshooting Commands

```bash
# Check Python version (should be 3.10+)
python --version

# Check if virtual environment is activated
which python  # Mac/Linux
where python  # Windows

# List installed packages
pip list

# Check for missing dependencies
pip check

# Reinstall all dependencies (fresh install)
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Clear Streamlit cache
streamlit cache clear

# Check if port is in use (Windows)
netstat -ano | findstr :8501

# Check if port is in use (Mac/Linux)
lsof -i :8501

# Kill process using port (Windows)
taskkill /F /PID <PID_NUMBER>

# Kill process using port (Mac/Linux)
kill -9 <PID_NUMBER>
```

### 🐳 Docker Setup (Optional)

```bash
# Build Docker image
docker build -t company-research-assistant .

# Run container
docker run -p 8501:8501 --env-file .env company-research-assistant

# Run with volume mount for persistence
docker run -p 8501:8501 -v $(pwd)/research_documents:/app/research_documents --env-file .env company-research-assistant
```

### 📦 Quick Start Script

Create a `start.sh` (Mac/Linux) or `start.bat` (Windows):

**Windows (start.bat):**
```batch
@echo off
echo Starting Company Research Assistant...
call venv\Scripts\activate.bat
streamlit run app.py
pause
```

**Mac/Linux (start.sh):**
```bash
#!/bin/bash
echo "Starting Company Research Assistant..."
source venv/bin/activate
streamlit run app.py
```

Make it executable (Mac/Linux):
```bash
chmod +x start.sh
./start.sh
```

## 🔑 Getting API Keys

### Required: Groq (Free)
1. Visit [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to API Keys section
4. Click "Create API Key"
5. Copy the key (starts with `gsk_`)
6. Add to `.env` as `GROQ_API_KEY`

### Verify Your Setup
```bash
# Create a test script
cat > verify_setup.py << 'EOF'
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("🔍 Checking setup...")
print("-" * 40)

# Check Python version
python_version = sys.version_info
print(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")

# Check required packages
required = ['streamlit', 'langchain', 'langgraph', 'langchain_groq']
for package in required:
    try:
        __import__(package.replace('_', '-'))
        print(f"✓ {package} installed")
    except ImportError:
        print(f"✗ {package} missing")

# Check API keys
if os.getenv('GROQ_API_KEY'):
    print("✓ GROQ_API_KEY set")
else:
    print("✗ GROQ_API_KEY not set")

if os.getenv('ASSEMBLY_API'):
    print("✓ ASSEMBLY_API set (optional)")
    
if os.getenv('ELEVENLABS_API_KEY'):
    print("✓ ELEVENLABS_API_KEY set (optional)")

print("-" * 40)
print("Setup verification complete!")
EOF

# Run verification
python verify_setup.py
```

### Optional: Voice Features
- **AssemblyAI**: [assemblyai.com](https://www.assemblyai.com) - For voice transcription
- **ElevenLabs**: [elevenlabs.io](https://elevenlabs.io) - For text-to-speech

### Optional: Enhanced Search
- **Perplexity**: [perplexity.ai](https://www.perplexity.ai) - For advanced web search
- **SERP API**: [serpapi.com](https://serpapi.com) - For search engine results

## 📖 Usage Guide

### Chat Mode
1. Select **Chat Mode** from the sidebar
2. Type your query or use voice input
3. The AI will respond conversationally
4. Ask follow-up questions or request research

### Form Mode (Research)
1. Select **Form Mode** from the sidebar
2. Enter your research query (e.g., "Microsoft company analysis")
3. Configure settings:
   - Max iterations (depth of research)
   - Search API preference
4. Click **Start Research**
5. View and edit the generated account plan

### Voice Features
1. Click the START button to begin recording
2. Speak your query clearly
3. Click STOP when finished
4. The AI will transcribe and process your request
5. Enable voice output to hear responses

## 🏗️ Project Structure

```
company-research-assistant/
├── app.py                      # Main Streamlit application
├── config.json                 # Model and provider configuration
├── requirements.txt            # Python dependencies
├── .env                        # API keys (create this)
│
├── streamlit_app_components/   # UI components
│   ├── __init__.py
│   ├── chat_interface.py       # Chat UI and voice features
│   ├── account_plan_editor.py  # Account plan editing interface
│   ├── deep_research_handler.py # Research workflow UI
│   └── research_display.py     # Research results display
│
├── product_research/           # Core research logic
│   ├── __init__.py
│   ├── model_service.py        # Model configuration service
│   ├── config_schema.py        # Configuration schemas
│   ├── deep_research_service.py # Main research service
│   ├── document_storage.py     # Document management
│   └── open_deep_research/     # Research workflow components
│       ├── deep_researcher.py  # Core research logic
│       ├── graph.py            # Research workflow graph
│       ├── models.py           # Data models
│       ├── nodes.py            # Workflow nodes
│       ├── prompts.py          # AI prompts
│       ├── state.py            # State management
│       └── utils.py            # Utility functions
│
└── research_documents/         # Generated research storage
    ├── documents/              # Research documents
    ├── exports/                # Exported reports
    └── runs/                   # Research run history
```

## 🎯 Example Use Cases

### Company Research
```
"Research Microsoft's cloud computing strategy and competitive position"
"Analyze Tesla's financial performance over the last 3 years"
"What are Apple's main revenue streams and growth areas?"
```

### Account Planning
```
"Create an account plan for selling enterprise software to Google"
"Develop a strategic account plan for Amazon Web Services"
"Generate a partnership proposal for Meta's AI initiatives"
```

### Industry Analysis
```
"Compare major players in the electric vehicle market"
"Analyze trends in the SaaS industry"
"Research emerging AI companies in healthcare"
```

## ⚙️ Configuration

### Customizing Research Settings
Edit `config.json` to adjust:
- Model parameters (using Groq Llama 3.3 70B)
- Research depth (max_iterations)
- Timeout settings
- Search API preferences

### Voice Settings
Configure voice options in the sidebar:
- Choose from 8 different AI voices
- Adjust speech speed
- Toggle auto-play for responses

## 🐛 Troubleshooting

### Common Issues & Solutions

**1. ModuleNotFoundError**
```bash
# Ensure virtual environment is activated
# Windows
.\venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate

# Reinstall requirements
pip install --upgrade -r requirements.txt
```

**2. Voice Input Not Working**
```bash
# Install audio dependencies
pip install assemblyai streamlit-audiorec

# Check microphone permissions in browser
# Chrome: Settings > Privacy > Site Settings > Microphone
# Allow localhost:8501

# Test AssemblyAI connection
python -c "import assemblyai as aai; print('AssemblyAI OK')"
```

**3. Groq Rate Limit Errors**
```bash
# Check your usage at https://console.groq.com
# Free tier: 100K tokens/day
# Solutions:
# - Wait for reset (resets daily)
# - Reduce max_iterations in config.json
# - Use shorter queries
```

**4. Port Already in Use**
```bash
# Find process using port
netstat -ano | findstr :8501  # Windows
lsof -i :8501                  # Mac/Linux

# Use different port
streamlit run app.py --server.port 8502
```

**5. ImportError: cannot import name 'Command'**
```bash
# Upgrade langgraph
pip install --upgrade langgraph==1.0.3
```

**6. Streamlit Connection Error**
```bash
# Clear cache and restart
streamlit cache clear
streamlit run app.py --server.baseUrlPath=""
```

**7. API Key Errors**
```bash
# Verify .env file exists
ls -la .env  # Mac/Linux
dir .env     # Windows

# Check API key format
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('GROQ_API_KEY set:', bool(os.getenv('GROQ_API_KEY')))"
```

**8. Memory/Performance Issues**
```bash
# Run with limited resources
streamlit run app.py --server.maxMessageSize 50 --server.maxUploadSize 50

# Clear old research documents
rm -rf research_documents/runs/*  # Mac/Linux
rmdir /s research_documents\runs   # Windows
```

## 📦 Dependencies

Main packages:
- `streamlit==1.51.0` - Web UI framework
- `langchain==1.0.8` - AI orchestration
- `langchain-groq==1.2.0` - Groq LLM integration
- `langgraph==1.0.3` - Workflow management
- `streamlit-audiorec==0.1.3` - Voice recording
- `assemblyai` - Voice transcription
- `elevenlabs` - Text-to-speech
- `duckduckgo-search` - Web search

## 🧪 Development & Testing

### Development Setup
```bash
# Clone for development
git clone https://github.com/yourusername/company-research-assistant.git
cd company-research-assistant

# Create development environment
python -m venv venv-dev
source venv-dev/bin/activate  # or .\venv-dev\Scripts\Activate.ps1 on Windows

# Install in development mode
pip install -r requirements.txt
pip install pytest black flake8  # Development tools

# Run with auto-reload
streamlit run app.py --server.runOnSave true
```

### Testing Commands
```bash
# Test Groq connection
python -c "from langchain_groq import ChatGroq; llm = ChatGroq(model='llama-3.3-70b-versatile'); print(llm.invoke('Say hello').content)"

# Test voice transcription (requires AssemblyAI key)
python -c "import assemblyai as aai; aai.settings.api_key = 'YOUR_KEY'; print('AssemblyAI connected')"

# Test the research workflow
python -c "from product_research.deep_research_service import DeepResearchService; print('Research service OK')"

# Run a simple query test
cat > test_query.py << 'EOF'
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv('GROQ_API_KEY'),
    model='llama-3.3-70b-versatile'
)

response = llm.invoke("What is Microsoft's main business?")
print(response.content)
EOF

python test_query.py
```

### Code Quality
```bash
# Format code with black
black .

# Check code style
flake8 . --max-line-length=120

# Type checking
mypy app.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Install development dependencies (`pip install -r requirements-dev.txt`)
4. Make your changes
5. Run tests (`pytest`)
6. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
7. Push to the branch (`git push origin feature/AmazingFeature`)
8. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Groq** - For providing free, fast LLM inference with Llama 3.3 70B
- **Streamlit** - For the amazing web app framework
- **LangChain & LangGraph** - For AI orchestration and workflow tools
- **AssemblyAI** - For accurate voice transcription
- **ElevenLabs** - For natural text-to-speech voices
- **DuckDuckGo** - For free web search API

## 💡 Tips for Best Results

1. **Be specific** in your research queries for better results
2. **Use voice mode** for hands-free operation
3. **Edit sections** individually for precise modifications
4. **Export regularly** to save your research
5. **Monitor token usage** to avoid rate limits

## 📧 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Star the repository if you find it useful!
