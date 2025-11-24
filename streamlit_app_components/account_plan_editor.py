"""
Account Plan Editor Component
Allows users to edit specific sections of generated account plans
"""

import streamlit as st
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import uuid


class AccountPlanEditor:
    """Manages account plan editing functionality"""
    
    # Standard account plan sections
    STANDARD_SECTIONS = [
        "Executive Summary",
        "Company Overview",
        "Financial Analysis",
        "Strategic Priorities & Goals",
        "Key Decision Makers",
        "Competitor Landscape",
        "Recent News & Signals",
        "Opportunities & Proposed Strategy",
        "Sources"
    ]
    
    def __init__(self):
        self.initialize_editor_state()
    
    def initialize_editor_state(self):
        """Initialize editor-related session state"""
        if 'account_plan_sections' not in st.session_state:
            st.session_state.account_plan_sections = {}
        
        if 'account_plan_original' not in st.session_state:
            st.session_state.account_plan_original = None
        
        if 'account_plan_edited' not in st.session_state:
            st.session_state.account_plan_edited = False
    
    def parse_account_plan(self, markdown_content: str) -> Dict[str, str]:
        """
        Parse account plan markdown into editable sections
        
        Args:
            markdown_content: Full markdown content of account plan
            
        Returns:
            Dictionary mapping section names to their content
        """
        sections = {}
        
        # Split by ## headers (main sections)
        # Pattern: ## Section Name followed by content until next ##
        pattern = r'^##\s+(.+?)$'
        matches = list(re.finditer(pattern, markdown_content, re.MULTILINE))
        
        if not matches:
            # If no sections found, treat entire content as one section
            sections["Full Report"] = markdown_content
            return sections
        
        # Extract content between sections
        for i, match in enumerate(matches):
            section_name = match.group(1).strip()
            start_pos = match.end()
            
            # Find end position (start of next section or end of document)
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(markdown_content)
            
            # Extract section content
            section_content = markdown_content[start_pos:end_pos].strip()
            sections[section_name] = section_content
        
        # Also capture title if present
        title_match = re.search(r'^#\s+(.+?)$', markdown_content, re.MULTILINE)
        if title_match:
            sections["_title"] = title_match.group(1).strip()
        
        return sections
    
    def reconstruct_account_plan(self, sections: Dict[str, str]) -> str:
        """
        Reconstruct account plan markdown from edited sections
        
        Args:
            sections: Dictionary of section names to content
            
        Returns:
            Complete markdown content
        """
        markdown_parts = []
        
        # Add title if present
        if "_title" in sections:
            markdown_parts.append(f"# {sections['_title']}\n")
            markdown_parts.append("\n")
        
        # Add each section
        for section_name, section_content in sections.items():
            if section_name == "_title":
                continue
            
            markdown_parts.append(f"## {section_name}\n")
            markdown_parts.append(section_content)
            markdown_parts.append("\n\n")
        
        return "".join(markdown_parts)
    
    def render_editor(self, account_plan_content: str, research_id: Optional[str] = None):
        """
        Render the account plan editor interface
        
        Args:
            account_plan_content: Original account plan markdown
            research_id: Optional research ID for tracking
        """
        st.markdown("### 📝 Account Plan Editor")
        st.markdown("Edit specific sections of the account plan below. Changes are saved automatically.")
        
        # Parse sections if not already parsed
        if not st.session_state.account_plan_sections or st.session_state.account_plan_original != account_plan_content:
            st.session_state.account_plan_sections = self.parse_account_plan(account_plan_content)
            st.session_state.account_plan_original = account_plan_content
        
        sections = st.session_state.account_plan_sections
        
        # Editor tabs for better organization
        if len(sections) > 3:
            # Use tabs for many sections
            tab_names = [name for name in sections.keys() if name != "_title"]
            tabs = st.tabs(tab_names)
            
            for i, (section_name, section_content) in enumerate(sections.items()):
                if section_name == "_title":
                    continue
                
                with tabs[tab_names.index(section_name)]:
                    self._render_section_editor(section_name, section_content, i, research_id)
        else:
            # Use expanders for few sections
            for i, (section_name, section_content) in enumerate(sections.items()):
                if section_name == "_title":
                    continue
                
                with st.expander(f"✏️ {section_name}", expanded=(i == 0)):
                    self._render_section_editor(section_name, section_content, i, research_id)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save All Changes", type="primary", use_container_width=True):
                self._save_edited_plan(research_id)
        
        with col2:
            if st.button("🔄 Reset to Original", use_container_width=True):
                self._reset_to_original(account_plan_content)
        
        with col3:
            if st.button("📥 Download Edited Plan", use_container_width=True):
                self._download_edited_plan()
    
    def _render_section_editor(self, section_name: str, current_content: str, index: int, research_id: Optional[str]):
        """Render editor for a single section"""
        # Get current edited content or use original
        unique_id = research_id if research_id is not None else "default"
        key = f"edit_{section_name}_{index}_{unique_id}"
        if key not in st.session_state:
            st.session_state[key] = current_content
        # Generate a truly unique key for the text area
        textarea_key = f"textarea_{section_name}_{index}_{unique_id}_{uuid.uuid4()}"
        # Text area for editing
        edited_content = st.text_area(
            f"Edit {section_name}",
            value=st.session_state[key],
            height=300,
            key=textarea_key,
            help=f"Edit the content of the {section_name} section"
        )
        
        # Update session state
        st.session_state[key] = edited_content
        st.session_state.account_plan_sections[section_name] = edited_content
        st.session_state.account_plan_edited = True
        
        # Character count
        char_count = len(edited_content)
        word_count = len(edited_content.split())
        st.caption(f"Characters: {char_count} | Words: {word_count}")
        
        # Quick actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"💾 Save {section_name}", key=f"save_{section_name}_{index}"):
                st.success(f"Saved {section_name}!")
                self._save_section(section_name, edited_content, research_id)
        
        with col2:
            if st.button(f"🔄 Reset {section_name}", key=f"reset_{section_name}_{index}"):
                st.session_state[key] = current_content
                st.session_state.account_plan_sections[section_name] = current_content
                st.rerun()
    
    def _save_section(self, section_name: str, content: str, research_id: Optional[str]):
        """Save a single section"""
        # Update sections
        st.session_state.account_plan_sections[section_name] = content
        
        # Save to file if research_id provided
        if research_id:
            import os
            edits_dir = os.path.join(os.getcwd(), "account_plan_edits")
            os.makedirs(edits_dir, exist_ok=True)
            
            edit_file = os.path.join(edits_dir, f"{research_id}_edits.json")
            edits_data = {
                'research_id': research_id,
                'section': section_name,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
            
            # Load existing edits
            if os.path.exists(edit_file):
                with open(edit_file, 'r') as f:
                    all_edits = json.load(f)
            else:
                all_edits = {'sections': {}}
            
            all_edits['sections'][section_name] = edits_data
            
            with open(edit_file, 'w') as f:
                json.dump(all_edits, f, indent=2)
    
    def _save_edited_plan(self, research_id: Optional[str]):
        """Save the complete edited account plan"""
        sections = st.session_state.account_plan_sections
        edited_content = self.reconstruct_account_plan(sections)
        
        # Update the research result if available
        if st.session_state.get('deep_research_result'):
            result = st.session_state.deep_research_result
            result.final_report = edited_content
            st.session_state.deep_research_result = result
        
        # Save to file
        if research_id:
            import os
            edits_dir = os.path.join(os.getcwd(), "account_plan_edits")
            os.makedirs(edits_dir, exist_ok=True)
            
            edit_file = os.path.join(edits_dir, f"{research_id}_complete.md")
            with open(edit_file, 'w', encoding='utf-8') as f:
                f.write(edited_content)
        
        st.success("✅ Account plan saved successfully!")
    
    def _reset_to_original(self, original_content: str):
        """Reset all sections to original content"""
        st.session_state.account_plan_sections = self.parse_account_plan(original_content)
        st.session_state.account_plan_edited = False
        
        # Clear all edit keys
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith("edit_")]
        for key in keys_to_remove:
            del st.session_state[key]
        
        st.success("🔄 Reset to original account plan")
        st.rerun()
    
    def _download_edited_plan(self):
        """Download the edited account plan"""
        sections = st.session_state.account_plan_sections
        edited_content = self.reconstruct_account_plan(sections)
        
        research_id = st.session_state.get('deep_research_result', {}).research_id if hasattr(st.session_state.get('deep_research_result', None), 'research_id') else "edited"
        
        st.download_button(
            label="📥 Download Edited Account Plan",
            data=edited_content,
            file_name=f"account_plan_{research_id}_edited.md",
            mime="text/markdown"
        )
    
    def get_edited_plan(self) -> Optional[str]:
        """Get the current edited account plan content"""
        if st.session_state.account_plan_sections:
            return self.reconstruct_account_plan(st.session_state.account_plan_sections)
        return None
    
    def has_edits(self) -> bool:
        """Check if there are any unsaved edits"""
        return st.session_state.get('account_plan_edited', False)

