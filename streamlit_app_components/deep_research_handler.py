"""
Deep Research Handler for Streamlit App
Handles the deep research 2.0 integration with real-time streaming
"""

import streamlit as st
import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
import time
import os
from dotenv import load_dotenv

# Import deep research service
from product_research.deep_research_service import DeepResearchService
from product_research.models.research_models import (
    StreamingEvent, ResearchStage, ResearchSession, ResearchDocument, ResearchResult
)
from product_research.model_service import ModelService
from product_research.document_storage import DocumentStorageService

# Import new components
from streamlit_app_components.chat_interface import ChatInterface
from streamlit_app_components.account_plan_editor import AccountPlanEditor
from streamlit_app_components.voice_interface import VoiceInterface

class DeepResearchHandler:
    """Handles deep research operations with real-time streaming"""

    def __init__(self, project_manager):
        self.project_manager = project_manager
        self.deep_research_service = DeepResearchService()
        self.model_service = ModelService()
        self.document_storage = DocumentStorageService()
        # Initialize new components
        self.chat_interface = ChatInterface()
        self.account_plan_editor = AccountPlanEditor()
        self.voice_interface = VoiceInterface()

    def _render_chat_mode(self):
        """Render conversational chat interface"""
        self.chat_interface.render_with_research_integration(self, self.model_service)
    
    def render_deep_research_interface(self):
        """Render the deep research interface with chat and form modes"""
        # Ensure .env is loaded for env-based API keys
        load_dotenv()
        mode_tabs = st.tabs(["💬 Chat Mode", "📝 Form Mode"])
        with mode_tabs[0]:
            self._render_chat_mode()
        with mode_tabs[1]:
            self._render_form_mode()
        def _render_chat_mode(self):
            """Render conversational chat interface"""
            self.chat_interface.render_with_research_integration(self, self.model_service)
    
    
    def _render_form_mode(self):
        """Render traditional form-based interface"""
        # Research query input with examples
        st.markdown("### Research Query")
        
        # Example queries
        example_queries = [
            "Create a detailed account plan for Tata Motors. Focus on their 2025 strategic goals, financial health, and key decision makers in IT.",
            "Research Microsoft's cloud strategy, recent acquisitions, and key executives in the Azure division.",
            "Generate an account plan for Apple Inc. focusing on their enterprise sales strategy and decision makers.",
            "Analyze Amazon's AWS business unit, financial performance, and competitive positioning.",
        ]
        
        col_query, col_examples = st.columns([3, 1])
        
        with col_query:
            research_query = st.text_area(
                "Enter your research question or topic:",
                placeholder="e.g., Create a detailed account plan for [Company Name]. Focus on their strategic goals, financial health, and key decision makers.",
                height=100,
                help="Be specific about the company and the type of information you need (Financials, Strategy, People, etc.).",
                value=st.session_state.get('research_query', '')
            )
            if research_query:
                st.session_state['research_query'] = research_query
        
        with col_examples:
            st.markdown("**💡 Example Queries**")
            for i, example in enumerate(example_queries):
                if st.button(f"Example {i+1}", key=f"example_{i}", use_container_width=True):
                    st.session_state['research_query'] = example
                    st.rerun()
        
        # Model selection and API provider switcher
        st.markdown("### AI Model Selection")
        api_providers = [
            "deepseek", "google", "anthropic", "groq", "perplexity", "openai"
        ]
        api_provider_display = {
            "deepseek": "DeepSeek",
            "google": "Google",
            "anthropic": "Anthropic",
            "groq": "Groq",
            "perplexity": "Perplexity",
            "openai": "OpenAI"
        }
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_api_provider = st.selectbox(
                "Choose AI Model",
                api_providers,
                format_func=lambda x: api_provider_display[x],
                index=api_providers.index("groq") if "groq" in api_providers else 0
            )
            st.session_state["selected_api_provider"] = selected_api_provider
            # Only show API provider switcher, remove model dropdown
            selected_model = selected_api_provider
            # Friendly fallback descriptions for each provider
            fallback_descriptions = {
                "deepseek": "DeepSeek: High-performance, multilingual AI for research and analysis.",
                "google": "Google: Advanced AI models for search and enterprise intelligence.",
                "anthropic": "Anthropic: Reliable, safety-focused AI for business and research.",
                "groq": "Groq: Free high-performance inference with Llama models. Fast and cost-effective for research tasks.",
                "perplexity": "Perplexity: AI-powered research and Q&A with web search integration.",
                "openai": "OpenAI: Industry-leading generative AI for deep research and analysis."
            }
            if hasattr(self.model_service, "get_model_description") and callable(getattr(self.model_service, "get_model_description")):
                try:
                    model_description = self.model_service.get_model_description(selected_model)
                    if model_description == "Unknown model" or not model_description:
                        model_description = fallback_descriptions.get(selected_model, f"No description available for {api_provider_display[selected_model]}")
                except Exception:
                    model_description = fallback_descriptions.get(selected_model, f"No description available for {api_provider_display[selected_model]}")
            else:
                model_description = fallback_descriptions.get(selected_model, f"No description available for {api_provider_display[selected_model]}")
            st.info(f"**{api_provider_display[selected_model]}**: {model_description}")
        
        with col2:
            # API Key input (with fallback to environment)
            api_env_map = {
                "deepseek": "DEEPSEEK_API_KEY",
                "google": "GOOGLE_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "groq": "GROQ_API_KEY",
                "perplexity": "PERPLEXITY_API_KEY",
                "openai": "OPENAI_API_KEY"
            }
            selected_api_provider = st.session_state.get("selected_api_provider", "groq")
            needed_env = api_env_map.get(selected_api_provider, "GROQ_API_KEY")
            env_api_key = os.environ.get(needed_env, "")
            st.markdown(f"**API Key Configuration for {selected_api_provider.title()}**")
            api_key_source = st.radio(
                "API Key Source",
                ["Environment Variable", "Manual Input"],
                index=0 if env_api_key else 1,
                help="Choose to use environment variable or enter API key manually",
                key=f"api_key_source_{selected_api_provider}"
            )
            if api_key_source == "Manual Input":
                api_key = st.text_input(
                    f"{needed_env}",
                    type="password",
                    help=f"Enter your {needed_env} here",
                    value=st.session_state.get(f'manual_{needed_env}', ''),
                    key=f"manual_api_key_{selected_api_provider}"
                )
                if api_key:
                    st.session_state[f'manual_{needed_env}'] = api_key
                    st.success("✓ API key entered")
                else:
                    st.warning("Please enter your API key")
            else:
                if env_api_key:
                    st.success(f"✓ Using {needed_env} from environment")
                    api_key = env_api_key
                else:
                    st.warning(f"⚠ Missing {needed_env} in environment")
                    st.info("💡 Switch to 'Manual Input' to enter your API key")
                    api_key = None
            # Store API key in session state for button click handler
            st.session_state[f'current_api_key_{selected_model}'] = api_key
        
        # Research configuration
        with st.expander("⚙️ Research Configuration", expanded=False):
            defaults = self.model_service.get_research_defaults()
            col1, col2 = st.columns(2)
            
            with col1:
                max_iterations = st.slider("Max Research Iterations", 1, 3, int(defaults.get("max_iterations", 1)), help="Number of research iterations to perform")
                max_tool_calls = st.slider("Max Tool Calls per Iteration", 1, 5, int(defaults.get("max_tool_calls", 3)), help="Maximum tool calls per research iteration")
                allow_clarification = st.checkbox("Allow Clarification", value=bool(defaults.get("allow_clarification", False)), help="Allow AI to ask clarifying questions")
            
            with col2:
                max_concurrent = st.slider("Max Concurrent Research Units", 1, 3, int(defaults.get("max_concurrent", 2)), help="Maximum concurrent research operations")
                timeout_minutes = st.slider("Timeout (minutes)", 5, 30, int(defaults.get("timeout_minutes", 15)), help="Maximum research time")
                search_api_options = ["duckduckgo", "tavily", "none"]
                default_api = str(defaults.get("search_api", "duckduckgo")).lower()
                default_idx = search_api_options.index(default_api) if default_api in search_api_options else 0
                search_api = st.selectbox("Search API", list(range(len(search_api_options))), index=default_idx, format_func=lambda i: search_api_options[i], help="Search API to use for web research (DuckDuckGo is free, no API key needed)")
                search_api = search_api_options[search_api]
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🔬 Start Deep Research", type="primary"):
                needed_env = self.model_service.get_required_api_key_env(selected_model) or "GROQ_API_KEY"
                # Get API key from session state (set in the API key configuration section)
                api_key_source = st.session_state.get(f'api_key_source_{selected_model}', 'Environment Variable')
                
                # Get API key from either manual input or environment
                if api_key_source == "Manual Input":
                    user_api_key = st.session_state.get(f'manual_{needed_env}', '')
                else:
                    user_api_key = os.environ.get(needed_env, "")
                
                if not research_query.strip():
                    st.error("❌ Please enter a research query")
                elif not user_api_key:
                    st.error(f"❌ Missing API key. Please provide {needed_env}")
                else:
                    self._start_deep_research(
                        research_query, selected_model, user_api_key,
                        max_iterations, max_tool_calls, max_concurrent,
                        allow_clarification, timeout_minutes, search_api
                    )
        
        with col2:
            if st.button("🔄 Reset"):
                self._reset_research_session()
                st.rerun()
        
        with col3:
            if st.button("📁 Save Research Document"):
                if st.session_state.get('deep_research_result'):
                    self._save_research_document()
                else:
                    st.warning("No research results to save")
        
        # Research History section
        with st.expander("📚 Research History", expanded=False):
            self._render_research_history()
        
        # Document management section
        with st.expander("📁 Document Management", expanded=False):
            self._render_document_management()
        
        # Display research progress and results
        self._display_research_progress()
        self._display_research_results()
        
        # Show account plan editor if results available
        if st.session_state.get('deep_research_result'):
            st.markdown("---")
            result = st.session_state.deep_research_result
            self.account_plan_editor.render_editor(result.final_report, result.research_id)
        
        self._display_stage_logs()
        self._display_tool_calls()
        self._display_crawl_log()
        
        # Display interactive conflict resolution if needed
        self._display_conflict_resolution()
    
    def _start_deep_research(self, query: str, model: str, api_key: str, 
                           max_iterations: int, max_tool_calls: int, max_concurrent: int,
                           allow_clarification: bool, timeout_minutes: int, search_api: str):
        """Start deep research with real-time streaming"""
        
        # Generate unique research ID
        research_id = f"research_{uuid.uuid4().hex[:8]}"
        
        # Initialize research session
        research_session = ResearchSession(
            research_id=research_id,
            query=query,
            model=model,
            api_key=api_key,
            start_time=datetime.now(),
            status="running"
        )
        
        # Store in session state
        st.session_state.deep_research_session = research_session
        st.session_state.deep_research_events = []
        st.session_state.deep_research_sources = []
        # Per-stage logs: { stage_name: [ {timestamp, type, content, metadata} ] }
        st.session_state.deep_research_stage_logs = {}
        # Tool calls log: [ {timestamp, tool, args, stage, message, result_preview, urls} ]
        st.session_state.deep_research_tool_calls = []
        # Crawl log entries: [ {from_page, link_text, to_url, section, status, title, validated, evidence} ]
        st.session_state.deep_research_crawl_log = []
        st.session_state.deep_research_progress = {
            "current_stage": ResearchStage.INITIALIZATION,
            "progress_percentage": 0,
            "stages_completed": [],
            "current_step": "Initializing research...",
            "sources_found": 0
        }
        
        # Create progress containers
        progress_container = st.container()
        events_container = st.container()
        sources_container = st.container()
        
        # Start research with enhanced loading state
        with st.spinner("🚀 Starting deep research... Please wait..."):
            try:
                # Show initial status
                status_placeholder = st.empty()
                status_placeholder.info("⏳ Initializing research session...")
                
                # Run async research
                asyncio.run(self._run_research_streaming(
                    query, model, api_key, research_id,
                    progress_container, events_container, sources_container
                ))
                
                status_placeholder.empty()
            except Exception as e:
                st.error(f"Research failed: {str(e)}")
                st.session_state.deep_research_session.status = "error"
    
    async def _run_research_streaming(self, query: str, model: str, api_key: str, research_id: str,
                                    progress_container, events_container, sources_container):
        """Run research with real-time streaming updates"""
        
        try:
            # Create progress placeholders
            progress_bar = progress_container.progress(0)
            status_text = progress_container.empty()
            events_placeholder = events_container.empty()
            sources_placeholder = sources_container.empty()
            
            # Stream research events
            async for event in self.deep_research_service.stream_research(query, model, api_key, research_id):
                # Update progress
                self._update_research_progress(event)
                
                # Update UI
                progress_bar.progress(st.session_state.deep_research_progress["progress_percentage"] / 100)
                status_text.text(f"Stage: {event.stage.value} - {event.content}")
                
                # Store event
                st.session_state.deep_research_events.append(event)
                # Store per-stage log entry
                stage_key = event.stage.value if event.stage else "unknown"
                stage_bucket = st.session_state.deep_research_stage_logs.get(stage_key, [])
                stage_bucket.append({
                    "timestamp": event.timestamp,
                    "type": event.type,
                    "content": event.content,
                    "metadata": event.metadata or {}
                })
                st.session_state.deep_research_stage_logs[stage_key] = stage_bucket
                # Capture tool calls and results
                try:
                    if event.metadata and isinstance(event.metadata, dict):
                        tool_name = event.metadata.get("tool")
                        if tool_name:
                            st.session_state.deep_research_tool_calls.append({
                                "timestamp": event.timestamp,
                                "tool": tool_name,
                                "args": {k: v for k, v in (event.metadata or {}).items() if k not in ["step", "tool"]},
                                "stage": stage_key,
                                "message": event.content
                            })
                    # Treat sources_found as a tool result (e.g., web_fetch/search result)
                    if event.type == "sources_found" and event.metadata and "sources" in event.metadata:
                        st.session_state.deep_research_tool_calls.append({
                            "timestamp": event.timestamp,
                            "tool": "sources_discovered",
                            "args": {},
                            "stage": stage_key,
                            "message": event.content,
                            "urls": event.metadata.get("sources", [])
                        })
                    # Also include api_call traces as low-level tool telemetry
                    if event.type == "api_call":
                        st.session_state.deep_research_tool_calls.append({
                            "timestamp": event.timestamp,
                            "tool": "api_call",
                            "args": event.metadata or {},
                            "stage": stage_key,
                            "message": event.content
                        })
                    # Capture crawl log entries if present in metadata
                    if event.metadata and isinstance(event.metadata, dict) and "crawl_log" in event.metadata:
                        crawl_items = event.metadata.get("crawl_log") or []
                        if isinstance(crawl_items, list):
                            # Normalize entries to expected keys
                            normalized = []
                            for it in crawl_items:
                                if isinstance(it, dict):
                                    normalized.append({
                                        "from_page": it.get("from_page") or it.get("source") or "",
                                        "link_text": it.get("link_text") or it.get("anchor") or "",
                                        "to_url": it.get("to_url") or it.get("url") or "",
                                        "section": it.get("section") or it.get("section_guess") or "",
                                        "status": it.get("status") or it.get("http_status") or "",
                                        "title": it.get("title") or "",
                                        "validated": it.get("validated"),
                                        "evidence": it.get("evidence") or ""
                                    })
                            st.session_state.deep_research_crawl_log.extend(normalized)
                except Exception:
                    pass
                
                # Update events display
                self._display_events(events_placeholder)
                
                # Update sources if found
                if event.type == "sources_found" and event.metadata and "sources" in event.metadata:
                    st.session_state.deep_research_sources.extend(event.metadata["sources"])
                    self._display_sources(sources_placeholder)
                
                # Check for conflicts and pause if needed
                conflict_info = self._detect_conflicts(event)
                if conflict_info:
                    st.session_state.research_paused = True
                    st.session_state.conflict_detected = conflict_info
                    # Break to allow user input
                    break
                
                # Yield control briefly to allow Streamlit UI to update without full rerun
                await asyncio.sleep(0)
            
            # Research completed
            st.session_state.deep_research_session.status = "completed"
            st.session_state.deep_research_session.end_time = datetime.now()
            
            # Extract final report
            final_report = self._extract_final_report()
            if final_report:
                st.session_state.deep_research_result = ResearchResult(
                    research_id=research_id,
                    query=query,
                    final_report=final_report,
                    sources=st.session_state.deep_research_sources,
                    stages_completed=st.session_state.deep_research_progress["stages_completed"],
                    total_time_seconds=(datetime.now() - st.session_state.deep_research_session.start_time).total_seconds(),
                    model_used=model,
                    created_at=datetime.now()
                )
                
                # Speak completion if voice mode enabled
                if st.session_state.get('voice_mode_enabled'):
                    self.voice_interface.speak_text("Research completed successfully!")
            
            st.success("🎉 Deep research completed successfully!")
            # Auto-save JSON artifacts (stages and result) upon completion
            try:
                self._save_stages_and_result_json()
            except Exception as e:
                # Non-fatal – provide UI button as alternative
                pass
            
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ Research Error: {error_msg}")
            
            # Enhanced error display
            with st.expander("🔍 Error Details", expanded=True):
                st.code(error_msg)
                
                # Provide helpful suggestions based on error type
                if "API key" in error_msg.lower() or "authentication" in error_msg.lower():
                    st.warning("💡 **API Key Issue:** Check that your Groq API key is correct and has sufficient credits.")
                elif "model" in error_msg.lower() and "decommissioned" in error_msg.lower():
                    st.warning("💡 **Model Issue:** The model may have been updated. Try refreshing the page.")
                elif "timeout" in error_msg.lower():
                    st.info("💡 **Timeout:** Try increasing the timeout in Research Configuration.")
                elif "rate limit" in error_msg.lower():
                    st.warning("💡 **Rate Limit:** You've hit the API rate limit. Please wait a moment and try again.")
                else:
                    st.info("💡 **General Error:** Check your query, API key, and network connection.")
            
            st.session_state.deep_research_session.status = "error"
    
    def _update_research_progress(self, event: StreamingEvent):
        """Update research progress based on event"""
        progress = st.session_state.deep_research_progress
        
        # Update current stage (handle optional stage)
        if event.stage:
            progress["current_stage"] = event.stage
            
            # Update progress percentage based on stage
            stage_progress = {
                ResearchStage.INITIALIZATION: 5,
                ResearchStage.CLARIFICATION: 10,
                ResearchStage.RESEARCH_BRIEF: 20,
                ResearchStage.RESEARCH_PLANNING: 30,
                ResearchStage.RESEARCH_EXECUTION: 60,
                ResearchStage.RESEARCH_ANALYSIS: 75,
                ResearchStage.RESEARCH_SYNTHESIS: 85,
                ResearchStage.FINAL_REPORT: 95,
                ResearchStage.COMPLETED: 100
            }
            
            progress["progress_percentage"] = stage_progress.get(event.stage, progress["progress_percentage"])
        
        progress["current_step"] = event.content
        
        # Add completed stages
        if event.type == "stage_complete" and event.stage and event.stage not in progress["stages_completed"]:
            progress["stages_completed"].append(event.stage)
        
        # Update sources count
        if event.type == "sources_found" and event.metadata and "sources" in event.metadata:
            progress["sources_found"] += len(event.metadata["sources"])
    
    def _display_events(self, placeholder):
        """Display research events in real-time"""
        events = st.session_state.get('deep_research_events', [])
        
        if events:
            with placeholder.container():
                st.markdown("### 🔄 Research Progress")
                
                # Show recent events
                recent_events = events[-10:]  # Show last 10 events
                
                for event in recent_events:
                    # Color code by event type
                    stage_name = event.stage.value.title() if event.stage else "Unknown"
                    
                    if event.type == "stage_start":
                        st.info(f"🚀 **{stage_name}**: {event.content}")
                    elif event.type == "stage_update":
                        st.write(f"📝 **{stage_name}**: {event.content}")
                    elif event.type == "stage_complete":
                        st.success(f"✅ **{stage_name}**: {event.content}")
                    elif event.type == "research_step":
                        st.write(f"🔍 {event.content}")
                    elif event.type == "sources_found":
                        st.write(f"📎 {event.content}")
                    elif event.type == "error":
                        st.error(f"❌ Error: {event.content}")
                    else:
                        st.write(f"ℹ️ {event.content}")
    
    def _display_sources(self, placeholder):
        """Display research sources"""
        sources = st.session_state.get('deep_research_sources', [])
        
        if sources:
            with placeholder.container():
                st.markdown("### 📎 Sources Found")
                
                # Remove duplicates and show unique sources
                unique_sources = list(set(sources))
                
                for i, source in enumerate(unique_sources[:10], 1):  # Show first 10 sources
                    if source.startswith('http'):
                        st.markdown(f"{i}. [{source}]({source})")
                    else:
                        st.markdown(f"{i}. {source}")
                
                if len(unique_sources) > 10:
                    st.write(f"... and {len(unique_sources) - 10} more sources")
    
    def _display_research_progress(self):
        """Display current research progress"""
        if st.session_state.get('deep_research_session'):
            session = st.session_state.deep_research_session
            
            if session.status == "running":
                progress = st.session_state.deep_research_progress
                
                st.markdown("### 📊 Research Progress")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    current_stage = progress["current_stage"]
                    stage_name = current_stage.value.title() if current_stage else "Unknown"
                    st.metric("Current Stage", stage_name)
                with col2:
                    st.metric("Progress", f"{progress['progress_percentage']:.0f}%")
                with col3:
                    st.metric("Sources Found", progress["sources_found"])
                
                # Progress bar
                st.progress(progress["progress_percentage"] / 100)
                st.write(f"**Current Step:** {progress['current_step']}")
                # Quick actions
                colA, colB = st.columns(2)
                with colA:
                    if st.button("💾 Save Stages & Result JSON", key="save_json_now"):
                        try:
                            paths = self._save_stages_and_result_json()
                            st.success(f"Saved: {paths['stages_path']} and {paths['result_path']}")
                        except Exception as e:
                            st.error(f"Failed to save JSON: {str(e)}")
                with colB:
                    st.caption("Exports to runs/ directory")
    
    def _display_research_results(self):
        """Display final research results"""
        if st.session_state.get('deep_research_result'):
            result = st.session_state.deep_research_result
            
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown("### 📊 Deep Research Results")
            
            # Research summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Research Time", f"{result.total_time_seconds:.0f}s")
            with col2:
                st.metric("Sources Used", len(result.sources))
            with col3:
                st.metric("Stages Completed", len(result.stages_completed))
            
            # Final report
            st.markdown("### 📄 Final Research Report")
            st.markdown(result.final_report)
            
            # Sources
            if result.sources:
                st.markdown("### 📎 Sources and References")
                for i, source in enumerate(result.sources, 1):
                    if source.startswith('http'):
                        st.markdown(f"{i}. [{source}]({source})")
                    else:
                        st.markdown(f"{i}. {source}")
            
            # Export options
            st.markdown("### 📤 Export Options")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Export as Markdown"):
                    self._export_as_markdown(result)
            
            with col2:
                if st.button("🌐 Export as HTML"):
                    self._export_as_html(result)
            
            st.markdown("</div>", unsafe_allow_html=True)

    def _display_crawl_log(self):
        """Display a consolidated crawl log if present (from first-party deep crawl or Claude web_fetch output)"""
        crawl_log = st.session_state.get('deep_research_crawl_log', [])
        if not crawl_log:
            return
        st.markdown("### 🌐 Crawl Log (First-Party & Validations)")
        # Show a compact table-like list with expanders for details
        max_show = 50
        for idx, entry in enumerate(crawl_log[:max_show], start=1):
            header = f"{idx}. {entry.get('link_text','').strip() or '(no anchor)'} → {entry.get('to_url','')}"
            with st.expander(header, expanded=False):
                cols = st.columns(2)
                with cols[0]:
                    st.write(f"From: {entry.get('from_page','')}")
                    st.write(f"Section: {entry.get('section','')}")
                    st.write(f"Status: {entry.get('status','')}")
                with cols[1]:
                    st.write(f"Title: {entry.get('title','')}")
                    st.write(f"Validated: {entry.get('validated')}")
                    if entry.get('evidence'):
                        st.write(f"Evidence: {entry.get('evidence')}")
        if len(crawl_log) > max_show:
            st.caption(f"Showing first {max_show} of {len(crawl_log)} entries")
        # Download button
        try:
            if st.button("⬇️ Download Crawl Log JSON"):
                import json
                st.download_button(
                    label="Download crawl_log.json",
                    data=json.dumps(crawl_log, indent=2),
                    file_name="crawl_log.json",
                    mime="application/json"
                )
        except Exception:
            pass

    def _display_tool_calls(self):
        """Show a live log of tool invocations and their results"""
        tool_calls = st.session_state.get('deep_research_tool_calls', [])
        if not tool_calls:
            return
        st.markdown("### 🧰 Tool Calls & Results")
        # Compact summary
        st.write(f"Total tool events: {len(tool_calls)}")
        # Show latest N calls
        latest = tool_calls[-12:]
        for i, call in enumerate(latest, 1):
            with st.expander(f"{i}. [{call.get('stage','')}] {call.get('tool','unknown')} — {call.get('timestamp','')}", expanded=False):
                st.write(call.get("message", ""))
                args = call.get("args")
                if args:
                    with st.expander("Args", expanded=False):
                        st.json(args)
                urls = call.get("urls")
                if urls:
                    st.markdown("**URLs**")
                    for u in urls[:20]:
                        if isinstance(u, str) and u.startswith("http"):
                            st.markdown(f"- [{u}]({u})")
                        else:
                            st.markdown(f"- {u}")

    def _display_stage_logs(self):
        """Display full per-stage logs with toggle to expand outputs"""
        logs = st.session_state.get('deep_research_stage_logs', {})
        if not logs:
            return
        st.markdown("### 🧭 Stage Logs")
        show_full = st.checkbox("Show full outputs", value=False, help="Toggle between compact and full stage outputs")
        # Order stages by a reasonable sequence using ResearchStage enum
        stage_order = [
            ResearchStage.INITIALIZATION.value,
            ResearchStage.CLARIFICATION.value,
            ResearchStage.RESEARCH_BRIEF.value,
            ResearchStage.RESEARCH_PLANNING.value,
            ResearchStage.RESEARCH_EXECUTION.value,
            ResearchStage.RESEARCH_ANALYSIS.value,
            ResearchStage.RESEARCH_SYNTHESIS.value,
            ResearchStage.FINAL_REPORT.value,
            ResearchStage.COMPLETED.value,
            ResearchStage.ERROR.value,
        ]
        # Include any unknown keys as well
        ordered_keys = [k for k in stage_order if k in logs] + [k for k in logs.keys() if k not in stage_order]
        for stage_key in ordered_keys:
            with st.expander(f"{stage_key.title()} ({len(logs.get(stage_key, []))} events)", expanded=False):
                for entry in logs.get(stage_key, []):
                    content = entry.get("content", "") or ""
                    preview = content if show_full else (content[:300] + ("..." if len(content) > 300 else ""))
                    st.write(f"- [{entry.get('timestamp','')}] {entry.get('type','')}")
                    if preview:
                        st.code(preview)
                    if entry.get("metadata"):
                        with st.expander("Metadata", expanded=False):
                            st.json(entry["metadata"])

        # Download helpers
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬇️ Download Stage Logs JSON"):
                try:
                    paths = self._save_stages_and_result_json()
                    with open(paths["stages_path"], "r") as f:
                        st.download_button(
                            label="Download Stages JSON",
                            data=f.read(),
                            file_name=paths["stages_path"].split("/")[-1],
                            mime="application/json"
                        )
                except Exception as e:
                    st.error(f"Failed to prepare download: {str(e)}")
        with col2:
            if st.button("⬇️ Download Result JSON"):
                try:
                    paths = self._save_stages_and_result_json()
                    with open(paths["result_path"], "r") as f:
                        st.download_button(
                            label="Download Result JSON",
                            data=f.read(),
                            file_name=paths["result_path"].split("/")[-1],
                            mime="application/json"
                        )
                except Exception as e:
                    st.error(f"Failed to prepare download: {str(e)}")

    def _save_stages_and_result_json(self) -> Dict[str, str]:
        """Persist stages log and final result to separate JSON files under runs/"""
        runs_dir = os.path.join(os.getcwd(), "runs")
        os.makedirs(runs_dir, exist_ok=True)
        session = st.session_state.get('deep_research_session')
        result = st.session_state.get('deep_research_result')
        logs = st.session_state.get('deep_research_stage_logs', {})
        events = st.session_state.get('deep_research_events', [])
        research_id = session.research_id if session else f"research_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        stages_path = os.path.join(runs_dir, f"stages_{research_id}_{timestamp}.json")
        result_path = os.path.join(runs_dir, f"result_{research_id}_{timestamp}.json")

        # Build serializable structures
        stages_payload = {
            "research_id": research_id,
            "created_at": datetime.now().isoformat(),
            "stages": logs,
            "events": [
                {
                    "timestamp": e.timestamp,
                    "type": e.type,
                    "stage": e.stage.value if e.stage else None,
                    "content": e.content,
                    "metadata": e.metadata
                } for e in events
            ]
        }

        result_payload: Dict[str, Any] = {
            "research_id": research_id,
            "query": result.query if result else session.query if session else None,
            "final_report": result.final_report if result else None,
            "sources": result.sources if result else st.session_state.get('deep_research_sources', []),
            "model_used": result.model_used if result else session.model if session else None,
            "created_at": datetime.now().isoformat(),
            "stages_completed": result.stages_completed if result else st.session_state.get('deep_research_progress', {}).get('stages_completed', [])
        }

        with open(stages_path, "w") as f:
            json.dump(stages_payload, f, indent=2)
        with open(result_path, "w") as f:
            json.dump(result_payload, f, indent=2)

        return {"stages_path": stages_path, "result_path": result_path}
    
    def _extract_final_report(self) -> Optional[str]:
        """Extract final report from events"""
        events = st.session_state.get('deep_research_events', [])
        
        # Look for final report in events
        for event in reversed(events):
            if event.type == "stage_update" and event.stage == ResearchStage.FINAL_REPORT:
                if "Final Report:" in event.content:
                    # Extract report content after "Final Report:"
                    report_start = event.content.find("Final Report:") + len("Final Report:")
                    return event.content[report_start:].strip()
            elif event.type == "stage_update" and "Final Report:" in event.content:
                # Also check for final report in any stage update
                report_start = event.content.find("Final Report:") + len("Final Report:")
                return event.content[report_start:].strip()
        
        return None
    
    def _save_research_document(self):
        """Save research as a document"""
        if st.session_state.get('deep_research_result'):
            result = st.session_state.deep_research_result
            
            try:
                # Save using document storage service
                document = self.document_storage.save_research_document(
                    result,
                    title=f"Research Report: {result.query[:50]}...",
                    format="markdown"
                )
                
                # Also save to project for integration with existing pipeline
                if st.session_state.current_project:
                    self.project_manager.save_project_stage_data(
                        'deep_research',
                        document.model_dump(),
                        f'research_document_{document.document_id}.json'
                    )
                
                st.success(f"Research document saved: {document.title}")
                st.info(f"Document ID: {document.document_id}")
                
            except Exception as e:
                st.error(f"Failed to save document: {str(e)}")
        else:
            st.warning("No research results to save")
    
    def _export_as_markdown(self, result: ResearchResult):
        """Export research result as markdown"""
        markdown_content = f"""# Research Report: {result.query}

**Generated on:** {result.created_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Model Used:** {result.model_used}  
**Research Time:** {result.total_time_seconds:.0f} seconds  
**Sources:** {len(result.sources)}

## Research Report

{result.final_report}

## Sources and References

"""
        
        for i, source in enumerate(result.sources, 1):
            markdown_content += f"{i}. {source}\n"
        
        # Create download button
        st.download_button(
            label="📥 Download Markdown",
            data=markdown_content,
            file_name=f"research_report_{result.research_id}.md",
            mime="text/markdown"
        )
    
    def _export_as_html(self, result: ResearchResult):
        """Export research result as HTML"""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Research Report: {result.query}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        .metadata {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .content {{ line-height: 1.6; }}
        .sources {{ background: #f9f9f9; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Research Report: {result.query}</h1>
    
    <div class="metadata">
        <p><strong>Generated on:</strong> {result.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Model Used:</strong> {result.model_used}</p>
        <p><strong>Research Time:</strong> {result.total_time_seconds:.0f} seconds</p>
        <p><strong>Sources:</strong> {len(result.sources)}</p>
    </div>
    
    <div class="content">
        {result.final_report.replace(chr(10), '<br>')}
    </div>
    
    <div class="sources">
        <h2>Sources and References</h2>
        <ol>
"""
        
        for source in result.sources:
            if source.startswith('http'):
                html_content += f'            <li><a href="{source}">{source}</a></li>\n'
            else:
                html_content += f'            <li>{source}</li>\n'
        
        html_content += """        </ol>
    </div>
</body>
</html>"""
        
        # Create download button
        st.download_button(
            label="📥 Download HTML",
            data=html_content,
            file_name=f"research_report_{result.research_id}.html",
            mime="text/html"
        )
    
    def _reset_research_session(self):
        """Reset research session"""
        keys_to_remove = [
            'deep_research_session', 'deep_research_events', 'deep_research_sources',
            'deep_research_progress', 'deep_research_result'
        ]
        
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    def _render_research_history(self):
        """Render research history interface"""
        st.markdown("### 📚 Research History")
        
        # Get saved research sessions from runs directory
        runs_dir = os.path.join(os.getcwd(), "runs")
        saved_sessions = []
        
        if os.path.exists(runs_dir):
            import glob
            result_files = glob.glob(os.path.join(runs_dir, "result_*.json"))
            result_files.sort(key=os.path.getmtime, reverse=True)  # Most recent first
            
            for file_path in result_files[:10]:  # Show last 10
                try:
                    with open(file_path, 'r') as f:
                        session_data = json.load(f)
                        saved_sessions.append({
                            'file': file_path,
                            'research_id': session_data.get('research_id', 'Unknown'),
                            'query': session_data.get('query', 'Unknown query'),
                            'created_at': session_data.get('created_at', ''),
                            'model': session_data.get('model_used', 'Unknown'),
                            'sources_count': len(session_data.get('sources', []))
                        })
                except Exception:
                    continue
        
        if saved_sessions:
            st.markdown(f"**Found {len(saved_sessions)} recent research sessions:**")
            
            for i, session in enumerate(saved_sessions):
                if i > 0:
                    st.divider()
                st.markdown(f"**🔍 {session['query'][:60]}... - {session['created_at'][:10] if session['created_at'] else 'Unknown date'}**")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Research ID:** `{session['research_id']}`")
                    st.markdown(f"**Model:** {session['model']}")
                    st.markdown(f"**Sources:** {session['sources_count']}")
                    st.markdown(f"**Date:** {session['created_at']}")
                    
                    with col2:
                        if st.button("📖 Load", key=f"load_{session['research_id']}"):
                            try:
                                with open(session['file'], 'r') as f:
                                    session_data = json.load(f)
                                    # Create ResearchResult from saved data
                                    from datetime import datetime
                                    result = ResearchResult(
                                        research_id=session_data.get('research_id'),
                                        query=session_data.get('query'),
                                        final_report=session_data.get('final_report', ''),
                                        sources=session_data.get('sources', []),
                                        stages_completed=session_data.get('stages_completed', []),
                                        total_time_seconds=0,
                                        model_used=session_data.get('model_used'),
                                        created_at=datetime.fromisoformat(session_data.get('created_at', datetime.now().isoformat()))
                                    )
                                    st.session_state.deep_research_result = result
                                    st.success("Research session loaded!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Failed to load: {str(e)}")
                        
                        if st.button("🗑️ Delete", key=f"delete_{session['research_id']}"):
                            try:
                                os.remove(session['file'])
                                st.success("Session deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete: {str(e)}")
        else:
            st.info("No saved research sessions found. Complete a research to see history here.")
    
    def _render_document_management(self):
        """Render document management interface"""
        st.markdown("### 📁 Stored Research Documents")
        
        # Get storage stats
        stats = self.document_storage.get_storage_stats()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", stats["total_documents"])
        with col2:
            st.metric("Storage Size", f"{stats['total_size_mb']} MB")
        with col3:
            st.metric("Formats", len(stats["format_distribution"]))
        
        # Search documents
        search_query = st.text_input("Search documents:", placeholder="Enter search query...")
        
        if search_query:
            documents = self.document_storage.search_documents(search_query, limit=10)
        else:
            documents = self.document_storage.list_documents(limit=10)
        
        if documents:
            st.markdown(f"**Found {len(documents)} documents:**")
            
            for i, doc in enumerate(documents):
                if i > 0:
                    st.divider()
                st.markdown(f"**📄 {doc.get('title', 'Untitled')} - {doc.get('created_at', '')[:10]}**")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Research ID:** {doc.get('research_id', 'Unknown')}")
                    st.markdown(f"**Model:** {doc.get('metadata', {}).get('model_used', 'Unknown')}")
                    st.markdown(f"**Sources:** {len(doc.get('sources', []))}")
                    st.markdown(f"**Format:** {doc.get('format', 'markdown')}")
                    
                    # Show preview
                    content_preview = doc.get('content', '')[:200] + "..." if len(doc.get('content', '')) > 200 else doc.get('content', '')
                    st.markdown(f"**Preview:** {content_preview}")
                
                with col2:
                        if st.button("📥 Download", key=f"download_{doc.get('document_id')}"):
                            self._download_document(doc.get('document_id'))
                        
                        if st.button("🗑️ Delete", key=f"delete_{doc.get('document_id')}"):
                            if self.document_storage.delete_document(doc.get('document_id')):
                                st.success("Document deleted successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to delete document")
        else:
            st.info("No documents found. Complete a research session to create documents.")
    
    def _detect_conflicts(self, event: StreamingEvent) -> Optional[Dict[str, Any]]:
        """Detect conflicting information in research events"""
        if not event.metadata or not isinstance(event.metadata, dict):
            return None
        
        content = event.content.lower()
        metadata = event.metadata
        
        # Check for conflict indicators in content
        conflict_keywords = [
            "conflicting", "contradict", "discrepancy", "inconsistent",
            "different sources", "unclear", "uncertain", "conflicting information"
        ]
        
        has_conflict_keyword = any(keyword in content for keyword in conflict_keywords)
        
        # Check for multiple sources with different information
        sources = metadata.get("sources", [])
        if len(sources) > 1 and has_conflict_keyword:
            return {
                "type": "conflicting_sources",
                "message": event.content,
                "sources": sources,
                "stage": event.stage.value if event.stage else "unknown",
                "timestamp": event.timestamp
            }
        
        # Check for financial data conflicts
        if "financial" in content or "revenue" in content or "profit" in content:
            if "not disclosed" in content or "unclear" in content or "varies" in content:
                return {
                    "type": "financial_uncertainty",
                    "message": event.content,
                    "stage": event.stage.value if event.stage else "unknown",
                    "timestamp": event.timestamp
                }
        
        return None
    
    def _display_conflict_resolution(self):
        """Display UI for resolving research conflicts"""
        if not st.session_state.get('research_paused') or not st.session_state.get('conflict_detected'):
            return
        
        conflict = st.session_state.conflict_detected
        
        st.markdown("---")
        st.warning("⚠️ **Conflicting Information Detected**")
        
        with st.expander("🔍 Conflict Details", expanded=True):
            st.write(f"**Type:** {conflict.get('type', 'Unknown')}")
            st.write(f"**Message:** {conflict.get('message', 'No details')}")
            st.write(f"**Stage:** {conflict.get('stage', 'Unknown')}")
            
            if conflict.get('sources'):
                st.write("**Conflicting Sources:**")
                for source in conflict.get('sources', [])[:5]:
                    if source.startswith('http'):
                        st.markdown(f"- [{source}]({source})")
                    else:
                        st.markdown(f"- {source}")
        
        st.markdown("**What would you like me to do?**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Dig Deeper", type="primary", use_container_width=True):
                st.session_state.user_research_decision = "dig_deeper"
                st.session_state.research_paused = False
                st.session_state.conflict_detected = None
                st.info("Continuing research with deeper investigation...")
                st.rerun()
        
        with col2:
            if st.button("➡️ Proceed with Current Info", use_container_width=True):
                st.session_state.user_research_decision = "proceed"
                st.session_state.research_paused = False
                st.session_state.conflict_detected = None
                st.info("Proceeding with current findings...")
                st.rerun()
    
    def _download_document(self, document_id: str):
        """Download a document in various formats"""
        document = self.document_storage.get_document(document_id)
        if not document:
            st.error("Document not found")
            return
        
        # Export options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Markdown", key=f"md_{document_id}"):
                content = self.document_storage.export_document(document_id, "markdown")
                if content:
                    st.download_button(
                        label="Download Markdown",
                        data=content,
                        file_name=f"{document.title}.md",
                        mime="text/markdown"
                    )
        
        with col2:
            if st.button("🌐 HTML", key=f"html_{document_id}"):
                content = self.document_storage.export_document(document_id, "html")
                if content:
                    st.download_button(
                        label="Download HTML",
                        data=content,
                        file_name=f"{document.title}.html",
                        mime="text/html"
                    )
        
        with col3:
            if st.button("📝 Text", key=f"txt_{document_id}"):
                content = self.document_storage.export_document(document_id, "txt")
                if content:
                    st.download_button(
                        label="Download Text",
                        data=content,
                        file_name=f"{document.title}.txt",
                        mime="text/plain"
                    )
