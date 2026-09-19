"""SQLite knowledge base implementation."""

import sqlite3
import json
from contextlib import contextmanager
from typing import List, Optional, Dict, Any, ContextManager
from pathlib import Path
from datetime import datetime

from sovereign.infrastructure.config import get_settings
from sovereign.infrastructure.paths import get_data_dir
from sovereign.core.exceptions import StateError
from sovereign.core.knowledge.models import Document, DocumentStatus, DocumentChunk, RetrievalResult
from sovereign.core.knowledge.registry import DocumentRegistry, DocumentStore
from sovereign.core.knowledge.index import KnowledgeIndex
from sovereign.core.knowledge.retriever import Retriever

class SQLiteKnowledgeBase(DocumentRegistry, DocumentStore, KnowledgeIndex, Retriever):
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            settings = get_settings()
            db_path = get_data_dir() / "knowledge.db"
            
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, isolation_level="DEFERRED")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            with conn:
                # Document Registry
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        document_id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        source_path TEXT NOT NULL,
                        document_type TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        content_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        ingested_at TEXT,
                        status TEXT NOT NULL,
                        metadata TEXT NOT NULL
                    )
                """)
                # Chunk Store
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        chunk_id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        text TEXT NOT NULL,
                        sequence INTEGER NOT NULL,
                        page_range TEXT,
                        section TEXT,
                        metadata TEXT NOT NULL,
                        token_estimate INTEGER NOT NULL,
                        FOREIGN KEY(document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                    )
                """)
                # FTS5 Index for retrieval
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                        chunk_id UNINDEXED,
                        document_id UNINDEXED,
                        text,
                        content='chunks',
                        content_rowid='rowid'
                    )
                """)
                # Triggers to keep FTS index synced with chunks
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                        INSERT INTO chunks_fts(rowid, chunk_id, document_id, text) 
                        VALUES (new.rowid, new.chunk_id, new.document_id, new.text);
                    END;
                """)
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                        INSERT INTO chunks_fts(chunks_fts, rowid, chunk_id, document_id, text) 
                        VALUES('delete', old.rowid, old.chunk_id, old.document_id, old.text);
                    END;
                """)
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
                        INSERT INTO chunks_fts(chunks_fts, rowid, chunk_id, document_id, text) 
                        VALUES('delete', old.rowid, old.chunk_id, old.document_id, old.text);
                        INSERT INTO chunks_fts(rowid, chunk_id, document_id, text) 
                        VALUES (new.rowid, new.chunk_id, new.document_id, new.text);
                    END;
                """)
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> ContextManager[sqlite3.Connection]:
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise StateError(f"Knowledge Base transaction failed: {e}") from e
        finally:
            conn.close()

    # --- DocumentRegistry Implementation ---
    
    def register_document(self, document: Document) -> None:
        with self.transaction() as conn:
            ingested_at = document.ingested_at.isoformat() if document.ingested_at else None
            conn.execute(
                """INSERT INTO documents 
                   (document_id, filename, source_path, document_type, file_size, content_hash, created_at, ingested_at, status, metadata) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (document.document_id, document.filename, document.source_path, document.document_type,
                 document.file_size, document.content_hash, document.created_at.isoformat(), 
                 ingested_at, document.status.value, json.dumps(document.metadata))
            )

    def update_document(self, document: Document) -> None:
        with self.transaction() as conn:
            ingested_at = document.ingested_at.isoformat() if document.ingested_at else None
            conn.execute(
                """UPDATE documents SET 
                   filename=?, source_path=?, document_type=?, file_size=?, content_hash=?, 
                   ingested_at=?, status=?, metadata=? 
                   WHERE document_id=?""",
                (document.filename, document.source_path, document.document_type, document.file_size, 
                 document.content_hash, ingested_at, document.status.value, 
                 json.dumps(document.metadata), document.document_id)
            )

    def _row_to_document(self, row: sqlite3.Row) -> Document:
        return Document(
            document_id=row['document_id'],
            filename=row['filename'],
            source_path=row['source_path'],
            document_type=row['document_type'],
            file_size=row['file_size'],
            content_hash=row['content_hash'],
            created_at=datetime.fromisoformat(row['created_at']),
            ingested_at=datetime.fromisoformat(row['ingested_at']) if row['ingested_at'] else None,
            status=DocumentStatus(row['status']),
            metadata=json.loads(row['metadata'])
        )

    def get_document(self, document_id: str) -> Optional[Document]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,)).fetchone()
            if not row:
                return None
            return self._row_to_document(row)
        finally:
            conn.close()

    def list_documents(self) -> List[Document]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
            return [self._row_to_document(row) for row in rows]
        finally:
            conn.close()

    def find_by_hash(self, content_hash: str) -> Optional[Document]:

        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM documents WHERE content_hash = ?", (content_hash,)).fetchone()
            if not row:
                return None
            return self._row_to_document(row)
        finally:
            conn.close()

    def find_by_path(self, source_path: str) -> Optional[Document]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM documents WHERE source_path = ?", (source_path,)).fetchone()
            if not row:
                return None
            return self._row_to_document(row)
        finally:
            conn.close()

    # --- DocumentStore Implementation ---
    
    def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        with self.transaction() as conn:
            for chunk in chunks:
                conn.execute(
                    """INSERT INTO chunks 
                       (chunk_id, document_id, text, sequence, page_range, section, metadata, token_estimate) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (chunk.chunk_id, chunk.document_id, chunk.text, chunk.sequence,
                     chunk.page_range, chunk.section, json.dumps(chunk.metadata), chunk.token_estimate)
                )

    def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,)).fetchone()
            if not row:
                return None
            return DocumentChunk(
                chunk_id=row['chunk_id'],
                document_id=row['document_id'],
                text=row['text'],
                sequence=row['sequence'],
                page_range=row['page_range'],
                section=row['section'],
                metadata=json.loads(row['metadata']),
                token_estimate=row['token_estimate']
            )
        finally:
            conn.close()

    def delete_chunks_for_document(self, document_id: str) -> None:
        with self.transaction() as conn:
            # Delete triggers chunks_fts sync automatically
            conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))

    def get_chunks_for_document(self, document_id: str) -> List[DocumentChunk]:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM chunks WHERE document_id = ? ORDER BY sequence ASC",
                (document_id,)
            ).fetchall()
            return [
                DocumentChunk(
                    chunk_id=row['chunk_id'],
                    document_id=row['document_id'],
                    text=row['text'],
                    sequence=row['sequence'],
                    page_range=row['page_range'],
                    section=row['section'],
                    metadata=json.loads(row['metadata']),
                    token_estimate=row['token_estimate']
                )
                for row in rows
            ]
        finally:
            conn.close()

    # --- KnowledgeIndex Implementation ---
    
    def index_chunks(self, chunks: List[DocumentChunk]) -> None:
        # Relying on FTS5 triggers on the `chunks` table.
        # By inserting into chunks, the FTS index is automatically updated.
        pass

    def remove_document(self, document_id: str) -> None:
        # Relying on FTS5 triggers on the `chunks` table.
        pass

    # --- Retriever Implementation ---
    
    def retrieve(self, query: str, top_k: int = 5, document_id: Optional[str] = None) -> List[RetrievalResult]:
        conn = self._get_connection()
        try:
            # We use standard FTS5 syntax
            # By default FTS5 uses a simple tokenizer that does case-folding and ignores punctuation.
            # BM25 is built-in. score is negative (lower is better in sqlite fts5)
            # We want to multiply by -1 to get a positive score.
            
            # Simple query normalization
            import re
            clean_query = re.sub(r'[^\w\s-]', ' ', query)
            terms = [t.strip() for t in clean_query.split() if t.strip()]
            if not terms:
                return []

            stopwords = {
                'a', 'an', 'the', 'and', 'or', 'to', 'in', 'on', 'at', 'for', 'of',
                'with', 'by', 'from', 'is', 'are', 'was', 'were', 'does', 'did',
                'what', 'which', 'who', 'how', 'according', 'it', 'its', 'uploaded',
                'this', 'that', 'these', 'those', 'as', 'be', 'can', 'if', 'we'
            }
            significant_terms = [t for t in terms if t.lower() not in stopwords]
            search_terms = significant_terms if significant_terms else terms
            
            # 1. Try strict AND on significant terms
            fts_query_and = " AND ".join(f'"{term}"' for term in search_terms)
            
            sql = """
                SELECT 
                    c.chunk_id,
                    c.document_id,
                    c.text,
                    c.page_range,
                    c.section,
                    c.metadata,
                    d.source_path,
                    bm25(chunks_fts) * -1.0 as score
                FROM chunks_fts fts
                JOIN chunks c ON fts.rowid = c.rowid
                JOIN documents d ON c.document_id = d.document_id
                WHERE chunks_fts MATCH ?
            """
            params = [fts_query_and]
            if document_id:
                sql += " AND c.document_id = ?"
                params.append(document_id)
            sql += " ORDER BY score DESC, c.sequence ASC LIMIT ?"
            params.append(top_k)
            
            rows = conn.execute(sql, tuple(params)).fetchall()
            
            # 2. If AND returned no results, fallback to ranked OR on significant terms
            if not rows and len(search_terms) > 1:
                fts_query_or = " OR ".join(f'"{term}"' for term in search_terms)
                params_or = [fts_query_or]
                sql_or = """
                    SELECT 
                        c.chunk_id,
                        c.document_id,
                        c.text,
                        c.page_range,
                        c.section,
                        c.metadata,
                        d.source_path,
                        bm25(chunks_fts) * -1.0 as score
                    FROM chunks_fts fts
                    JOIN chunks c ON fts.rowid = c.rowid
                    JOIN documents d ON c.document_id = d.document_id
                    WHERE chunks_fts MATCH ?
                """
                if document_id:
                    sql_or += " AND c.document_id = ?"
                    params_or.append(document_id)
                sql_or += " ORDER BY score DESC, c.sequence ASC LIMIT ?"
                params_or.append(top_k)
                raw_rows = conn.execute(sql_or, tuple(params_or)).fetchall()
                
                # Filter out low-overlap chunks when multiple search terms exist
                rows = []
                for r in raw_rows:
                    chunk_text_lower = r['text'].lower()
                    matched_count = sum(1 for term in search_terms if term.lower() in chunk_text_lower)
                    min_required = 2 if len(search_terms) >= 3 else 1
                    if matched_count >= min_required:
                        rows.append(r)
            
            results = []
            for row in rows:
                results.append(RetrievalResult(
                    chunk_id=row['chunk_id'],
                    document_id=row['document_id'],
                    score=row['score'],
                    text=row['text'],
                    page=row['page_range'],
                    section=row['section'],
                    source_path=row['source_path'],
                    metadata=json.loads(row['metadata'])
                ))
            return results
        finally:
            conn.close()
