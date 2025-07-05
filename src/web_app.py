"""
Letta Knowledge Management & Personal Assistant Web Application
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import redis
from dotenv import load_dotenv

from agent_manager import AgentManager
from knowledge_manager import KnowledgeManager
from utils import allowed_file, get_file_type, format_timestamp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', './uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Initialize extensions
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Redis (optional)
try:
    redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    redis_client.ping()
    logger.info("Redis connected successfully")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

# Initialize managers
agent_manager = AgentManager()
knowledge_manager = KnowledgeManager()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('./data', exist_ok=True)
os.makedirs('./logs', exist_ok=True)

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        # Get agent status
        agent_status = agent_manager.get_agent_status()
        
        # Get recent conversations
        recent_conversations = agent_manager.get_recent_conversations(limit=5)
        
        # Get knowledge base stats
        knowledge_stats = knowledge_manager.get_stats()
        
        return render_template('index.html', 
                               agent_status=agent_status,
                               recent_conversations=recent_conversations,
                               knowledge_stats=knowledge_stats)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return render_template('index.html', 
                               agent_status={'status': 'error'},
                               recent_conversations=[],
                               knowledge_stats={})

@app.route('/chat')
def chat():
    """Chat interface page"""
    return render_template('chat.html')

@app.route('/knowledge')
def knowledge():
    """Knowledge management page"""
    try:
        # Get all notes and documents
        notes = knowledge_manager.get_all_notes()
        documents = knowledge_manager.get_all_documents()
        
        return render_template('knowledge.html', 
                               notes=notes, 
                               documents=documents)
    except Exception as e:
        logger.error(f"Error loading knowledge page: {e}")
        flash(f"Error loading knowledge base: {str(e)}", 'error')
        return render_template('knowledge.html', notes=[], documents=[])

@app.route('/agent')
def agent():
    """Agent management page"""
    try:
        agent_info = agent_manager.get_agent_info()
        memory_info = agent_manager.get_memory_info()
        
        return render_template('agent.html', 
                               agent_info=agent_info,
                               memory_info=memory_info)
    except Exception as e:
        logger.error(f"Error loading agent page: {e}")
        flash(f"Error loading agent information: {str(e)}", 'error')
        return render_template('agent.html', agent_info={}, memory_info={})

# API Routes
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Send message to agent"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Send message to agent
        response = agent_manager.send_message(message)
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in chat API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory', methods=['GET'])
def api_memory():
    """Get agent memory information"""
    try:
        memory_info = agent_manager.get_memory_info()
        return jsonify(memory_info)
    except Exception as e:
        logger.error(f"Error getting memory info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """Upload file to knowledge base"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process the uploaded file
            result = knowledge_manager.process_file(file_path, filename)
            
            return jsonify({
                'success': True,
                'message': 'File uploaded successfully',
                'file_info': result
            })
        else:
            return jsonify({'error': 'File type not allowed'}), 400
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes', methods=['GET', 'POST'])
def api_notes():
    """Get or create notes"""
    try:
        if request.method == 'GET':
            notes = knowledge_manager.get_all_notes()
            return jsonify(notes)
        
        elif request.method == 'POST':
            data = request.get_json()
            title = data.get('title', '')
            content = data.get('content', '')
            tags = data.get('tags', [])
            
            if not title or not content:
                return jsonify({'error': 'Title and content are required'}), 400
            
            note = knowledge_manager.create_note(title, content, tags)
            return jsonify({
                'success': True,
                'note': note
            })
    
    except Exception as e:
        logger.error(f"Error with notes API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """Search knowledge base"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        results = knowledge_manager.search(query)
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query
        })
    
    except Exception as e:
        logger.error(f"Error in search API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent/status', methods=['GET'])
def api_agent_status():
    """Get agent status"""
    try:
        status = agent_manager.get_agent_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent/reset', methods=['POST'])
def api_agent_reset():
    """Reset agent memory"""
    try:
        result = agent_manager.reset_agent()
        return jsonify({
            'success': True,
            'message': 'Agent reset successfully',
            'result': result
        })
    except Exception as e:
        logger.error(f"Error resetting agent: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('status', {'message': 'Connected to Letta Assistant'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle real-time chat message"""
    try:
        message = data.get('message', '')
        if message:
            # Send to agent
            response = agent_manager.send_message(message)
            
            # Emit response back to client
            emit('chat_response', {
                'message': message,
                'response': response,
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        emit('error', {'message': str(e)})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    try:
        # Initialize agent on startup
        agent_manager.initialize_agent()
        
        # Run the application
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise