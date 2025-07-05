"""
Note Taker Tool for Letta Agent
Handles note creation, organization, and retrieval
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3

logger = logging.getLogger(__name__)

class NoteTakerTool:
    """Tool for managing notes and quick captures"""
    
    def __init__(self):
        self.name = "note_taker"
        self.description = "Create, organize, and manage notes with tagging and search capabilities"
        self.db_path = "./data/notes.db"
        self.data_dir = "./data"
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize the notes database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    priority INTEGER DEFAULT 0,
                    archived BOOLEAN DEFAULT FALSE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS note_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    count INTEGER DEFAULT 0,
                    color TEXT DEFAULT '#007bff'
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize notes database: {e}")
    
    def get_function_schema(self) -> Dict[str, Any]:
        """Get the function schema for Letta"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "list", "search", "update", "delete", "tag", "archive"],
                        "description": "Action to perform on notes"
                    },
                    "title": {
                        "type": "string",
                        "description": "Title of the note"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content of the note"
                    },
                    "tags": {
                        "type": "string",
                        "description": "Comma-separated tags for the note"
                    },
                    "note_id": {
                        "type": "integer",
                        "description": "ID of the note to operate on"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for finding notes"
                    },
                    "priority": {
                        "type": "integer",
                        "description": "Priority level (0-5, higher is more important)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["action"]
            }
        }
    
    def execute(self, action: str, title: str = None, content: str = None, 
                tags: str = None, note_id: int = None, query: str = None,
                priority: int = 0, limit: int = 20) -> Dict[str, Any]:
        """Execute note management action"""
        try:
            if action == "create":
                return self._create_note(title, content, tags, priority)
            elif action == "list":
                return self._list_notes(limit)
            elif action == "search":
                return self._search_notes(query, limit)
            elif action == "update":
                return self._update_note(note_id, title, content, tags, priority)
            elif action == "delete":
                return self._delete_note(note_id)
            elif action == "tag":
                return self._manage_tags(tags)
            elif action == "archive":
                return self._archive_note(note_id)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error in note taker: {e}")
            return {"error": str(e)}
    
    def _create_note(self, title: str, content: str, tags: str = None, priority: int = 0) -> Dict[str, Any]:
        """Create a new note"""
        try:
            if not title or not content:
                return {"error": "Title and content are required"}
            
            # Parse tags
            tag_list = self._parse_tags(tags) if tags else []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notes (title, content, tags, priority)
                VALUES (?, ?, ?, ?)
            ''', (title, content, json.dumps(tag_list), priority))
            
            note_id = cursor.lastrowid
            
            # Update tag counts
            for tag in tag_list:
                cursor.execute('''
                    INSERT OR REPLACE INTO note_tags (name, count)
                    VALUES (?, COALESCE((SELECT count FROM note_tags WHERE name = ?), 0) + 1)
                ''', (tag, tag))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "note_id": note_id,
                "title": title,
                "content": content,
                "tags": tag_list,
                "priority": priority,
                "message": f"Note '{title}' created successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to create note: {str(e)}"}
    
    def _list_notes(self, limit: int = 20) -> Dict[str, Any]:
        """List recent notes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, content, tags, created_at, updated_at, priority, archived
                FROM notes
                WHERE archived = FALSE
                ORDER BY priority DESC, updated_at DESC
                LIMIT ?
            ''', (limit,))
            
            notes = []
            for row in cursor.fetchall():
                notes.append({
                    "id": row[0],
                    "title": row[1],
                    "content": row[2][:200] + "..." if len(row[2]) > 200 else row[2],
                    "tags": json.loads(row[3]),
                    "created_at": row[4],
                    "updated_at": row[5],
                    "priority": row[6],
                    "archived": bool(row[7])
                })
            
            conn.close()
            
            return {
                "success": True,
                "count": len(notes),
                "notes": notes
            }
            
        except Exception as e:
            return {"error": f"Failed to list notes: {str(e)}"}
    
    def _search_notes(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search notes by title, content, or tags"""
        try:
            if not query:
                return {"error": "Search query is required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, content, tags, created_at, updated_at, priority, archived
                FROM notes
                WHERE (title LIKE ? OR content LIKE ? OR tags LIKE ?)
                AND archived = FALSE
                ORDER BY priority DESC, updated_at DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            notes = []
            for row in cursor.fetchall():
                notes.append({
                    "id": row[0],
                    "title": row[1],
                    "content": row[2][:200] + "..." if len(row[2]) > 200 else row[2],
                    "tags": json.loads(row[3]),
                    "created_at": row[4],
                    "updated_at": row[5],
                    "priority": row[6],
                    "archived": bool(row[7])
                })
            
            conn.close()
            
            return {
                "success": True,
                "query": query,
                "count": len(notes),
                "notes": notes
            }
            
        except Exception as e:
            return {"error": f"Failed to search notes: {str(e)}"}
    
    def _update_note(self, note_id: int, title: str = None, content: str = None, 
                     tags: str = None, priority: int = None) -> Dict[str, Any]:
        """Update an existing note"""
        try:
            if not note_id:
                return {"error": "Note ID is required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current note
            cursor.execute('SELECT title, content, tags, priority FROM notes WHERE id = ?', (note_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"error": f"Note with ID {note_id} not found"}
            
            # Update fields
            new_title = title if title else row[0]
            new_content = content if content else row[1]
            new_tags = json.dumps(self._parse_tags(tags)) if tags else row[2]
            new_priority = priority if priority is not None else row[3]
            
            cursor.execute('''
                UPDATE notes
                SET title = ?, content = ?, tags = ?, priority = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_title, new_content, new_tags, new_priority, note_id))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "note_id": note_id,
                "title": new_title,
                "content": new_content,
                "tags": json.loads(new_tags),
                "priority": new_priority,
                "message": f"Note updated successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to update note: {str(e)}"}
    
    def _delete_note(self, note_id: int) -> Dict[str, Any]:
        """Delete a note"""
        try:
            if not note_id:
                return {"error": "Note ID is required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get note tags before deletion
            cursor.execute('SELECT tags FROM notes WHERE id = ?', (note_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"error": f"Note with ID {note_id} not found"}
            
            # Delete the note
            cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
            
            # Update tag counts
            tags = json.loads(row[0])
            for tag in tags:
                cursor.execute('''
                    UPDATE note_tags SET count = count - 1 WHERE name = ?
                ''', (tag,))
                
                # Remove tag if count becomes 0
                cursor.execute('DELETE FROM note_tags WHERE name = ? AND count <= 0', (tag,))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "note_id": note_id,
                "message": f"Note deleted successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to delete note: {str(e)}"}
    
    def _manage_tags(self, tags: str) -> Dict[str, Any]:
        """List or manage tags"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if tags:
                # Add new tags
                tag_list = self._parse_tags(tags)
                for tag in tag_list:
                    cursor.execute('''
                        INSERT OR IGNORE INTO note_tags (name, count) VALUES (?, 0)
                    ''', (tag,))
                
                conn.commit()
                
            # List all tags
            cursor.execute('SELECT name, count FROM note_tags ORDER BY count DESC')
            tag_data = cursor.fetchall()
            
            conn.close()
            
            return {
                "success": True,
                "tags": [{"name": tag[0], "count": tag[1]} for tag in tag_data],
                "total_tags": len(tag_data)
            }
            
        except Exception as e:
            return {"error": f"Failed to manage tags: {str(e)}"}
    
    def _archive_note(self, note_id: int) -> Dict[str, Any]:
        """Archive or unarchive a note"""
        try:
            if not note_id:
                return {"error": "Note ID is required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Toggle archived status
            cursor.execute('''
                UPDATE notes
                SET archived = NOT archived, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (note_id,))
            
            # Get new status
            cursor.execute('SELECT archived FROM notes WHERE id = ?', (note_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"error": f"Note with ID {note_id} not found"}
            
            conn.commit()
            conn.close()
            
            status = "archived" if row[0] else "unarchived"
            
            return {
                "success": True,
                "note_id": note_id,
                "status": status,
                "message": f"Note {status} successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to archive note: {str(e)}"}
    
    def _parse_tags(self, tags_str: str) -> List[str]:
        """Parse comma-separated tags string"""
        if not tags_str:
            return []
        
        tags = [tag.strip().lower() for tag in tags_str.split(',')]
        return [tag for tag in tags if tag]  # Remove empty tags