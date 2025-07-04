# Letta Knowledge Management & Personal Assistant - Setup Guide

I've created a comprehensive knowledge management and personal assistant application using the Letta framework. Here's what has been built and how to use it.

## 🎯 What Was Created

### Core Application
- **Full-stack web application** with Flask backend and modern Bootstrap frontend
- **Letta agent integration** with persistent memory and custom tools
- **Docker-based deployment** for easy setup and scalability
- **Knowledge management system** with document processing and semantic search
- **Personal assistant features** including calendar, tasks, and notes

### Custom Tools for the Letta Agent
1. **File Manager** - Upload, organize, and search files
2. **Note Taker** - Create and manage notes with tagging
3. **Calendar Manager** - Schedule events and manage appointments
4. **Task Manager** - Track todos, projects, and productivity
5. **Knowledge Search** - Semantic search across all content
6. **Web Search** - Search the internet for current information

### Features
- ✅ **Persistent Memory** - Agent remembers across sessions
- ✅ **Document Processing** - PDF, DOCX, CSV, Excel support
- ✅ **Semantic Search** - AI-powered content discovery
- ✅ **Real-time Chat** - WebSocket-based conversations
- ✅ **Knowledge Base** - Organized storage and retrieval
- ✅ **Task Management** - Full productivity suite
- ✅ **Calendar Integration** - Event and reminder management
- ✅ **Web Interface** - Beautiful, responsive UI
- ✅ **RESTful API** - Programmatic access
- ✅ **Docker Deployment** - Easy setup and scaling

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key (or other LLM provider)
- 4GB+ RAM recommended

### Installation

1. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start the Application**
   ```bash
   ./start.sh
   ```

3. **Access the Interface**
   - Web App: http://localhost:5000
   - Letta Server: http://localhost:8283
   - ADE (optional): https://app.letta.com

## 📁 Project Structure

```
letta-knowledge-assistant/
├── src/                          # Application source code
│   ├── web_app.py               # Main Flask application
│   ├── agent_manager.py         # Letta agent management
│   ├── knowledge_manager.py     # Knowledge base operations
│   ├── utils.py                 # Utility functions
│   └── tools/                   # Custom Letta tools
│       ├── file_manager.py      # File operations
│       ├── note_taker.py        # Note management
│       ├── calendar_manager.py  # Calendar & events
│       ├── task_manager.py      # Task tracking
│       ├── knowledge_search.py  # Knowledge search
│       └── web_search.py        # Web search
├── templates/                    # HTML templates
│   ├── base.html               # Base template
│   └── index.html              # Dashboard
├── static/                      # Static assets (CSS, JS, images)
├── uploads/                     # File uploads
├── data/                        # Database files
├── docker-compose.yml          # Docker services
├── Dockerfile.web              # Web app container
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── start.sh                   # Startup script
└── README.md                  # Documentation
```

## 🛠 Configuration

### Environment Variables (.env)
```env
# Required: At least one LLM API key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...

# Letta Configuration
LETTA_SERVER_PASSWORD=your_secure_password
SECURE=true

# Database
POSTGRES_DB=letta_db
POSTGRES_USER=letta_user
POSTGRES_PASSWORD=secure_password

# Application
FLASK_SECRET_KEY=your_secret_key
```

### Docker Services
- **letta-server**: Main Letta server with agent runtime
- **postgres**: PostgreSQL database for persistence
- **web-app**: Flask web application
- **redis**: Caching and session storage

## 🎮 Usage Guide

### 1. Dashboard
- View system status and statistics
- Quick actions for common tasks
- Recent conversation history
- Getting started guide

### 2. Chat Interface
- Natural language conversation with your assistant
- Real-time responses with WebSocket
- Tool usage visibility
- Conversation history

### 3. Knowledge Management
- Upload documents (PDF, DOCX, CSV, Excel)
- Create and organize notes
- Tag-based organization
- Semantic search across all content

### 4. Agent Management
- Monitor agent status and memory
- View tool usage and performance
- Reset or reconfigure agent
- Inspect conversation history

### API Endpoints
- `POST /api/chat` - Send messages to agent
- `POST /api/upload` - Upload documents
- `POST /api/notes` - Create notes
- `POST /api/search` - Search knowledge base
- `GET /api/agent/status` - Get agent status

## 🔧 Advanced Usage

### Custom Tools
Add new tools by:
1. Create tool class in `src/tools/`
2. Implement `get_function_schema()` and `execute()`
3. Register in `agent_manager.py`

### Database Access
Direct database access available:
- Knowledge: `./data/knowledge.db`
- Notes: `./data/notes.db`
- Tasks: `./data/tasks.db`
- Calendar: `./data/calendar.db`

### Scaling
For production deployment:
- Use external PostgreSQL database
- Add nginx reverse proxy
- Configure SSL certificates
- Set up monitoring and logging

## 🔍 Troubleshooting

### Common Issues
1. **Services won't start**: Check Docker and ports
2. **Agent not responding**: Verify API keys in .env
3. **Upload failures**: Check file permissions
4. **Database errors**: Ensure PostgreSQL is running

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f letta-server
docker-compose logs -f web-app
```

### Reset Data
```bash
# Reset all data and restart
docker-compose down -v
docker-compose up -d
```

## 🚀 Next Steps

### Immediate Use
1. Upload your first document
2. Create some notes with tags
3. Start a conversation with the agent
4. Try searching your knowledge base

### Customization
1. Add custom tools for your workflow
2. Modify the UI to match your preferences
3. Configure additional LLM providers
4. Set up automated backups

### Integration
1. Connect to external APIs
2. Set up webhooks for notifications
3. Integrate with existing tools
4. Build mobile app using the API

## 📚 Resources

- [Letta Documentation](https://docs.letta.com)
- [Letta GitHub](https://github.com/cpacker/MemGPT)
- [Letta Discord](https://discord.gg/letta)
- [Agent Development Environment](https://app.letta.com)

## 🤝 Support

For issues with this implementation:
1. Check the troubleshooting section
2. Review Docker logs
3. Verify environment configuration
4. Consult Letta documentation

The application is designed to be self-contained and easy to modify. All source code is well-documented and follows best practices for maintainability and extensibility.