"""
Utility functions for the Letta Knowledge Management System
"""

import os
import re
import hashlib
import mimetypes
from datetime import datetime
from typing import List, Dict, Any, Optional
import magic

def allowed_file(filename: str) -> bool:
    """Check if file type is allowed for upload"""
    ALLOWED_EXTENSIONS = {
        'txt', 'md', 'pdf', 'docx', 'doc', 'csv', 'xlsx', 'xls', 
        'json', 'xml', 'html', 'htm', 'rtf', 'odt', 'pptx', 'ppt'
    }
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename: str) -> str:
    """Get file type from filename"""
    try:
        mime_type, _ = mimetypes.guess_type(filename)
        extension = os.path.splitext(filename)[1].lower()
        
        # Common file type mappings
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
            '.ppt': 'PowerPoint Presentation'
        }
        
        return type_mapping.get(extension, 'Unknown File Type')
        
    except Exception:
        return 'Unknown File Type'

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return timestamp

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file"""
    try:
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return ""

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)]', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text using simple frequency analysis"""
    if not text:
        return []
    
    # Convert to lowercase and split into words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter out common stop words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have',
        'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might', 'can',
        'this', 'that', 'these', 'those', 'a', 'an', 'you', 'i', 'we', 'they',
        'he', 'she', 'it', 'his', 'her', 'our', 'their', 'my', 'your'
    }
    
    # Count word frequencies
    word_count = {}
    for word in words:
        if word not in stop_words and len(word) > 2:
            word_count[word] = word_count.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:max_keywords]]

def validate_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "untitled"
    
    return filename

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def parse_tags(tags_input: str) -> List[str]:
    """Parse tag string into list of tags"""
    if not tags_input:
        return []
    
    # Split by comma and clean each tag
    tags = [tag.strip().lower() for tag in tags_input.split(',')]
    
    # Remove empty tags and duplicates
    tags = list(set(tag for tag in tags if tag))
    
    return tags

def format_tags(tags: List[str]) -> str:
    """Format tags list for display"""
    if not tags:
        return ""
    
    return ", ".join(tags)

def is_valid_url(url: str) -> bool:
    """Check if string is a valid URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get comprehensive file information"""
    try:
        stat = os.stat(file_path)
        
        return {
            'name': os.path.basename(file_path),
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'type': get_file_type(file_path),
            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'hash': calculate_file_hash(file_path),
            'extension': os.path.splitext(file_path)[1].lower()
        }
    except Exception as e:
        return {
            'name': os.path.basename(file_path),
            'error': str(e)
        }

def create_directory_if_not_exists(directory: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception:
        return False

def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Safely load JSON string with default fallback"""
    try:
        import json
        return json.loads(json_string)
    except Exception:
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely dump object to JSON string with default fallback"""
    try:
        import json
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return default

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text"""
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def get_text_statistics(text: str) -> Dict[str, int]:
    """Get basic text statistics"""
    if not text:
        return {
            'characters': 0,
            'words': 0,
            'lines': 0,
            'paragraphs': 0
        }
    
    # Count characters
    char_count = len(text)
    
    # Count words
    word_count = len(re.findall(r'\b\w+\b', text))
    
    # Count lines
    line_count = len(text.split('\n'))
    
    # Count paragraphs (empty lines separate paragraphs)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    paragraph_count = len(paragraphs)
    
    return {
        'characters': char_count,
        'words': word_count,
        'lines': line_count,
        'paragraphs': paragraph_count
    }

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def generate_unique_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix"""
    import uuid
    unique_id = str(uuid.uuid4())
    
    if prefix:
        return f"{prefix}_{unique_id}"
    
    return unique_id

def is_text_file(file_path: str) -> bool:
    """Check if file is a text file"""
    try:
        # Try to detect file type using python-magic
        file_type = magic.from_file(file_path, mime=True)
        return file_type.startswith('text/')
    except Exception:
        # Fallback to extension-based detection
        text_extensions = {'.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm', '.rtf'}
        extension = os.path.splitext(file_path)[1].lower()
        return extension in text_extensions