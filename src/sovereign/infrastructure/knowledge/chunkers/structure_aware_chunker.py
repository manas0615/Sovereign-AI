"""Structure aware chunker."""

from typing import List, Optional
from sovereign.core.knowledge.chunker import Chunker
from sovereign.core.knowledge.models import DocumentBlock, DocumentChunk, Document
from sovereign.infrastructure.state.tokenizer import TokenCounter

class StructureAwareChunker(Chunker):
    def __init__(self, tokenizer: TokenCounter, max_chunk_tokens: int = 500):
        # We default to 500 tokens. This is significantly smaller than the 8192 token model context.
        # This allows the Context Manager to fit multiple chunks from different documents or pages
        # alongside task state, system instructions, and output budgets.
        self.tokenizer = tokenizer
        self.max_chunk_tokens = max_chunk_tokens
        
    def chunk(self, document: Document, blocks: List[DocumentBlock]) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        
        current_chunk_blocks: List[DocumentBlock] = []
        current_tokens = 0
        sequence = 0
        
        def _emit_chunk(blocks_to_emit: List[DocumentBlock]) -> None:
            nonlocal sequence
            if not blocks_to_emit:
                return
                
            text = "\n\n".join(b.text for b in blocks_to_emit)
            pages = [b.page_number for b in blocks_to_emit if b.page_number is not None]
            
            page_range = None
            if pages:
                min_page = min(pages)
                max_page = max(pages)
                page_range = str(min_page) if min_page == max_page else f"{min_page}-{max_page}"
                
            sections = [b.section for b in blocks_to_emit if b.section]
            section = sections[0] if sections else None
            
            chunk = DocumentChunk(
                document_id=document.document_id,
                text=text,
                sequence=sequence,
                page_range=page_range,
                section=section,
                token_estimate=self.tokenizer.count_tokens(text)
            )
            chunks.append(chunk)
            sequence += 1
            
        for block in blocks:
            block_tokens = self.tokenizer.count_tokens(block.text)
            
            # If a single block exceeds the max size, we should ideally split it,
            # but for this MVP structure-aware chunker, we'll just emit it as one slightly oversized chunk
            # to preserve the structural boundary (e.g., a massive paragraph).
            
            if current_tokens + block_tokens > self.max_chunk_tokens and current_chunk_blocks:
                _emit_chunk(current_chunk_blocks)
                current_chunk_blocks = [block]
                current_tokens = block_tokens
            else:
                current_chunk_blocks.append(block)
                current_tokens += block_tokens
                
        if current_chunk_blocks:
            _emit_chunk(current_chunk_blocks)
            
        return chunks
