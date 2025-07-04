# Letta Knowledge Management & Personal Assistant

A comprehensive knowledge management and personal assistant application built with the Letta framework, featuring stateful AI agents with persistent memory.

## Features

- **Persistent Memory**: Agents remember conversations and information across sessions
- **Knowledge Management**: Store, organize, and retrieve notes, documents, and information
- **Personal Assistant**: Schedule management, task tracking, and reminders
- **File Management**: Upload, organize, and search through documents
- **Custom Tools**: Specialized tools for productivity and knowledge work
- **Web Interface**: User-friendly web interface for interacting with your assistant
- **Self-Hosted**: Complete control over your data and privacy

## Architecture

This application uses:
- **Letta Server**: Self-hosted using Docker for agent management
- **Custom Tools**: Python-based tools for knowledge management and productivity
- **Web Interface**: Flask-based web application for user interaction
- **PostgreSQL**: Database for persistent storage
- **File Storage**: Local file system for document management

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- OpenAI API key (or other LLM provider)

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd letta-knowledge-assistant
```

2. Copy the environment file and configure your API keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Start the application:
```bash
docker-compose up -d
```

4. Access the web interface at `http://localhost:5000`

### Environment Variables

Create a `.env` file with the following variables:

```env
# LLM Provider API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Letta Server Configuration
LETTA_SERVER_PASSWORD=your_secure_password
SECURE=true

# Database Configuration
POSTGRES_DB=letta_db
POSTGRES_USER=letta_user
POSTGRES_PASSWORD=letta_password

# Application Configuration
FLASK_SECRET_KEY=your_flask_secret_key
```

## Usage

### Knowledge Management

1. **Add Documents**: Upload PDFs, text files, or create notes through the web interface
2. **Query Knowledge**: Ask questions about your documents and notes
3. **Organize Information**: Tag and categorize your knowledge base
4. **Search**: Find information quickly using natural language queries

### Personal Assistant

1. **Schedule Management**: Add, view, and manage appointments
2. **Task Tracking**: Create and track todo items
3. **Reminders**: Set reminders for important events
4. **Note Taking**: Quick note capture and organization

### Agent Interaction

- **Chat Interface**: Natural conversation with your assistant
- **Memory Inspection**: View what your agent remembers
- **Tool Usage**: See when and how tools are used
- **Context Management**: Understand agent reasoning

## Custom Tools

The application includes several custom tools:

- **File Manager**: Upload, organize, and search files
- **Note Taker**: Create and manage notes with tagging
- **Calendar**: Schedule and reminder management
- **Task Manager**: Todo list and task tracking
- **Knowledge Search**: Semantic search across your knowledge base
- **Web Search**: Search the web for current information

## Development

### Adding Custom Tools

1. Create a new tool in `src/tools/`
2. Register the tool in `src/agent_manager.py`
3. Restart the application

### Extending the Web Interface

1. Add new routes in `src/web_app.py`
2. Create templates in `templates/`
3. Add static files in `static/`

## API Reference

The application exposes a REST API for programmatic access:

- `POST /api/chat` - Send messages to the agent
- `GET /api/memory` - View agent memory
- `POST /api/upload` - Upload documents
- `GET /api/notes` - List notes
- `POST /api/notes` - Create notes

## Docker Services

- **letta-server**: Main Letta server container
- **postgres**: PostgreSQL database
- **web-app**: Flask web application
- **nginx**: Reverse proxy (optional)

## Security

- All API keys are stored in environment variables
- Database credentials are configurable
- Optional password protection for the Letta server
- File uploads are validated and secured

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check the troubleshooting section below
- Join the Letta Discord community
- Open an issue on GitHub

## Troubleshooting

### Common Issues

1. **Container won't start**: Check Docker logs and ensure ports are available
2. **Database connection errors**: Verify PostgreSQL container is running
3. **API key errors**: Ensure environment variables are properly set
4. **File upload issues**: Check file permissions and storage space

### Logs

View application logs:
```bash
docker-compose logs -f letta-server
docker-compose logs -f web-app
```

### Reset Database

To reset the database:
```bash
docker-compose down -v
docker-compose up -d
```
