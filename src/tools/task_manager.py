"""
Task Manager Tool for Letta Agent
Handles todo items, projects, task tracking, and productivity
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sqlite3

logger = logging.getLogger(__name__)

class TaskManagerTool:
    """Tool for managing tasks, todos, and projects"""
    
    def __init__(self):
        self.name = "task_manager"
        self.description = "Manage tasks, todo items, projects, and track productivity"
        self.db_path = "./data/tasks.db"
        self.data_dir = "./data"
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize the tasks database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    deadline TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    project_id INTEGER,
                    priority INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    tags TEXT DEFAULT '[]',
                    due_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    estimated_hours REAL DEFAULT 0,
                    actual_hours REAL DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS time_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_minutes INTEGER,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize tasks database: {e}")
    
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
                        "enum": ["create", "list", "search", "update", "delete", "complete", "project", "track", "report"],
                        "description": "Action to perform on tasks"
                    },
                    "title": {
                        "type": "string",
                        "description": "Title of the task"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the task"
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project"
                    },
                    "project_id": {
                        "type": "integer",
                        "description": "ID of the project"
                    },
                    "task_id": {
                        "type": "integer",
                        "description": "ID of the task to operate on"
                    },
                    "priority": {
                        "type": "integer",
                        "description": "Priority level (0-5, higher is more important)"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed", "blocked", "cancelled"],
                        "description": "Status of the task"
                    },
                    "tags": {
                        "type": "string",
                        "description": "Comma-separated tags for the task"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in ISO format (YYYY-MM-DD)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for finding tasks"
                    },
                    "estimated_hours": {
                        "type": "number",
                        "description": "Estimated hours to complete the task"
                    },
                    "hours": {
                        "type": "number",
                        "description": "Hours to log for time tracking"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["action"]
            }
        }
    
    def execute(self, action: str, title: str = None, description: str = None,
                project_name: str = None, project_id: int = None, task_id: int = None,
                priority: int = 0, status: str = "pending", tags: str = None,
                due_date: str = None, query: str = None, estimated_hours: float = 0,
                hours: float = None, limit: int = 20) -> Dict[str, Any]:
        """Execute task management action"""
        try:
            if action == "create":
                return self._create_task(title, description, project_id, priority, tags, due_date, estimated_hours)
            elif action == "list":
                return self._list_tasks(limit, status)
            elif action == "search":
                return self._search_tasks(query, limit)
            elif action == "update":
                return self._update_task(task_id, title, description, project_id, priority, status, tags, due_date, estimated_hours)
            elif action == "delete":
                return self._delete_task(task_id)
            elif action == "complete":
                return self._complete_task(task_id)
            elif action == "project":
                return self._manage_project(project_name, description)
            elif action == "track":
                return self._track_time(task_id, hours, description)
            elif action == "report":
                return self._generate_report()
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error in task manager: {e}")
            return {"error": str(e)}
    
    def _create_task(self, title: str, description: str, project_id: int, priority: int, 
                     tags: str, due_date: str, estimated_hours: float) -> Dict[str, Any]:
        """Create a new task"""
        try:
            if not title:
                return {"error": "Task title is required"}
            
            # Parse tags
            tag_list = self._parse_tags(tags) if tags else []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tasks (title, description, project_id, priority, tags, 
                                 due_date, estimated_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, project_id, priority, json.dumps(tag_list), 
                  due_date, estimated_hours))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "task_id": task_id,
                "title": title,
                "description": description,
                "priority": priority,
                "tags": tag_list,
                "due_date": due_date,
                "estimated_hours": estimated_hours,
                "message": f"Task '{title}' created successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to create task: {str(e)}"}
    
    def _list_tasks(self, limit: int = 20, status_filter: str = None) -> Dict[str, Any]:
        """List tasks with optional status filter"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status_filter and status_filter != "pending":
                cursor.execute('''
                    SELECT t.id, t.title, t.description, t.project_id, p.name as project_name,
                           t.priority, t.status, t.tags, t.due_date, t.created_at, 
                           t.estimated_hours, t.actual_hours
                    FROM tasks t
                    LEFT JOIN projects p ON t.project_id = p.id
                    WHERE t.status = ?
                    ORDER BY t.priority DESC, t.created_at DESC
                    LIMIT ?
                ''', (status_filter, limit))
            else:
                cursor.execute('''
                    SELECT t.id, t.title, t.description, t.project_id, p.name as project_name,
                           t.priority, t.status, t.tags, t.due_date, t.created_at, 
                           t.estimated_hours, t.actual_hours
                    FROM tasks t
                    LEFT JOIN projects p ON t.project_id = p.id
                    WHERE t.status != 'completed'
                    ORDER BY t.priority DESC, t.created_at DESC
                    LIMIT ?
                ''', (limit,))
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "project_id": row[3],
                    "project_name": row[4],
                    "priority": row[5],
                    "status": row[6],
                    "tags": json.loads(row[7]) if row[7] else [],
                    "due_date": row[8],
                    "created_at": row[9],
                    "estimated_hours": row[10],
                    "actual_hours": row[11]
                })
            
            conn.close()
            
            return {
                "success": True,
                "count": len(tasks),
                "status_filter": status_filter,
                "tasks": tasks
            }
            
        except Exception as e:
            return {"error": f"Failed to list tasks: {str(e)}"}
    
    def _search_tasks(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search tasks by title, description, or tags"""
        try:
            if not query:
                return {"error": "Search query is required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT t.id, t.title, t.description, t.project_id, p.name as project_name,
                       t.priority, t.status, t.tags, t.due_date, t.created_at, 
                       t.estimated_hours, t.actual_hours
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE t.title LIKE ? OR t.description LIKE ? OR t.tags LIKE ?
                ORDER BY t.priority DESC, t.created_at DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "project_id": row[3],
                    "project_name": row[4],
                    "priority": row[5],
                    "status": row[6],
                    "tags": json.loads(row[7]) if row[7] else [],
                    "due_date": row[8],
                    "created_at": row[9],
                    "estimated_hours": row[10],
                    "actual_hours": row[11]
                })
            
            conn.close()
            
            return {
                "success": True,
                "query": query,
                "count": len(tasks),
                "tasks": tasks
            }
            
        except Exception as e:
            return {"error": f"Failed to search tasks: {str(e)}"}
    
    def _update_task(self, task_id: int, title: str = None, description: str = None,
                     project_id: int = None, priority: int = None, status: str = None,
                     tags: str = None, due_date: str = None, estimated_hours: float = None) -> Dict[str, Any]:
        """Update an existing task"""
        try:
            if not task_id:
                return {"error": "Task ID is required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current task
            cursor.execute('''
                SELECT title, description, project_id, priority, status, tags, 
                       due_date, estimated_hours
                FROM tasks WHERE id = ?
            ''', (task_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"error": f"Task with ID {task_id} not found"}
            
            # Update fields
            new_title = title if title else row[0]
            new_description = description if description else row[1]
            new_project_id = project_id if project_id is not None else row[2]
            new_priority = priority if priority is not None else row[3]
            new_status = status if status else row[4]
            new_tags = json.dumps(self._parse_tags(tags)) if tags else row[5]
            new_due_date = due_date if due_date else row[6]
            new_estimated_hours = estimated_hours if estimated_hours is not None else row[7]
            
            cursor.execute('''
                UPDATE tasks
                SET title = ?, description = ?, project_id = ?, priority = ?, 
                    status = ?, tags = ?, due_date = ?, estimated_hours = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_title, new_description, new_project_id, new_priority,
                  new_status, new_tags, new_due_date, new_estimated_hours, task_id))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "task_id": task_id,
                "title": new_title,
                "status": new_status,
                "priority": new_priority,
                "message": f"Task updated successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to update task: {str(e)}"}
    
    def _delete_task(self, task_id: int) -> Dict[str, Any]:
        """Delete a task"""
        try:
            if not task_id:
                return {"error": "Task ID is required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if task exists
            cursor.execute('SELECT title FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"error": f"Task with ID {task_id} not found"}
            
            title = row[0]
            
            # Delete time logs first
            cursor.execute('DELETE FROM time_logs WHERE task_id = ?', (task_id,))
            
            # Delete the task
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "task_id": task_id,
                "title": title,
                "message": f"Task '{title}' deleted successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to delete task: {str(e)}"}
    
    def _complete_task(self, task_id: int) -> Dict[str, Any]:
        """Mark a task as completed"""
        try:
            if not task_id:
                return {"error": "Task ID is required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if task exists
            cursor.execute('SELECT title, status FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"error": f"Task with ID {task_id} not found"}
            
            title, current_status = row
            
            if current_status == 'completed':
                return {"message": f"Task '{title}' is already completed"}
            
            # Mark as completed
            cursor.execute('''
                UPDATE tasks
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (task_id,))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "task_id": task_id,
                "title": title,
                "message": f"Task '{title}' marked as completed"
            }
            
        except Exception as e:
            return {"error": f"Failed to complete task: {str(e)}"}
    
    def _manage_project(self, name: str, description: str = None) -> Dict[str, Any]:
        """Create or list projects"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if name:
                # Create new project
                cursor.execute('''
                    INSERT INTO projects (name, description)
                    VALUES (?, ?)
                ''', (name, description))
                
                project_id = cursor.lastrowid
                conn.commit()
                
                result = {
                    "success": True,
                    "project_id": project_id,
                    "name": name,
                    "description": description,
                    "message": f"Project '{name}' created successfully"
                }
            else:
                # List all projects
                cursor.execute('''
                    SELECT id, name, description, status, created_at,
                           (SELECT COUNT(*) FROM tasks WHERE project_id = p.id) as task_count
                    FROM projects p
                    ORDER BY created_at DESC
                ''')
                
                projects = []
                for row in cursor.fetchall():
                    projects.append({
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "status": row[3],
                        "created_at": row[4],
                        "task_count": row[5]
                    })
                
                result = {
                    "success": True,
                    "count": len(projects),
                    "projects": projects
                }
            
            conn.close()
            return result
            
        except Exception as e:
            return {"error": f"Failed to manage project: {str(e)}"}
    
    def _track_time(self, task_id: int, hours: float, description: str = None) -> Dict[str, Any]:
        """Track time spent on a task"""
        try:
            if not task_id or not hours:
                return {"error": "Task ID and hours are required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if task exists
            cursor.execute('SELECT title, actual_hours FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"error": f"Task with ID {task_id} not found"}
            
            title, current_hours = row
            
            # Log time
            start_time = datetime.now().isoformat()
            duration_minutes = int(hours * 60)
            
            cursor.execute('''
                INSERT INTO time_logs (task_id, start_time, duration_minutes, description)
                VALUES (?, ?, ?, ?)
            ''', (task_id, start_time, duration_minutes, description))
            
            # Update task total hours
            new_total_hours = (current_hours or 0) + hours
            cursor.execute('''
                UPDATE tasks SET actual_hours = ? WHERE id = ?
            ''', (new_total_hours, task_id))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "task_id": task_id,
                "title": title,
                "hours_logged": hours,
                "total_hours": new_total_hours,
                "description": description,
                "message": f"Logged {hours} hours for task '{title}'"
            }
            
        except Exception as e:
            return {"error": f"Failed to track time: {str(e)}"}
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate productivity report"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Task status summary
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM tasks
                GROUP BY status
            ''')
            status_summary = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Priority breakdown
            cursor.execute('''
                SELECT priority, COUNT(*) as count
                FROM tasks
                WHERE status != 'completed'
                GROUP BY priority
                ORDER BY priority DESC
            ''')
            priority_breakdown = {f"Priority {row[0]}": row[1] for row in cursor.fetchall()}
            
            # Overdue tasks
            today = datetime.now().date().isoformat()
            cursor.execute('''
                SELECT COUNT(*) FROM tasks
                WHERE due_date < ? AND status != 'completed'
            ''', (today,))
            overdue_count = cursor.fetchone()[0]
            
            # Time tracking summary
            cursor.execute('''
                SELECT SUM(actual_hours), SUM(estimated_hours)
                FROM tasks
                WHERE status = 'completed'
            ''')
            time_row = cursor.fetchone()
            total_actual = time_row[0] or 0
            total_estimated = time_row[1] or 0
            
            # Recent completions
            cursor.execute('''
                SELECT title, completed_at
                FROM tasks
                WHERE status = 'completed'
                ORDER BY completed_at DESC
                LIMIT 5
            ''')
            recent_completions = [{"title": row[0], "completed_at": row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                "success": True,
                "report": {
                    "status_summary": status_summary,
                    "priority_breakdown": priority_breakdown,
                    "overdue_tasks": overdue_count,
                    "time_tracking": {
                        "total_actual_hours": total_actual,
                        "total_estimated_hours": total_estimated,
                        "estimation_accuracy": (total_actual / total_estimated * 100) if total_estimated > 0 else 0
                    },
                    "recent_completions": recent_completions
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to generate report: {str(e)}"}
    
    def _parse_tags(self, tags_str: str) -> List[str]:
        """Parse comma-separated tags string"""
        if not tags_str:
            return []
        
        tags = [tag.strip().lower() for tag in tags_str.split(',')]
        return [tag for tag in tags if tag]  # Remove empty tags