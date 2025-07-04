"""
File Manager Tool for Letta Agent
Handles file operations, uploads, organization, and retrieval
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class FileManagerTool:
    """Tool for managing files and documents"""
    
    def __init__(self):
        self.name = "file_manager"
        self.description = "Manage files and documents - upload, organize, list, and retrieve file information"
        self.upload_dir = "./uploads"
        self.data_dir = "./data"
        
        # Ensure directories exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
    
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
                        "enum": ["list", "info", "search", "organize", "delete"],
                        "description": "Action to perform on files"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the file to operate on"
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to operate in (optional)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for finding files"
                    },
                    "tag": {
                        "type": "string",
                        "description": "Tag to organize files by"
                    }
                },
                "required": ["action"]
            }
        }
    
    def execute(self, action: str, filename: str = None, directory: str = None, 
                query: str = None, tag: str = None) -> Dict[str, Any]:
        """Execute file management action"""
        try:
            if action == "list":
                return self._list_files(directory)
            elif action == "info":
                return self._get_file_info(filename)
            elif action == "search":
                return self._search_files(query)
            elif action == "organize":
                return self._organize_file(filename, tag)
            elif action == "delete":
                return self._delete_file(filename)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error in file manager: {e}")
            return {"error": str(e)}
    
    def _list_files(self, directory: str = None) -> Dict[str, Any]:
        """List files in directory"""
        try:
            target_dir = directory if directory else self.upload_dir
            
            if not os.path.exists(target_dir):
                return {"error": f"Directory {target_dir} does not exist"}
            
            files = []
            for filename in os.listdir(target_dir):
                file_path = os.path.join(target_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        "name": filename,
                        "size": stat.st_size,
                        "size_formatted": self._format_file_size(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": self._get_file_type(filename)
                    })
            
            return {
                "success": True,
                "directory": target_dir,
                "file_count": len(files),
                "files": files
            }
            
        except Exception as e:
            return {"error": f"Failed to list files: {str(e)}"}
    
    def _get_file_info(self, filename: str) -> Dict[str, Any]:
        """Get detailed information about a file"""
        try:
            if not filename:
                return {"error": "Filename is required"}
            
            file_path = os.path.join(self.upload_dir, filename)
            
            if not os.path.exists(file_path):
                return {"error": f"File {filename} not found"}
            
            stat = os.stat(file_path)
            
            return {
                "success": True,
                "name": filename,
                "path": file_path,
                "size": stat.st_size,
                "size_formatted": self._format_file_size(stat.st_size),
                "type": self._get_file_type(filename),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessible": os.access(file_path, os.R_OK),
                "writable": os.access(file_path, os.W_OK)
            }
            
        except Exception as e:
            return {"error": f"Failed to get file info: {str(e)}"}
    
    def _search_files(self, query: str) -> Dict[str, Any]:
        """Search for files by name or content"""
        try:
            if not query:
                return {"error": "Search query is required"}
            
            matching_files = []
            
            # Search in uploads directory
            for filename in os.listdir(self.upload_dir):
                if query.lower() in filename.lower():
                    file_path = os.path.join(self.upload_dir, filename)
                    stat = os.stat(file_path)
                    matching_files.append({
                        "name": filename,
                        "path": file_path,
                        "size": stat.st_size,
                        "size_formatted": self._format_file_size(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": self._get_file_type(filename),
                        "match_reason": "filename"
                    })
            
            return {
                "success": True,
                "query": query,
                "matches": len(matching_files),
                "files": matching_files
            }
            
        except Exception as e:
            return {"error": f"Failed to search files: {str(e)}"}
    
    def _organize_file(self, filename: str, tag: str) -> Dict[str, Any]:
        """Organize file with tags or move to category"""
        try:
            if not filename:
                return {"error": "Filename is required"}
            
            file_path = os.path.join(self.upload_dir, filename)
            
            if not os.path.exists(file_path):
                return {"error": f"File {filename} not found"}
            
            # Create metadata file for organization
            metadata_path = os.path.join(self.data_dir, f"{filename}.meta")
            
            # Load existing metadata or create new
            metadata = {}
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            # Add tag
            if 'tags' not in metadata:
                metadata['tags'] = []
            
            if tag and tag not in metadata['tags']:
                metadata['tags'].append(tag)
            
            metadata['organized_at'] = datetime.now().isoformat()
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return {
                "success": True,
                "filename": filename,
                "tag": tag,
                "all_tags": metadata['tags'],
                "message": f"File {filename} organized with tag '{tag}'"
            }
            
        except Exception as e:
            return {"error": f"Failed to organize file: {str(e)}"}
    
    def _delete_file(self, filename: str) -> Dict[str, Any]:
        """Delete a file"""
        try:
            if not filename:
                return {"error": "Filename is required"}
            
            file_path = os.path.join(self.upload_dir, filename)
            
            if not os.path.exists(file_path):
                return {"error": f"File {filename} not found"}
            
            # Delete the file
            os.remove(file_path)
            
            # Also delete metadata if it exists
            metadata_path = os.path.join(self.data_dir, f"{filename}.meta")
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
            return {
                "success": True,
                "filename": filename,
                "message": f"File {filename} deleted successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to delete file: {str(e)}"}
    
    def _get_file_type(self, filename: str) -> str:
        """Get file type from extension"""
        extension = os.path.splitext(filename)[1].lower()
        
        type_mapping = {
            '.pdf': 'PDF Document',
            '.docx': 'Word Document',
            '.doc': 'Word Document',
            '.txt': 'Text File',
            '.md': 'Markdown File',
            '.csv': 'CSV File',
            '.xlsx': 'Excel Spreadsheet',
            '.xls': 'Excel Spreadsheet',
            '.json': 'JSON File',
            '.xml': 'XML File',
            '.html': 'HTML File',
            '.htm': 'HTML File',
            '.rtf': 'Rich Text Format',
            '.odt': 'OpenDocument Text',
            '.pptx': 'PowerPoint Presentation',
            '.ppt': 'PowerPoint Presentation',
            '.jpg': 'JPEG Image',
            '.jpeg': 'JPEG Image',
            '.png': 'PNG Image',
            '.gif': 'GIF Image',
            '.svg': 'SVG Image'
        }
        
        return type_mapping.get(extension, 'Unknown')
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"