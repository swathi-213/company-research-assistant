import streamlit as st
from dotenv import load_dotenv

from streamlit_app_components.deep_research_handler import DeepResearchHandler
# OpenAI Deep Research handler removed - using free Groq models instead
# from streamlit_app_components.openai_deep_research_handler import OpenAIDeepResearchHandler


def main():
    load_dotenv()
    st.set_page_config(page_title="Company Research Assistant", page_icon="🏢", layout="wide")

    # Custom CSS for better UI
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
        font-style: italic;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

    
    
    
    handler = DeepResearchHandler(project_manager=None)
    handler.render_deep_research_interface()



if __name__ == "__main__":
    main()


