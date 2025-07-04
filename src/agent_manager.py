"""
Agent Manager for Letta Knowledge Management System
Handles agent initialization, communication, and memory management
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import time

from letta_client import Letta
from letta_client.types import AgentState, CreateAgentRequest
from dotenv import load_dotenv

from tools.file_manager import FileManagerTool
from tools.note_taker import NoteTakerTool
from tools.calendar_manager import CalendarManagerTool
from tools.task_manager import TaskManagerTool
from tools.knowledge_search import KnowledgeSearchTool
from tools.web_search import WebSearchTool

load_dotenv()

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages Letta agent interactions and state"""
    
    def __init__(self):
        self.client = None
        self.agent_id = None
        self.agent_state = None
        self.conversation_history = []
        self.tools = {}
        self.initialize_client()
        
    def initialize_client(self):
        """Initialize the Letta client"""
        try:
            server_url = os.getenv('LETTA_SERVER_URL', 'http://localhost:8283')
            server_password = os.getenv('LETTA_SERVER_PASSWORD')
            
            if server_password:
                self.client = Letta(
                    base_url=server_url,
                    token=server_password
                )
            else:
                self.client = Letta(base_url=server_url)
                
            logger.info("Letta client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Letta client: {e}")
            raise
    
    def initialize_agent(self):
        """Initialize or load the knowledge management agent"""
        try:
            # Try to load existing agent
            agent_id_file = './data/agent_id.txt'
            
            if os.path.exists(agent_id_file):
                with open(agent_id_file, 'r') as f:
                    self.agent_id = f.read().strip()
                
                # Try to retrieve the agent
                try:
                    self.agent_state = self.client.agents.get(self.agent_id)
                    logger.info(f"Loaded existing agent: {self.agent_id}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load existing agent: {e}")
                    # Create new agent if existing one is not found
            
            # Create new agent
            self.agent_state = self.create_agent()
            self.agent_id = self.agent_state.id
            
            # Save agent ID
            with open(agent_id_file, 'w') as f:
                f.write(self.agent_id)
                
            logger.info(f"Created new agent: {self.agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    def create_agent(self) -> AgentState:
        """Create a new knowledge management agent"""
        try:
            # Initialize custom tools
            self.initialize_tools()
            
            # Get available tool names
            tool_names = list(self.tools.keys())
            
            # Create agent with custom memory and tools
            agent_state = self.client.agents.create(
                name="Knowledge Assistant",
                description="A personal knowledge management and assistant agent",
                model="openai/gpt-4",
                embedding="openai/text-embedding-3-small",
                memory_blocks=[
                    {
                        "label": "human",
                        "value": "The user is looking for a comprehensive knowledge management and personal assistant system. They want to organize information, take notes, manage tasks, and have intelligent conversations about their data."
                    },
                    {
                        "label": "persona",
                        "value": "I am a knowledgeable and helpful assistant specialized in knowledge management and personal productivity. I can help organize information, take notes, manage tasks and schedules, search through documents, and provide intelligent insights. I maintain context across conversations and learn from our interactions."
                    }
                ],
                tools=tool_names,
                system_prompt="""You are a sophisticated knowledge management and personal assistant. Your capabilities include:

1. **Knowledge Management**: Help organize, store, and retrieve information from documents and notes
2. **Note Taking**: Create, organize, and manage notes with tagging and categorization
3. **Task Management**: Track tasks, deadlines, and project progress
4. **Calendar Management**: Schedule appointments, set reminders, and manage time
5. **Document Processing**: Analyze and extract information from various file types
6. **Search & Retrieval**: Find relevant information across all stored data
7. **Web Research**: Search the internet for current information when needed

Always be helpful, accurate, and maintain context across conversations. Use your tools effectively to provide comprehensive assistance. When users ask questions, consider what information you might need from your knowledge base and search accordingly.

Remember to:
- Use appropriate tools for each task
- Maintain organized records of information
- Provide clear, actionable responses
- Learn from interactions to improve future assistance
- Respect privacy and security of user data"""
            )
            
            return agent_state
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise
    
    def initialize_tools(self):
        """Initialize all custom tools"""
        try:
            self.tools = {
                'file_manager': FileManagerTool(),
                'note_taker': NoteTakerTool(),
                'calendar_manager': CalendarManagerTool(),
                'task_manager': TaskManagerTool(),
                'knowledge_search': KnowledgeSearchTool(),
                'web_search': WebSearchTool()
            }
            
            # Register tools with Letta client
            for tool_name, tool_instance in self.tools.items():
                try:
                    self.client.tools.create(
                        name=tool_name,
                        description=tool_instance.description,
                        function=tool_instance.get_function_schema()
                    )
                    logger.info(f"Registered tool: {tool_name}")
                except Exception as e:
                    logger.warning(f"Failed to register tool {tool_name}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to initialize tools: {e}")
            raise
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """Send a message to the agent and get response"""
        try:
            if not self.agent_id:
                raise ValueError("Agent not initialized")
            
            # Send message to agent
            response = self.client.agents.messages.create(
                agent_id=self.agent_id,
                messages=[
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            )
            
            # Process response
            result = {
                'messages': [],
                'tool_calls': [],
                'usage': response.usage if hasattr(response, 'usage') else {}
            }
            
            for msg in response.messages:
                if msg.message_type == 'assistant_message':
                    result['messages'].append({
                        'role': 'assistant',
                        'content': msg.content,
                        'timestamp': msg.date
                    })
                elif msg.message_type == 'tool_call':
                    result['tool_calls'].append({
                        'tool': msg.tool_name,
                        'arguments': msg.arguments,
                        'result': msg.result
                    })
            
            # Store in conversation history
            self.conversation_history.append({
                'user_message': message,
                'agent_response': result,
                'timestamp': datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending message to agent: {e}")
            raise
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        try:
            if not self.agent_id:
                return {'status': 'not_initialized'}
            
            # Get agent information
            agent_info = self.client.agents.get(self.agent_id)
            
            return {
                'status': 'active',
                'agent_id': self.agent_id,
                'name': agent_info.name,
                'model': agent_info.model,
                'created_at': agent_info.created_at,
                'conversation_count': len(self.conversation_history),
                'tools_available': len(self.tools)
            }
            
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get detailed agent information"""
        try:
            if not self.agent_id:
                return {}
            
            agent_info = self.client.agents.get(self.agent_id)
            
            return {
                'id': agent_info.id,
                'name': agent_info.name,
                'description': agent_info.description,
                'model': agent_info.model,
                'embedding': agent_info.embedding,
                'created_at': agent_info.created_at,
                'tools': list(self.tools.keys()),
                'conversation_count': len(self.conversation_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting agent info: {e}")
            return {}
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get agent memory information"""
        try:
            if not self.agent_id:
                return {}
            
            # Get memory blocks
            memory_blocks = self.client.agents.memory.get(self.agent_id)
            
            return {
                'memory_blocks': memory_blocks,
                'conversation_history_size': len(self.conversation_history),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return {}
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        try:
            recent = self.conversation_history[-limit:] if len(self.conversation_history) > limit else self.conversation_history
            return recent
            
        except Exception as e:
            logger.error(f"Error getting recent conversations: {e}")
            return []
    
    def reset_agent(self) -> Dict[str, Any]:
        """Reset agent memory and state"""
        try:
            if not self.agent_id:
                return {'success': False, 'message': 'Agent not initialized'}
            
            # Clear conversation history
            self.conversation_history = []
            
            # Reset agent memory (this depends on Letta's API)
            # For now, we'll recreate the agent
            self.agent_state = self.create_agent()
            self.agent_id = self.agent_state.id
            
            # Save new agent ID
            with open('./data/agent_id.txt', 'w') as f:
                f.write(self.agent_id)
            
            return {
                'success': True,
                'message': 'Agent reset successfully',
                'new_agent_id': self.agent_id
            }
            
        except Exception as e:
            logger.error(f"Error resetting agent: {e}")
            return {'success': False, 'message': str(e)}
    
    def save_conversation_history(self):
        """Save conversation history to file"""
        try:
            history_file = './data/conversation_history.json'
            with open(history_file, 'w') as f:
                json.dump(self.conversation_history, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
    
    def load_conversation_history(self):
        """Load conversation history from file"""
        try:
            history_file = './data/conversation_history.json'
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.conversation_history = json.load(f)
                    
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
            self.conversation_history = []