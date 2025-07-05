"""
Knowledge Manager for Letta Knowledge Management System
Handles document processing, note management, and knowledge base operations
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib
import pickle

import sqlite3
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import docx
from PIL import Image
import pandas as pd

logger = logging.getLogger(__name__)

class KnowledgeManager:
    """Manages knowledge base operations including documents, notes, and search"""
    
    def __init__(self):
        self.db_path = './data/knowledge.db'
        self.embeddings_model = None
        self.initialize_database()
        self.initialize_embeddings()
        
    def initialize_database(self):
        """Initialize SQLite database for knowledge management"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs('./data', exist_ok=True)
            
            # Create database connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    content TEXT,
                    metadata TEXT,
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    results_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Knowledge database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge database: {e}")
            raise
    
    def initialize_embeddings(self):
        """Initialize sentence transformer model for embeddings"""
        try:
            model_name = 'all-MiniLM-L6-v2'  # Lightweight and fast
            self.embeddings_model = SentenceTransformer(model_name)
            logger.info(f"Initialized embeddings model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize embeddings model: {e}")
            # Fallback to a simpler approach if model fails
            self.embeddings_model = None
    
    def process_file(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """Process uploaded file and extract content"""
        try:
            file_size = os.path.getsize(file_path)
            file_type = self._get_file_type(original_filename)
            
            # Extract content based on file type
            content = ""
            metadata = {}
            
            if file_type == 'pdf':
                content, metadata = self._extract_pdf_content(file_path)
            elif file_type == 'docx':
                content, metadata = self._extract_docx_content(file_path)
            elif file_type == 'txt':
                content, metadata = self._extract_text_content(file_path)
            elif file_type == 'csv':
                content, metadata = self._extract_csv_content(file_path)
            elif file_type == 'excel':
                content, metadata = self._extract_excel_content(file_path)
            else:
                content = f"Unsupported file type: {file_type}"
                metadata = {'error': 'Unsupported file type'}
            
            # Generate embedding
            embedding = self._generate_embedding(content)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO documents 
                (filename, original_filename, file_type, file_size, content, metadata, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                os.path.basename(file_path),
                original_filename,
                file_type,
                file_size,
                content,
                json.dumps(metadata),
                pickle.dumps(embedding) if embedding is not None else None
            ))
            
            document_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'id': document_id,
                'filename': original_filename,
                'file_type': file_type,
                'file_size': file_size,
                'content_length': len(content),
                'metadata': metadata,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing file {original_filename}: {e}")
            raise
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type from extension"""
        extension = os.path.splitext(filename)[1].lower()
        
        type_mapping = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.doc': 'docx',
            '.txt': 'txt',
            '.md': 'txt',
            '.csv': 'csv',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.json': 'json',
            '.xml': 'xml'
        }
        
        return type_mapping.get(extension, 'unknown')
    
    def _extract_pdf_content(self, file_path: str) -> tuple:
        """Extract content from PDF file"""
        try:
            content = ""
            metadata = {'pages': 0, 'method': 'PyPDF2'}
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata['pages'] = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            
            return content, metadata
            
        except Exception as e:
            logger.error(f"Error extracting PDF content: {e}")
            return f"Error extracting PDF: {str(e)}", {'error': str(e)}
    
    def _extract_docx_content(self, file_path: str) -> tuple:
        """Extract content from DOCX file"""
        try:
            doc = docx.Document(file_path)
            content = ""
            metadata = {'paragraphs': 0, 'method': 'python-docx'}
            
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
                metadata['paragraphs'] += 1
            
            return content, metadata
            
        except Exception as e:
            logger.error(f"Error extracting DOCX content: {e}")
            return f"Error extracting DOCX: {str(e)}", {'error': str(e)}
    
    def _extract_text_content(self, file_path: str) -> tuple:
        """Extract content from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            metadata = {
                'lines': len(content.split('\n')),
                'characters': len(content),
                'method': 'direct_read'
            }
            
            return content, metadata
            
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return f"Error extracting text: {str(e)}", {'error': str(e)}
    
    def _extract_csv_content(self, file_path: str) -> tuple:
        """Extract content from CSV file"""
        try:
            df = pd.read_csv(file_path)
            content = df.to_string()
            
            metadata = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'method': 'pandas'
            }
            
            return content, metadata
            
        except Exception as e:
            logger.error(f"Error extracting CSV content: {e}")
            return f"Error extracting CSV: {str(e)}", {'error': str(e)}
    
    def _extract_excel_content(self, file_path: str) -> tuple:
        """Extract content from Excel file"""
        try:
            df = pd.read_excel(file_path)
            content = df.to_string()
            
            metadata = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'method': 'pandas'
            }
            
            return content, metadata
            
        except Exception as e:
            logger.error(f"Error extracting Excel content: {e}")
            return f"Error extracting Excel: {str(e)}", {'error': str(e)}
    
    def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text"""
        try:
            if self.embeddings_model is None or not text.strip():
                return None
            
            # Clean and prepare text
            text = text.strip()[:1000]  # Limit text length for performance
            
            # Generate embedding
            embedding = self.embeddings_model.encode(text)
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def create_note(self, title: str, content: str, tags: List[str] = None) -> Dict[str, Any]:
        """Create a new note"""
        try:
            if tags is None:
                tags = []
            
            # Generate embedding
            full_text = f"{title}\n{content}"
            embedding = self._generate_embedding(full_text)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notes (title, content, tags, embedding)
                VALUES (?, ?, ?, ?)
            ''', (
                title,
                content,
                json.dumps(tags),
                pickle.dumps(embedding) if embedding is not None else None
            ))
            
            note_id = cursor.lastrowid
            conn.commit()
            
            # Update tag counts
            for tag in tags:
                cursor.execute('''
                    INSERT OR REPLACE INTO tags (name, count)
                    VALUES (?, COALESCE((SELECT count FROM tags WHERE name = ?), 0) + 1)
                ''', (tag, tag))
            
            conn.commit()
            conn.close()
            
            return {
                'id': note_id,
                'title': title,
                'content': content,
                'tags': tags,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            raise
    
    def get_all_notes(self) -> List[Dict[str, Any]]:
        """Get all notes from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, content, tags, created_at, updated_at
                FROM notes
                ORDER BY updated_at DESC
            ''')
            
            notes = []
            for row in cursor.fetchall():
                notes.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'tags': json.loads(row[3]) if row[3] else [],
                    'created_at': row[4],
                    'updated_at': row[5]
                })
            
            conn.close()
            return notes
            
        except Exception as e:
            logger.error(f"Error getting notes: {e}")
            return []
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, original_filename, file_type, file_size, created_at
                FROM documents
                ORDER BY created_at DESC
            ''')
            
            documents = []
            for row in cursor.fetchall():
                documents.append({
                    'id': row[0],
                    'filename': row[1],
                    'file_type': row[2],
                    'file_size': row[3],
                    'created_at': row[4]
                })
            
            conn.close()
            return documents
            
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search through knowledge base using both text and semantic search"""
        try:
            # Generate embedding for query
            query_embedding = self._generate_embedding(query)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Text-based search in documents
            cursor.execute('''
                SELECT id, original_filename, file_type, content, created_at, 'document' as type
                FROM documents
                WHERE content LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (f'%{query}%', limit))
            
            doc_results = cursor.fetchall()
            
            # Text-based search in notes
            cursor.execute('''
                SELECT id, title, content, tags, created_at, 'note' as type
                FROM notes
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', limit))
            
            note_results = cursor.fetchall()
            
            # Combine results
            results = []
            
            # Process document results
            for row in doc_results:
                results.append({
                    'id': row[0],
                    'title': row[1],
                    'type': row[5],
                    'content': row[3][:200] + "..." if len(row[3]) > 200 else row[3],
                    'created_at': row[4],
                    'relevance_score': 0.5  # Default text match score
                })
            
            # Process note results
            for row in note_results:
                results.append({
                    'id': row[0],
                    'title': row[1],
                    'type': row[5],
                    'content': row[2][:200] + "..." if len(row[2]) > 200 else row[2],
                    'tags': json.loads(row[3]) if row[3] else [],
                    'created_at': row[4],
                    'relevance_score': 0.5  # Default text match score
                })
            
            # If we have embeddings, perform semantic search
            if query_embedding is not None:
                results = self._enhance_with_semantic_search(results, query_embedding, conn)
            
            # Sort by relevance score
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Log search query
            cursor.execute('''
                INSERT INTO search_history (query, results_count)
                VALUES (?, ?)
            ''', (query, len(results)))
            
            conn.commit()
            conn.close()
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def _enhance_with_semantic_search(self, results: List[Dict], query_embedding: np.ndarray, conn: sqlite3.Connection) -> List[Dict]:
        """Enhance search results with semantic similarity scores"""
        try:
            cursor = conn.cursor()
            
            # Get embeddings for existing results
            for result in results:
                if result['type'] == 'document':
                    cursor.execute('SELECT embedding FROM documents WHERE id = ?', (result['id'],))
                else:
                    cursor.execute('SELECT embedding FROM notes WHERE id = ?', (result['id'],))
                
                row = cursor.fetchone()
                if row and row[0]:
                    try:
                        item_embedding = pickle.loads(row[0])
                        # Calculate cosine similarity
                        similarity = cosine_similarity([query_embedding], [item_embedding])[0][0]
                        result['relevance_score'] = max(result['relevance_score'], similarity)
                    except Exception as e:
                        logger.warning(f"Error calculating similarity: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error enhancing with semantic search: {e}")
            return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count documents
            cursor.execute('SELECT COUNT(*) FROM documents')
            doc_count = cursor.fetchone()[0]
            
            # Count notes
            cursor.execute('SELECT COUNT(*) FROM notes')
            note_count = cursor.fetchone()[0]
            
            # Count tags
            cursor.execute('SELECT COUNT(*) FROM tags')
            tag_count = cursor.fetchone()[0]
            
            # Get recent searches
            cursor.execute('SELECT COUNT(*) FROM search_history')
            search_count = cursor.fetchone()[0]
            
            # Get total file size
            cursor.execute('SELECT SUM(file_size) FROM documents')
            total_size = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'documents': doc_count,
                'notes': note_count,
                'tags': tag_count,
                'searches': search_count,
                'total_size': total_size,
                'embeddings_enabled': self.embeddings_model is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def delete_note(self, note_id: int) -> bool:
        """Delete a note"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting note: {e}")
            return False
    
    def delete_document(self, document_id: int) -> bool:
        """Delete a document"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM documents WHERE id = ?', (document_id,))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False