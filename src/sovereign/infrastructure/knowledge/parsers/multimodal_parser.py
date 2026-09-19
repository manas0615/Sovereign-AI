import base64
from typing import List, BinaryIO
from sovereign.core.knowledge.parser import DocumentParser
from sovereign.core.knowledge.models import Document, DocumentBlock
from sovereign.core.runtime.models import InferenceRequest
from sovereign.core.runtime.gateway import ModelGateway

class MultimodalParser(DocumentParser):
    def __init__(self, gateway: ModelGateway):
        self.gateway = gateway
        
    def parse(self, document: Document, file_stream: BinaryIO) -> List[DocumentBlock]:
        data = file_stream.read()
        b64_data = base64.b64encode(data).decode('utf-8')
        
        # Determine mime type from extension
        ext = document.filename.split('.')[-1].lower() if document.filename else 'png'
        mime = f"image/{ext}" if ext in ('png', 'jpeg', 'jpg') else "image/png"
        data_uri = f"data:{mime};base64,{b64_data}"
        
        request = InferenceRequest(
            prompt="Extract and transcribe all relevant structural and semantic knowledge from this image. Format the response as a single, clear explanation.",
            images=[data_uri],
            max_tokens=1024
        )
        
        response = self.gateway.generate(request)
        
        blocks = []
        if response.text.strip():
            blocks.append(DocumentBlock(
                document_id=document.document_id,
                page_number=document.metadata.get("page_number", 1) if document.metadata else 1,
                sequence=0,
                text=response.text.strip(),
                block_type="multimodal_interpretation"
            ))
            
        return blocks
