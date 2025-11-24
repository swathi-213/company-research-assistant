"""
Document Storage Service for Deep Research 2.0
Handles storage and retrieval of research documents
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from .models.research_models import ResearchDocument, ResearchResult


class DocumentStorageService:
    """Service for managing research document storage and retrieval"""
    
    def __init__(self, base_storage_path: str = "research_documents"):
        """
        Initialize document storage service
        
        Args:
            base_storage_path: Base directory for storing documents
        """
        self.base_storage_path = Path(base_storage_path)
        self.base_storage_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.documents_dir = self.base_storage_path / "documents"
        self.metadata_dir = self.base_storage_path / "metadata"
        self.exports_dir = self.base_storage_path / "exports"
        
        for directory in [self.documents_dir, self.metadata_dir, self.exports_dir]:
            directory.mkdir(exist_ok=True)
    
    def save_research_document(self, research_result: ResearchResult, 
                             title: Optional[str] = None,
                             format: str = "markdown") -> ResearchDocument:
        """
        Save a research result as a document
        
        Args:
            research_result: Research result to save
            title: Optional custom title for the document
            format: Document format (markdown, html, etc.)
            
        Returns:
            ResearchDocument object
        """
        # Generate document ID
        document_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        # Create title if not provided
        if not title:
            title = f"Research Report: {research_result.query[:50]}..."
        
        # Create document
        document = ResearchDocument(
            document_id=document_id,
            research_id=research_result.research_id,
            title=title,
            content=research_result.final_report,
            format=format,
            created_at=datetime.now(),
            sources=research_result.sources,
            metadata={
                "model_used": research_result.model_used,
                "total_time": research_result.total_time_seconds,
                "stages_completed": [stage.value for stage in research_result.stages_completed],
                "query": research_result.query
            }
        )
        
        # Save document content
        self._save_document_content(document)
        
        # Save metadata
        self._save_document_metadata(document)
        
        return document
    
    def _save_document_content(self, document: ResearchDocument):
        """Save document content to file"""
        filename = f"{document.document_id}.{document.format}"
        filepath = self.documents_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            if document.format == "markdown":
                f.write(self._format_as_markdown(document))
            elif document.format == "html":
                f.write(self._format_as_html(document))
            else:
                f.write(document.content)
    
    def _save_document_metadata(self, document: ResearchDocument):
        """Save document metadata to file"""
        filename = f"{document.document_id}_metadata.json"
        filepath = self.metadata_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(document.model_dump(), f, indent=2, default=str)
    
    def _format_as_markdown(self, document: ResearchDocument) -> str:
        """Format document as markdown"""
        markdown_content = f"""# {document.title}

**Generated on:** {document.created_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Research ID:** {document.research_id}  
**Model Used:** {document.metadata.get('model_used', 'Unknown')}  
**Research Time:** {document.metadata.get('total_time', 0):.0f} seconds  
**Sources:** {len(document.sources)}

## Research Report

{document.content}

## Sources and References

"""
        
        for i, source in enumerate(document.sources, 1):
            markdown_content += f"{i}. {source}\n"
        
        return markdown_content
    
    def _format_as_html(self, document: ResearchDocument) -> str:
        """Format document as HTML"""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{document.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        .metadata {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .content {{ line-height: 1.6; }}
        .sources {{ background: #f9f9f9; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{document.title}</h1>
    
    <div class="metadata">
        <p><strong>Generated on:</strong> {document.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Research ID:</strong> {document.research_id}</p>
        <p><strong>Model Used:</strong> {document.metadata.get('model_used', 'Unknown')}</p>
        <p><strong>Research Time:</strong> {document.metadata.get('total_time', 0):.0f} seconds</p>
        <p><strong>Sources:</strong> {len(document.sources)}</p>
    </div>
    
    <div class="content">
        {document.content.replace(chr(10), '<br>')}
    </div>
    
    <div class="sources">
        <h2>Sources and References</h2>
        <ol>
"""
        
        for source in document.sources:
            if source.startswith('http'):
                html_content += f'            <li><a href="{source}">{source}</a></li>\n'
            else:
                html_content += f'            <li>{source}</li>\n'
        
        html_content += """        </ol>
    </div>
</body>
</html>"""
        
        return html_content
    
    def get_document(self, document_id: str) -> Optional[ResearchDocument]:
        """
        Retrieve a document by ID
        
        Args:
            document_id: Document ID to retrieve
            
        Returns:
            ResearchDocument or None if not found
        """
        metadata_file = self.metadata_dir / f"{document_id}_metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Load document content
            content_file = self.documents_dir / f"{document_id}.{metadata.get('format', 'markdown')}"
            if content_file.exists():
                with open(content_file, 'r', encoding='utf-8') as f:
                    metadata['content'] = f.read()
            
            return ResearchDocument.model_validate(metadata)
            
        except Exception as e:
            print(f"Error loading document {document_id}: {e}")
            return None
    
    def list_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all stored documents
        
        Args:
            limit: Optional limit on number of documents to return
            
        Returns:
            List of document metadata
        """
        documents = []
        
        for metadata_file in self.metadata_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Add file info
                metadata['file_size'] = metadata_file.stat().st_size
                metadata['last_modified'] = datetime.fromtimestamp(metadata_file.stat().st_mtime).isoformat()
                
                documents.append(metadata)
                
            except Exception as e:
                print(f"Error loading metadata from {metadata_file}: {e}")
        
        # Sort by creation date (newest first)
        documents.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        if limit:
            documents = documents[:limit]
        
        return documents
    
    def search_documents(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search documents by content or metadata
        
        Args:
            query: Search query
            limit: Optional limit on number of results
            
        Returns:
            List of matching documents
        """
        all_documents = self.list_documents()
        matching_documents = []
        
        query_lower = query.lower()
        
        for doc in all_documents:
            # Search in title, content, and metadata
            searchable_text = f"{doc.get('title', '')} {doc.get('content', '')} {doc.get('query', '')}"
            
            if query_lower in searchable_text.lower():
                matching_documents.append(doc)
        
        if limit:
            matching_documents = matching_documents[:limit]
        
        return matching_documents
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its metadata
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Get document to find format
            document = self.get_document(document_id)
            if not document:
                return False
            
            # Delete content file
            content_file = self.documents_dir / f"{document_id}.{document.format}"
            if content_file.exists():
                content_file.unlink()
            
            # Delete metadata file
            metadata_file = self.metadata_dir / f"{document_id}_metadata.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error deleting document {document_id}: {e}")
            return False
    
    def export_document(self, document_id: str, export_format: str = "markdown") -> Optional[str]:
        """
        Export a document in a specific format
        
        Args:
            document_id: Document ID to export
            export_format: Export format (markdown, html, txt)
            
        Returns:
            Exported content or None if document not found
        """
        document = self.get_document(document_id)
        if not document:
            return None
        
        if export_format == "markdown":
            return self._format_as_markdown(document)
        elif export_format == "html":
            return self._format_as_html(document)
        elif export_format == "txt":
            return document.content
        else:
            return None
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        total_documents = len(list(self.metadata_dir.glob("*_metadata.json")))
        total_size = sum(f.stat().st_size for f in self.documents_dir.glob("*"))
        
        # Get format distribution
        format_counts = {}
        for content_file in self.documents_dir.glob("*"):
            if content_file.suffix:
                format_type = content_file.suffix[1:]  # Remove the dot
                format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        return {
            "total_documents": total_documents,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "format_distribution": format_counts,
            "storage_path": str(self.base_storage_path)
        }
