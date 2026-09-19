"""Knowledge search tool integrating Package 03."""

from pydantic import BaseModel, Field
from typing import Dict, Any, List

from sovereign.core.capabilities.models import ToolDefinition, ToolImplementation, CapabilityType
from sovereign.infrastructure.knowledge.sqlite_knowledge import SQLiteKnowledgeBase

class SearchKnowledgeInput(BaseModel):
    query: str = Field(description="The search query.")
    top_k: int = Field(default=5, description="Number of results to retrieve. Max bounded to 20.")
    
def search_knowledge_handler(inputs: SearchKnowledgeInput) -> List[Dict[str, Any]]:
    query = inputs.query
    
    # 1. Output Bounding: Never allow an unbounded retrieval payload
    top_k = min(inputs.top_k, 20)
    
    # 2. Integrate directly with Package 03
    kb = SQLiteKnowledgeBase()
    results = kb.retrieve(query=query, top_k=top_k)
    
    # 3. Return bounded, structured metadata
    output = []
    for r in results:
        output.append({
            "chunk_id": r.chunk_id,
            "document_id": r.document_id,
            "text": r.text,
            "page": r.page,
            "section": r.section,
            "source_path": r.source_path,
            "score": r.score
        })
    return output

def get_search_knowledge_tool() -> ToolImplementation:
    definition = ToolDefinition(
        tool_id="core-kb-001",
        name="search_knowledge",
        description="Searches the local knowledge base. Bounded to a maximum of 20 results.",
        input_schema=SearchKnowledgeInput.model_json_schema(),
        output_schema={"type": "array"},
        capability=CapabilityType.READ_ONLY
    )
    return ToolImplementation(
        definition=definition,
        handler=search_knowledge_handler,
        input_model=SearchKnowledgeInput
    )
