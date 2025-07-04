"""
Knowledge Search Tool for Letta Agent
Handles searching through the knowledge base including documents and notes
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
import sqlite3
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class KnowledgeSearchTool:
    """Tool for searching through the knowledge base"""
    
    def __init__(self):
        self.name = "knowledge_search"
        self.description = "Search through documents, notes, and knowledge base using text and semantic search"
        self.knowledge_db_path = "./data/knowledge.db"
        self.notes_db_path = "./data/notes.db"
        self.data_dir = "./data"
        self.embeddings_model = None
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        self.initialize_embeddings()
    
    def initialize_embeddings(self):
        """Initialize sentence transformer model for semantic search"""
        try:
            model_name = 'all-MiniLM-L6-v2'
            self.embeddings_model = SentenceTransformer(model_name)
            logger.info(f"Initialized embeddings model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings model: {e}")
            self.embeddings_model = None
    
    def get_function_schema(self) -> Dict[str, Any]:
        """Get the function schema for Letta"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant information"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["all", "documents", "notes", "semantic", "text"],
                        "description": "Type of search to perform"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return"
                    },
                    "min_relevance": {
                        "type": "number",
                        "description": "Minimum relevance score (0.0 to 1.0) for semantic search"
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category or tag"
                    }
                },
                "required": ["query"]
            }
        }
    
    def execute(self, query: str, search_type: str = "all", limit: int = 10,
                min_relevance: float = 0.3, category: str = None) -> Dict[str, Any]:
        """Execute knowledge search"""
        try:
            if not query:
                return {"error": "Search query is required"}
            
            results = []
            
            if search_type in ["all", "documents"]:
                doc_results = self._search_documents(query, limit, min_relevance, category)
                results.extend(doc_results)
            
            if search_type in ["all", "notes"]:
                note_results = self._search_notes(query, limit, min_relevance, category)
                results.extend(note_results)
            
            if search_type == "semantic" and self.embeddings_model:
                semantic_results = self._semantic_search_all(query, limit, min_relevance)
                results.extend(semantic_results)
            
            # Remove duplicates and sort by relevance
            unique_results = self._deduplicate_results(results)
            sorted_results = sorted(unique_results, key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Limit final results
            final_results = sorted_results[:limit]
            
            return {
                "success": True,
                "query": query,
                "search_type": search_type,
                "count": len(final_results),
                "results": final_results,
                "semantic_enabled": self.embeddings_model is not None
            }
            
        except Exception as e:
            logger.error(f"Error in knowledge search: {e}")
            return {"error": str(e)}
    
    def _search_documents(self, query: str, limit: int, min_relevance: float, category: str) -> List[Dict[str, Any]]:
        """Search through documents"""
        try:
            if not os.path.exists(self.knowledge_db_path):
                return []
            
            conn = sqlite3.connect(self.knowledge_db_path)
            cursor = conn.cursor()
            
            # Text-based search
            sql = '''
                SELECT id, original_filename, file_type, content, metadata, embedding, created_at
                FROM documents
                WHERE content LIKE ?
            '''
            params = [f'%{query}%']
            
            if category:
                sql += ' AND (file_type LIKE ? OR metadata LIKE ?)'
                params.extend([f'%{category}%', f'%{category}%'])
            
            sql += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                doc_id, filename, file_type, content, metadata, embedding, created_at = row
                
                # Calculate relevance score
                relevance_score = self._calculate_text_relevance(query, content)
                
                # Try semantic search if embedding exists
                if embedding and self.embeddings_model:
                    try:
                        query_embedding = self.embeddings_model.encode(query)
                        doc_embedding = pickle.loads(embedding)
                        semantic_score = cosine_similarity([query_embedding], [doc_embedding])[0][0]
                        relevance_score = max(relevance_score, semantic_score)
                    except Exception as e:
                        logger.warning(f"Error in semantic similarity: {e}")
                
                if relevance_score >= min_relevance:
                    # Extract relevant snippet
                    snippet = self._extract_snippet(content, query, max_length=300)
                    
                    results.append({
                        "id": doc_id,
                        "type": "document",
                        "title": filename,
                        "file_type": file_type,
                        "content": snippet,
                        "metadata": json.loads(metadata) if metadata else {},
                        "created_at": created_at,
                        "relevance_score": relevance_score,
                        "source": "documents"
                    })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def _search_notes(self, query: str, limit: int, min_relevance: float, category: str) -> List[Dict[str, Any]]:
        """Search through notes"""
        try:
            if not os.path.exists(self.notes_db_path):
                return []
            
            conn = sqlite3.connect(self.notes_db_path)
            cursor = conn.cursor()
            
            # Text-based search
            sql = '''
                SELECT id, title, content, tags, embedding, created_at, priority
                FROM notes
                WHERE (title LIKE ? OR content LIKE ?)
                AND archived = FALSE
            '''
            params = [f'%{query}%', f'%{query}%']
            
            if category:
                sql += ' AND tags LIKE ?'
                params.append(f'%{category}%')
            
            sql += ' ORDER BY priority DESC, created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                note_id, title, content, tags, embedding, created_at, priority = row
                
                # Calculate relevance score
                full_text = f"{title}\n{content}"
                relevance_score = self._calculate_text_relevance(query, full_text)
                
                # Try semantic search if embedding exists
                if embedding and self.embeddings_model:
                    try:
                        query_embedding = self.embeddings_model.encode(query)
                        note_embedding = pickle.loads(embedding)
                        semantic_score = cosine_similarity([query_embedding], [note_embedding])[0][0]
                        relevance_score = max(relevance_score, semantic_score)
                    except Exception as e:
                        logger.warning(f"Error in semantic similarity: {e}")
                
                if relevance_score >= min_relevance:
                    # Extract relevant snippet
                    snippet = self._extract_snippet(content, query, max_length=200)
                    
                    results.append({
                        "id": note_id,
                        "type": "note",
                        "title": title,
                        "content": snippet,
                        "tags": json.loads(tags) if tags else [],
                        "created_at": created_at,
                        "priority": priority,
                        "relevance_score": relevance_score,
                        "source": "notes"
                    })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            return []
    
    def _semantic_search_all(self, query: str, limit: int, min_relevance: float) -> List[Dict[str, Any]]:
        """Perform semantic search across all content"""
        try:
            if not self.embeddings_model:
                return []
            
            query_embedding = self.embeddings_model.encode(query)
            results = []
            
            # Search documents
            if os.path.exists(self.knowledge_db_path):
                conn = sqlite3.connect(self.knowledge_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, original_filename, file_type, content, embedding, created_at
                    FROM documents
                    WHERE embedding IS NOT NULL
                ''')
                
                for row in cursor.fetchall():
                    doc_id, filename, file_type, content, embedding, created_at = row
                    try:
                        doc_embedding = pickle.loads(embedding)
                        similarity = cosine_similarity([query_embedding], [doc_embedding])[0][0]
                        
                        if similarity >= min_relevance:
                            snippet = self._extract_snippet(content, query, max_length=300)
                            results.append({
                                "id": doc_id,
                                "type": "document",
                                "title": filename,
                                "file_type": file_type,
                                "content": snippet,
                                "created_at": created_at,
                                "relevance_score": similarity,
                                "source": "semantic_documents"
                            })
                    except Exception as e:
                        logger.warning(f"Error processing document embedding: {e}")
                
                conn.close()
            
            # Search notes
            if os.path.exists(self.notes_db_path):
                conn = sqlite3.connect(self.notes_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, title, content, tags, embedding, created_at, priority
                    FROM notes
                    WHERE embedding IS NOT NULL AND archived = FALSE
                ''')
                
                for row in cursor.fetchall():
                    note_id, title, content, tags, embedding, created_at, priority = row
                    try:
                        note_embedding = pickle.loads(embedding)
                        similarity = cosine_similarity([query_embedding], [note_embedding])[0][0]
                        
                        if similarity >= min_relevance:
                            snippet = self._extract_snippet(content, query, max_length=200)
                            results.append({
                                "id": note_id,
                                "type": "note",
                                "title": title,
                                "content": snippet,
                                "tags": json.loads(tags) if tags else [],
                                "created_at": created_at,
                                "priority": priority,
                                "relevance_score": similarity,
                                "source": "semantic_notes"
                            })
                    except Exception as e:
                        logger.warning(f"Error processing note embedding: {e}")
                
                conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _calculate_text_relevance(self, query: str, text: str) -> float:
        """Calculate text-based relevance score"""
        try:
            query_lower = query.lower()
            text_lower = text.lower()
            
            # Count exact matches
            exact_matches = text_lower.count(query_lower)
            
            # Count word matches
            query_words = set(query_lower.split())
            text_words = set(text_lower.split())
            word_matches = len(query_words.intersection(text_words))
            
            # Calculate score based on matches and text length
            if len(text) == 0:
                return 0.0
            
            # Normalize by text length (prefer shorter, more relevant snippets)
            length_factor = min(1.0, 1000.0 / len(text))
            
            # Combine exact matches and word matches
            score = (exact_matches * 2 + word_matches) / len(query_words)
            score = min(1.0, score * length_factor)
            
            return score
            
        except Exception as e:
            logger.warning(f"Error calculating text relevance: {e}")
            return 0.0
    
    def _extract_snippet(self, text: str, query: str, max_length: int = 300) -> str:
        """Extract relevant snippet from text around query match"""
        try:
            if not text or not query:
                return text[:max_length] if text else ""
            
            text_lower = text.lower()
            query_lower = query.lower()
            
            # Find the first occurrence of the query
            match_pos = text_lower.find(query_lower)
            
            if match_pos == -1:
                # No exact match, look for word matches
                query_words = query_lower.split()
                for word in query_words:
                    match_pos = text_lower.find(word)
                    if match_pos != -1:
                        break
            
            if match_pos == -1:
                # No matches found, return beginning of text
                return text[:max_length] + ("..." if len(text) > max_length else "")
            
            # Calculate snippet boundaries
            snippet_start = max(0, match_pos - max_length // 3)
            snippet_end = min(len(text), match_pos + max_length * 2 // 3)
            
            # Adjust to word boundaries
            if snippet_start > 0:
                # Find the next space to start at a word boundary
                space_pos = text.find(' ', snippet_start)
                if space_pos != -1 and space_pos < snippet_start + 50:
                    snippet_start = space_pos + 1
            
            if snippet_end < len(text):
                # Find the previous space to end at a word boundary
                space_pos = text.rfind(' ', snippet_start, snippet_end)
                if space_pos != -1:
                    snippet_end = space_pos
            
            snippet = text[snippet_start:snippet_end]
            
            # Add ellipsis if needed
            if snippet_start > 0:
                snippet = "..." + snippet
            if snippet_end < len(text):
                snippet = snippet + "..."
            
            return snippet
            
        except Exception as e:
            logger.warning(f"Error extracting snippet: {e}")
            return text[:max_length] + ("..." if len(text) > max_length else "")
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on content similarity"""
        try:
            if not results:
                return []
            
            unique_results = []
            seen_content = set()
            
            for result in results:
                # Create a content hash for deduplication
                content_key = f"{result.get('type', '')}-{result.get('id', '')}"
                
                if content_key not in seen_content:
                    seen_content.add(content_key)
                    unique_results.append(result)
            
            return unique_results
            
        except Exception as e:
            logger.warning(f"Error deduplicating results: {e}")
            return results