"""
OpenAI Deep Research Handler for Streamlit
==========================================

Streamlit component for OpenAI deep research brand analysis.
Provides a user interface for conducting comprehensive brand research
using OpenAI's o3-deep-research and o4-mini-deep-research models.
"""

import streamlit as st
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai_deep_research import OpenAIBrandResearcher, BrandResearchConfig


class OpenAIDeepResearchHandler:
    """Streamlit handler for OpenAI deep research brand analysis."""
    
    def __init__(self):
        self.researcher = None
        self.config = None

    def render_interface(self):
        """Render the OpenAI deep research interface."""
        st.markdown("### OpenAI Deep Research (Brand Analysis)")
        st.write("Conduct comprehensive brand research using OpenAI's advanced deep research models with web search, code interpretation, and multi-step analysis.")
        
        # Configuration panel
        with st.expander("🔧 Research Configuration", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                model = st.selectbox(
                    "Deep Research Model",
                    ["o3-deep-research", "o4-mini-deep-research"],
                    index=0,
                    help="o3-deep-research: Most capable, o4-mini-deep-research: Faster and cheaper"
                )
                
                background_mode = st.checkbox(
                    "Background Mode",
                    value=True,
                    help="Run research in background mode for long-running tasks"
                )
                
                max_tool_calls = st.number_input(
                    "Max Tool Calls",
                    min_value=10,
                    max_value=100,
                    value=30,
                    help="Maximum number of tool calls (web search, code interpreter, etc.)"
                )
                
                # Polling configuration
                max_wait_time = st.number_input(
                    "Max Wait Time (minutes)",
                    min_value=5,
                    max_value=120,
                    value=60,
                    help="Maximum time to wait for research completion"
                )
            
            with col2:
                include_web_search = st.checkbox(
                    "Web Search",
                    value=True,
                    help="Enable web search capabilities"
                )
                
                include_code_interpreter = st.checkbox(
                    "Code Interpreter",
                    value=True,
                    help="Enable code execution for data analysis"
                )
                
                timeout = st.number_input(
                    "Timeout (seconds)",
                    min_value=300,
                    max_value=7200,
                    value=3600,
                    help="Request timeout in seconds"
                )
                
                poll_interval = st.number_input(
                    "Poll Interval (seconds)",
                    min_value=10,
                    max_value=300,
                    value=30,
                    help="Time between status checks when polling"
                )
        
        # Research input
        st.markdown("#### Research Target")
        brand_url = st.text_input(
            "Brand Website URL:",
            value="https://thedeconstruct.in/",
            help="Enter the brand's official website URL"
        )
        
        brand_name = st.text_input(
            "Brand Name (optional):",
            value="",
            help="Optional: Provide the brand name for better context"
        )
        
        # Custom research focus
        custom_focus = st.text_area(
            "Custom Research Focus (optional):",
            value="",
            height=100,
            help="Specify any particular aspects you want the research to focus on"
        )
        
        # Research actions
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Start Deep Research", type="primary"):
                if not brand_url:
                    st.error("Please enter a brand website URL")
                    return
                    
                if not os.getenv("OPENAI_API_KEY"):
                    st.error("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
                    return
                
                try:
                    # Create configuration
                    self.config = BrandResearchConfig(
                        model=model,
                        background=background_mode,
                        max_tool_calls=max_tool_calls,
                        include_web_search=include_web_search,
                        include_code_interpreter=include_code_interpreter,
                        timeout=timeout
                    )
                    
                    # Initialize researcher
                    self.researcher = OpenAIBrandResearcher(self.config)
                    
                    # Store configuration in session state
                    st.session_state.openai_config = self.config
                    st.session_state.openai_researcher = self.researcher
                    
                    # Store polling parameters
                    st.session_state.max_wait_time = max_wait_time * 60  # Convert to seconds
                    st.session_state.poll_interval = poll_interval
                    
                    # Run research
                    self._run_research(brand_url, brand_name, custom_focus)
                    
                except Exception as e:
                    st.error(f"Failed to initialize research: {str(e)}")
                    return
        
        with col2:
            # Manual polling section
            st.markdown("**Manual Polling**")
            response_id_input = st.text_input(
                "Response ID to poll:",
                value="",
                help="Enter a response ID from a previous research task to check its status"
            )
            
            if st.button("🔄 Poll for Results") and response_id_input:
                self._poll_existing_response(response_id_input, max_wait_time * 60, poll_interval)
        
        # Display results
        self._display_research_results()
        
        # Display exports
        self._display_exports()

    def _run_research(self, brand_url: str, brand_name: str, custom_focus: str):
        """Run the deep research and handle the results."""
        
        # Get polling parameters
        max_wait_time = st.session_state.get('max_wait_time', 3600)
        poll_interval = st.session_state.get('poll_interval', 30)
        
        # Create progress containers
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        with status_container:
            status_display = st.empty()
        
        try:
            # Modify the researcher's prompt if custom focus is provided
            if custom_focus and st.session_state.openai_researcher:
                # Store custom focus for later use
                st.session_state.custom_research_focus = custom_focus
            
            # Run the research with polling
            import nest_asyncio
            nest_asyncio.apply()
            
            # Create a custom async function for polling with progress updates
            async def run_with_progress():
                try:
                    status_text.text("🚀 Starting research task...")
                    progress_bar.progress(0.1)
                    
                    # Start the research with polling
                    result = await st.session_state.openai_researcher.research_brand_with_polling(
                        brand_url, 
                        brand_name,
                        max_wait_time=max_wait_time,
                        poll_interval=poll_interval,
                        ui_update_callback=update_polling_status
                    )
                    
                    return result
                    
                except Exception as e:
                    status_text.text(f"❌ Error during research: {str(e)}")
                    progress_bar.progress(1.0)
                    raise
            
            # Create a polling status display function
            def update_polling_status(response_id: str, elapsed_time: float, max_time: float):
                """Update the UI with polling status."""
                progress = min(0.1 + (elapsed_time / max_time) * 0.8, 0.9)  # Reserve 10% for completion
                progress_bar.progress(progress)
                
                elapsed_minutes = elapsed_time / 60
                max_minutes = max_time / 60
                status_text.text(f"🔄 Polling for completion... ({elapsed_minutes:.1f}/{max_minutes:.1f} min)")
                
                # Create a status display
                with status_display:
                    st.info(f"""
                    **Research Status**: Polling for completion  
                    **Response ID**: `{response_id}`  
                    **Elapsed Time**: {elapsed_minutes:.1f} minutes  
                    **Max Wait Time**: {max_minutes:.1f} minutes  
                    **Status**: Research in progress...
                    """)
            
            # Store the update function for use in polling
            st.session_state.update_polling_status = update_polling_status
            
            # Run the async function
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(run_with_progress())
            
            # Store results in session state
            st.session_state.openai_research_result = result
            
            # Handle different result statuses
            if result.get("status") == "completed":
                progress_bar.progress(1.0)
                status_text.text("✅ Deep research completed successfully!")
                st.success("✅ Deep research completed successfully!")
                
                # Auto-save results
                try:
                    json_path = st.session_state.openai_researcher.save_research_report(result)
                    st.session_state.openai_research_json_path = json_path
                    
                    # Save markdown report
                    markdown_content = st.session_state.openai_researcher.extract_markdown_report(result)
                    markdown_path = json_path.replace(".json", ".md")
                    
                    with open(markdown_path, "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                    
                    st.session_state.openai_research_md_path = markdown_path
                    
                    st.info(f"💾 Reports saved to runs/ directory")
                    
                except Exception as e:
                    st.warning(f"Auto-save failed: {str(e)}")
                
                # Display polling time if available
                if "polling_time" in result:
                    polling_minutes = result["polling_time"] / 60
                    st.info(f"⏱️ Total research time: {polling_minutes:.1f} minutes")
                
            elif result.get("status") == "timeout":
                progress_bar.progress(1.0)
                status_text.text("⏰ Research timed out")
                st.warning(f"⏰ Research timed out after {max_wait_time/60:.1f} minutes")
                st.write(f"Response ID: `{result.get('response_id')}`")
                st.write("You can check the OpenAI dashboard for completion status.")
                
            elif result.get("status") == "failed":
                progress_bar.progress(1.0)
                status_text.text("❌ Research failed")
                st.error(f"❌ Research failed: {result.get('error', 'Unknown error')}")
                
            else:
                progress_bar.progress(1.0)
                status_text.text("❌ Research failed")
                st.error(f"❌ Research failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            progress_bar.progress(1.0)
            status_text.text(f"❌ Error: {str(e)}")
            st.error(f"Research error: {str(e)}")

    def _poll_existing_response(self, response_id: str, max_wait_time: int, poll_interval: int):
        """Poll for an existing response ID."""
        
        # Create progress containers
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        with status_container:
            status_display = st.empty()
        
        try:
            # Create researcher if not exists
            if not hasattr(st.session_state, 'openai_researcher') or not st.session_state.openai_researcher:
                config = BrandResearchConfig()
                st.session_state.openai_researcher = OpenAIBrandResearcher(config)
            
            # Create polling status display function
            def update_polling_status(response_id: str, elapsed_time: float, max_time: float):
                """Update the UI with polling status."""
                progress = min(0.1 + (elapsed_time / max_time) * 0.8, 0.9)
                progress_bar.progress(progress)
                
                elapsed_minutes = elapsed_time / 60
                max_minutes = max_time / 60
                status_text.text(f"🔄 Polling for completion... ({elapsed_minutes:.1f}/{max_minutes:.1f} min)")
                
                with status_display:
                    st.info(f"""
                    **Research Status**: Polling for completion  
                    **Response ID**: `{response_id}`  
                    **Elapsed Time**: {elapsed_minutes:.1f} minutes  
                    **Max Wait Time**: {max_minutes:.1f} minutes  
                    **Status**: Research in progress...
                    """)
            
            # Run polling
            import nest_asyncio
            nest_asyncio.apply()
            
            async def poll_existing():
                status_text.text("🔄 Starting to poll existing response...")
                progress_bar.progress(0.1)
                
                result = await st.session_state.openai_researcher.poll_for_completion(
                    response_id, 
                    max_wait_time, 
                    poll_interval, 
                    update_polling_status
                )
                
                return result
            
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(poll_existing())
            
            # Store results in session state
            st.session_state.openai_research_result = result
            
            # Handle different result statuses
            if result.get("status") == "completed":
                progress_bar.progress(1.0)
                status_text.text("✅ Research completed successfully!")
                st.success("✅ Research completed successfully!")
                
                # Auto-save results
                try:
                    json_path = st.session_state.openai_researcher.save_research_report(result)
                    markdown_content = st.session_state.openai_researcher.extract_markdown_report(result)
                    markdown_path = json_path.replace(".json", ".md")
                    
                    with open(markdown_path, "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                    
                    st.info(f"💾 Reports saved to runs/ directory")
                    
                except Exception as e:
                    st.warning(f"Auto-save failed: {str(e)}")
                
            elif result.get("status") == "timeout":
                progress_bar.progress(1.0)
                status_text.text("⏰ Research timed out")
                st.warning(f"⏰ Research timed out after {max_wait_time/60:.1f} minutes")
                
            elif result.get("status") == "failed":
                progress_bar.progress(1.0)
                status_text.text("❌ Research failed")
                st.error(f"❌ Research failed: {result.get('error', 'Unknown error')}")
                
            else:
                progress_bar.progress(1.0)
                status_text.text("❌ Research failed")
                st.error(f"❌ Research failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            progress_bar.progress(1.0)
            status_text.text(f"❌ Error: {str(e)}")
            st.error(f"Polling error: {str(e)}")

    def _display_research_results(self):
        """Display the research results."""
        result = st.session_state.get('openai_research_result')
        if not result:
            return
        
        st.markdown("### 📊 Research Results")
        
        # Status and metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", result.get('status', 'Unknown'))
        with col2:
            st.metric("Model", result.get('model', 'Unknown'))
        with col3:
            content_length = result.get('metadata', {}).get('content_length', 0)
            st.metric("Content Length", f"{content_length:,} chars")
        
        # Main content display
        if result.get("status") == "completed":
            main_content = result.get("main_content", "")
            
            if main_content:
                # Display as markdown
                st.markdown("#### 📄 Research Report")
                st.markdown(main_content)
            else:
                st.warning("No content generated in the research result.")
        
        # Tool calls and metadata
        tool_calls = result.get("tool_calls", [])
        if tool_calls:
            with st.expander(f"🔧 Tool Calls ({len(tool_calls)} total)"):
                for i, tool_call in enumerate(tool_calls, 1):
                    st.write(f"**{i}. {tool_call.get('type', 'Unknown')}**")
                    if isinstance(tool_call.get('data'), dict):
                        st.json(tool_call['data'])
                    else:
                        st.text(str(tool_call.get('data', '')))

    def _display_exports(self):
        """Display export options."""
        result = st.session_state.get('openai_research_result')
        if not result:
            return
        
        st.markdown("### 📤 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Download JSON Report"):
                if result.get("status") == "completed":
                    st.download_button(
                        label="Download Research JSON",
                        data=json.dumps(result, indent=2),
                        file_name=f"openai_brand_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        
        with col2:
            if result.get("status") == "completed" and result.get("main_content"):
                markdown_content = st.session_state.openai_researcher.extract_markdown_report(result)
                st.download_button(
                    label="📝 Download Markdown Report",
                    data=markdown_content,
                    file_name=f"openai_brand_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
        
        with col3:
            if st.button("💾 Save to runs/ Directory"):
                try:
                    if st.session_state.openai_researcher and result.get("status") == "completed":
                        json_path = st.session_state.openai_researcher.save_research_report(result)
                        markdown_content = st.session_state.openai_researcher.extract_markdown_report(result)
                        markdown_path = json_path.replace(".json", ".md")
                        
                        with open(markdown_path, "w", encoding="utf-8") as f:
                            f.write(markdown_content)
                        
                        st.success(f"✅ Saved to: {json_path}")
                        st.success(f"✅ Saved to: {markdown_path}")
                    else:
                        st.warning("No completed research results to save.")
                except Exception as e:
                    st.error(f"Save failed: {str(e)}")

    def render_webhook_setup(self):
        """Render webhook setup instructions for background mode."""
        st.markdown("### 🔗 Webhook Setup (for Background Mode)")
        st.write("""
        For background mode research, you can set up webhooks to receive notifications when research completes.
        
        **Setup Steps:**
        1. Create a webhook endpoint in your application
        2. Configure the webhook URL in your OpenAI dashboard
        3. The webhook will receive a POST request when research completes
        
        **Example webhook payload:**
        ```json
        {
            "id": "response_id",
            "status": "completed",
            "output": "research_results_here"
        }
        ```
        """)

    def render_research_examples(self):
        """Render examples of research types."""
        st.markdown("### 📚 Research Examples")
        
        examples = [
            {
                "title": "Skincare Brand Analysis",
                "url": "https://thedeconstruct.in/",
                "focus": "Product ingredients, target demographics, competitive positioning, social media strategy"
            },
            {
                "title": "EdTech Company Research", 
                "url": "https://www.eurokidsindia.com/",
                "focus": "Educational programs, franchise model, market expansion, customer acquisition"
            },
            {
                "title": "E-commerce Platform Analysis",
                "url": "https://example-ecommerce.com/",
                "focus": "Product catalog, pricing strategy, customer reviews, logistics network"
            }
        ]
        
        for i, example in enumerate(examples, 1):
            with st.expander(f"{i}. {example['title']}"):
                st.write(f"**URL:** {example['url']}")
                st.write(f"**Research Focus:** {example['focus']}")
                
                if st.button(f"Use Example {i}", key=f"example_{i}"):
                    st.session_state.brand_url = example['url']
                    st.session_state.brand_name = example['title']
                    st.session_state.custom_focus = example['focus']
                    st.rerun()


def main():
    """Main function for testing the handler."""
    handler = OpenAIDeepResearchHandler()
    
    st.set_page_config(
        page_title="OpenAI Deep Research",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("OpenAI Deep Research - Brand Analysis")
    
    # Render main interface
    handler.render_interface()
    
    # Render additional sections
    with st.sidebar:
        handler.render_research_examples()
        handler.render_webhook_setup()


if __name__ == "__main__":
    main()
