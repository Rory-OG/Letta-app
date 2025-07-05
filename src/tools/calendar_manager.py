"""
Calendar Manager Tool for Letta Agent
Handles appointments, events, reminders, and scheduling
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sqlite3

logger = logging.getLogger(__name__)

class CalendarManagerTool:
    """Tool for managing calendar events and scheduling"""
    
    def __init__(self):
        self.name = "calendar_manager"
        self.description = "Manage calendar events, appointments, and reminders"
        self.db_path = "./data/calendar.db"
        self.data_dir = "./data"
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize the calendar database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    location TEXT,
                    category TEXT DEFAULT 'general',
                    reminder_minutes INTEGER DEFAULT 15,
                    status TEXT DEFAULT 'scheduled',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    reminder_time TEXT NOT NULL,
                    message TEXT NOT NULL,
                    sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize calendar database: {e}")
    
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
                        "enum": ["create", "list", "search", "update", "delete", "today", "week", "remind"],
                        "description": "Action to perform on calendar"
                    },
                    "title": {
                        "type": "string",
                        "description": "Title of the event"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the event"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                    },
                    "location": {
                        "type": "string",
                        "description": "Location of the event"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category of the event (work, personal, health, etc.)"
                    },
                    "reminder_minutes": {
                        "type": "integer",
                        "description": "Minutes before event to send reminder"
                    },
                    "event_id": {
                        "type": "integer",
                        "description": "ID of the event to operate on"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for finding events"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date to view events for (YYYY-MM-DD format)"
                    }
                },
                "required": ["action"]
            }
        }
    
    def execute(self, action: str, title: str = None, description: str = None,
                start_time: str = None, end_time: str = None, location: str = None,
                category: str = "general", reminder_minutes: int = 15,
                event_id: int = None, query: str = None, date: str = None) -> Dict[str, Any]:
        """Execute calendar management action"""
        try:
            if action == "create":
                return self._create_event(title, description, start_time, end_time, 
                                        location, category, reminder_minutes)
            elif action == "list":
                return self._list_events()
            elif action == "search":
                return self._search_events(query)
            elif action == "update":
                return self._update_event(event_id, title, description, start_time, 
                                        end_time, location, category, reminder_minutes)
            elif action == "delete":
                return self._delete_event(event_id)
            elif action == "today":
                return self._get_today_events()
            elif action == "week":
                return self._get_week_events()
            elif action == "remind":
                return self._get_upcoming_reminders()
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error in calendar manager: {e}")
            return {"error": str(e)}
    
    def _create_event(self, title: str, description: str, start_time: str, end_time: str,
                     location: str, category: str, reminder_minutes: int) -> Dict[str, Any]:
        """Create a new calendar event"""
        try:
            if not title or not start_time:
                return {"error": "Title and start time are required"}
            
            # Validate datetime format
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                if end_time:
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    if end_dt <= start_dt:
                        return {"error": "End time must be after start time"}
                else:
                    end_dt = start_dt + timedelta(hours=1)  # Default 1 hour duration
                    end_time = end_dt.isoformat()
            except ValueError:
                return {"error": "Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO events (title, description, start_time, end_time, location, 
                                  category, reminder_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, start_time, end_time, location, category, reminder_minutes))
            
            event_id = cursor.lastrowid
            
            # Create reminder
            if reminder_minutes > 0:
                reminder_time = start_dt - timedelta(minutes=reminder_minutes)
                cursor.execute('''
                    INSERT INTO reminders (event_id, reminder_time, message)
                    VALUES (?, ?, ?)
                ''', (event_id, reminder_time.isoformat(), 
                     f"Reminder: {title} starts in {reminder_minutes} minutes"))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "event_id": event_id,
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "location": location,
                "category": category,
                "message": f"Event '{title}' scheduled successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to create event: {str(e)}"}
    
    def _list_events(self, limit: int = 20) -> Dict[str, Any]:
        """List upcoming events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            
            cursor.execute('''
                SELECT id, title, description, start_time, end_time, location, 
                       category, reminder_minutes, status
                FROM events
                WHERE start_time >= ?
                ORDER BY start_time ASC
                LIMIT ?
            ''', (current_time, limit))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "start_time": row[3],
                    "end_time": row[4],
                    "location": row[5],
                    "category": row[6],
                    "reminder_minutes": row[7],
                    "status": row[8]
                })
            
            conn.close()
            
            return {
                "success": True,
                "count": len(events),
                "events": events
            }
            
        except Exception as e:
            return {"error": f"Failed to list events: {str(e)}"}
    
    def _search_events(self, query: str) -> Dict[str, Any]:
        """Search events by title, description, or location"""
        try:
            if not query:
                return {"error": "Search query is required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, description, start_time, end_time, location, 
                       category, reminder_minutes, status
                FROM events
                WHERE title LIKE ? OR description LIKE ? OR location LIKE ?
                ORDER BY start_time ASC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "start_time": row[3],
                    "end_time": row[4],
                    "location": row[5],
                    "category": row[6],
                    "reminder_minutes": row[7],
                    "status": row[8]
                })
            
            conn.close()
            
            return {
                "success": True,
                "query": query,
                "count": len(events),
                "events": events
            }
            
        except Exception as e:
            return {"error": f"Failed to search events: {str(e)}"}
    
    def _update_event(self, event_id: int, title: str = None, description: str = None,
                     start_time: str = None, end_time: str = None, location: str = None,
                     category: str = None, reminder_minutes: int = None) -> Dict[str, Any]:
        """Update an existing event"""
        try:
            if not event_id:
                return {"error": "Event ID is required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current event
            cursor.execute('''
                SELECT title, description, start_time, end_time, location, 
                       category, reminder_minutes
                FROM events WHERE id = ?
            ''', (event_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"error": f"Event with ID {event_id} not found"}
            
            # Update fields
            new_title = title if title else row[0]
            new_description = description if description else row[1]
            new_start_time = start_time if start_time else row[2]
            new_end_time = end_time if end_time else row[3]
            new_location = location if location else row[4]
            new_category = category if category else row[5]
            new_reminder_minutes = reminder_minutes if reminder_minutes is not None else row[6]
            
            cursor.execute('''
                UPDATE events
                SET title = ?, description = ?, start_time = ?, end_time = ?, 
                    location = ?, category = ?, reminder_minutes = ?, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_title, new_description, new_start_time, new_end_time,
                  new_location, new_category, new_reminder_minutes, event_id))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "event_id": event_id,
                "title": new_title,
                "start_time": new_start_time,
                "end_time": new_end_time,
                "message": f"Event updated successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to update event: {str(e)}"}
    
    def _delete_event(self, event_id: int) -> Dict[str, Any]:
        """Delete an event"""
        try:
            if not event_id:
                return {"error": "Event ID is required"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if event exists
            cursor.execute('SELECT title FROM events WHERE id = ?', (event_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"error": f"Event with ID {event_id} not found"}
            
            title = row[0]
            
            # Delete reminders first
            cursor.execute('DELETE FROM reminders WHERE event_id = ?', (event_id,))
            
            # Delete the event
            cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "event_id": event_id,
                "title": title,
                "message": f"Event '{title}' deleted successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to delete event: {str(e)}"}
    
    def _get_today_events(self) -> Dict[str, Any]:
        """Get today's events"""
        try:
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time()).isoformat()
            end_of_day = datetime.combine(today, datetime.max.time()).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, description, start_time, end_time, location, category
                FROM events
                WHERE start_time >= ? AND start_time <= ?
                ORDER BY start_time ASC
            ''', (start_of_day, end_of_day))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "start_time": row[3],
                    "end_time": row[4],
                    "location": row[5],
                    "category": row[6]
                })
            
            conn.close()
            
            return {
                "success": True,
                "date": today.isoformat(),
                "count": len(events),
                "events": events
            }
            
        except Exception as e:
            return {"error": f"Failed to get today's events: {str(e)}"}
    
    def _get_week_events(self) -> Dict[str, Any]:
        """Get this week's events"""
        try:
            today = datetime.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            start_time = datetime.combine(start_of_week, datetime.min.time()).isoformat()
            end_time = datetime.combine(end_of_week, datetime.max.time()).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, description, start_time, end_time, location, category
                FROM events
                WHERE start_time >= ? AND start_time <= ?
                ORDER BY start_time ASC
            ''', (start_time, end_time))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "start_time": row[3],
                    "end_time": row[4],
                    "location": row[5],
                    "category": row[6]
                })
            
            conn.close()
            
            return {
                "success": True,
                "week_start": start_of_week.isoformat(),
                "week_end": end_of_week.isoformat(),
                "count": len(events),
                "events": events
            }
            
        except Exception as e:
            return {"error": f"Failed to get week's events: {str(e)}"}
    
    def _get_upcoming_reminders(self) -> Dict[str, Any]:
        """Get upcoming reminders"""
        try:
            current_time = datetime.now().isoformat()
            next_hour = (datetime.now() + timedelta(hours=1)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT r.id, r.reminder_time, r.message, e.title, e.start_time
                FROM reminders r
                JOIN events e ON r.event_id = e.id
                WHERE r.reminder_time >= ? AND r.reminder_time <= ? AND r.sent = FALSE
                ORDER BY r.reminder_time ASC
            ''', (current_time, next_hour))
            
            reminders = []
            for row in cursor.fetchall():
                reminders.append({
                    "id": row[0],
                    "reminder_time": row[1],
                    "message": row[2],
                    "event_title": row[3],
                    "event_start": row[4]
                })
            
            conn.close()
            
            return {
                "success": True,
                "count": len(reminders),
                "reminders": reminders
            }
            
        except Exception as e:
            return {"error": f"Failed to get reminders: {str(e)}"}