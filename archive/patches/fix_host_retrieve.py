with open('src/sovereign/core/agent/host.py', 'r') as f:
    content = f.read()

replacement = '''
            elif decision.action == AgentAction.RETRIEVE:
                top_k = min(decision.top_k or 5, self.max_retrieval_results)
                try:
                    results = self.retriever.retrieve(query=decision.query, top_k=top_k)
                    ev_ids = []
                    for r in results:
                        ev = EvidenceReference(
                            source_id=r.document_id,
                            locator=r.page or "N/A",
                            metadata={"chunk_id": r.chunk_id, "text": r.text, "score": r.score}
                        )
                        self.repo.add_evidence(task.task_id, ev)
                        ev_ids.append(ev.evidence_id)
                    
                    if not results:
                         self.repo.add_state_item(task.task_id, Finding(statement=f"No results found for query: {decision.query}", confidence="high"))
                    else:
                         self.repo.add_state_item(task.task_id, Finding(statement=f"Retrieved {len(results)} results for query: {decision.query}", confidence="high", evidence_refs=ev_ids))
                         
                except Exception as e:
'''

target = '''
            elif decision.action == AgentAction.RETRIEVE:
                top_k = min(decision.top_k or 5, self.max_retrieval_results)
                try:
                    results = self.retriever.retrieve(query=decision.query, top_k=top_k)
                    for r in results:
                        ev = EvidenceReference(
                            source_id=r.document_id,
                            locator=r.page or "N/A",
                            metadata={"chunk_id": r.chunk_id, "text": r.text, "score": r.score}
                        )
                        self.repo.add_evidence(task.task_id, ev)
                    
                    if not results:
                         self.repo.add_state_item(task.task_id, Finding(statement=f"No results found for query: {decision.query}", confidence="high"))
                         
                except Exception as e:
'''

content = content.replace(target.lstrip('\n'), replacement.lstrip('\n'))

with open('src/sovereign/core/agent/host.py', 'w') as f:
    f.write(content)

print("Patch applied for AgentAction.RETRIEVE.")
