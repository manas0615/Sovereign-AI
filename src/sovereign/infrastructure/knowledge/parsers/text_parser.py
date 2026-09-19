"""Basic text and markdown parser."""

from typing import List, BinaryIO
import re

from sovereign.core.knowledge.parser import DocumentParser
from sovereign.core.knowledge.models import Document, DocumentBlock

class TextParser(DocumentParser):
    def parse(self, document: Document, file_stream: BinaryIO) -> List[DocumentBlock]:
        text = file_stream.read().decode('utf-8', errors='replace')
        blocks = []
        
        # Split by empty lines to get paragraphs
        raw_paragraphs = re.split(r'\n\s*\n', text)
        
        sequence = 0
        current_section = None
        
        for raw in raw_paragraphs:
            clean_text = raw.strip()
            if not clean_text:
                continue
                
            block_type = "paragraph"
            
            # Simple markdown heading detection
            if document.document_type.lower() in ['md', 'markdown', 'txt']:
                heading_match = re.match(r'^(#{1,6})\s+(.+)$', clean_text)
                if heading_match:
                    current_section = heading_match.group(2).strip()
                    block_type = "heading"
                    
            block = DocumentBlock(
                document_id=document.document_id,
                page_number=None,
                section=current_section,
                block_type=block_type,
                sequence=sequence,
                text=clean_text
            )
            blocks.append(block)
            sequence += 1
            
        return blocks
