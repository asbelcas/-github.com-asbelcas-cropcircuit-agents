#!/usr/bin/env python3
"""
AGENT CLIENT MODULE

Handles client communication and work delivery.

Current state: Manual (no API access to email/Slack/Discord)
Target state: Automated response to inquiries

For now, this tracks client interactions manually.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path

CLIENT_DB = "/home/asbelcas/rm-qpt/agent_central.db"

class ClientManager:
    """Manage client relationships and work"""
    
    def __init__(self):
        self.db_path = CLIENT_DB
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure client tables exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Clients
        c.execute('''CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            source TEXT,
            status TEXT DEFAULT 'lead',
            first_contact TEXT,
            last_contact TEXT,
            total_paid REAL DEFAULT 0,
            notes TEXT
        )''')
        
        # Work projects
        c.execute('''CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            client_id INTEGER,
            created_at TEXT,
            title TEXT,
            description TEXT,
            scope TEXT,
            agreed_price REAL,
            status TEXT DEFAULT 'inquiry',
            deadline TEXT,
            deliverables TEXT,
            completed_at TEXT
        )''')
        
        # Communications
        c.execute('''CREATE TABLE IF NOT EXISTS communications (
            id INTEGER PRIMARY KEY,
            client_id INTEGER,
            project_id INTEGER,
            timestamp TEXT,
            direction TEXT,
            channel TEXT,
            message TEXT,
            requires_response BOOLEAN DEFAULT 0,
            responded_at TEXT
        )''')
        
        conn.commit()
        conn.close()
    
    def add_client(self, name, email, source, notes=None):
        """Add new client"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        now = datetime.now().isoformat()
        c.execute('''INSERT INTO clients 
            (name, email, source, first_contact, last_contact, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (name, email, source, now, now, 'lead', notes))
        
        client_id = c.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Added client: {name} ({email})")
        return client_id
    
    def log_communication(self, client_id, direction, channel, message, 
                          project_id=None, requires_response=False):
        """
        Log a client communication
        
        direction: 'inbound' or 'outbound'
        channel: 'email', 'phone', 'dm', 'meeting'
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO communications
            (client_id, project_id, timestamp, direction, channel, message, requires_response)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (client_id, project_id, datetime.now().isoformat(),
             direction, channel, message, requires_response))
        
        # Update client's last_contact
        c.execute('''UPDATE clients SET last_contact = ? WHERE id = ?''',
            (datetime.now().isoformat(), client_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Logged {direction} {channel} with client {client_id}")
    
    def create_project(self, client_id, title, description, scope, 
                       agreed_price, deadline=None):
        """Create new project"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO projects
            (client_id, created_at, title, description, scope, agreed_price, deadline, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (client_id, datetime.now().isoformat(), title, description,
             scope, agreed_price, deadline, 'scoped'))
        
        project_id = c.lastrowid
        
        # Update client status
        c.execute('''UPDATE clients SET status = 'project' WHERE id = ?''',
            (client_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Created project: {title} (${agreed_price})")
        return project_id
    
    def complete_project(self, project_id, deliverables_path):
        """Mark project as complete"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''UPDATE projects 
            SET status = 'completed', 
                completed_at = ?,
                deliverables = ?
            WHERE id = ?''',
            (datetime.now().isoformat(), deliverables_path, project_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Marked project {project_id} as complete")
    
    def show_status(self):
        """Show client and project status"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Client counts
        c.execute('''SELECT status, COUNT(*) FROM clients GROUP BY status''')
        client_stats = dict(c.fetchall())
        
        # Project counts
        c.execute('''SELECT status, COUNT(*) FROM projects GROUP BY status''')
        project_stats = dict(c.fetchall())
        
        # Active projects
        c.execute('''SELECT p.id, c.name, p.title, p.status, p.agreed_price
            FROM projects p
            JOIN clients c ON p.client_id = c.id
            WHERE p.status NOT IN ('completed', 'cancelled')
            ORDER BY p.created_at DESC''')
        
        active = c.fetchall()
        
        # Pending responses
        c.execute('''SELECT c.name, m.message, m.timestamp
            FROM communications m
            JOIN clients c ON m.client_id = c.id
            WHERE m.requires_response = 1 AND m.responded_at IS NULL
            ORDER BY m.timestamp DESC''')
        
        pending = c.fetchall()
        
        conn.close()
        
        print("\n" + "="*70)
        print("👥 CLIENT DASHBOARD")
        print("="*70)
        
        print(f"\n   Clients:")
        for status, count in client_stats.items():
            print(f"      {status}: {count}")
        
        print(f"\n   Projects:")
        for status, count in project_stats.items():
            print(f"      {status}: {count}")
        
        print(f"\n   Active Projects:")
        for proj in active[:5]:
            print(f"      [{proj[3]}] {proj[1]} - {proj[2]} (${proj[4]})")
        
        if pending:
            print(f"\n   ⚠️  Pending Responses ({len(pending)}):")
            for p in pending[:3]:
                print(f"      {p[0]}: {p[1][:40]}...")
        else:
            print(f"\n   ✅ No pending responses")
        
        print("="*70)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Client management")
    parser.add_argument('action', choices=['add', 'log', 'project', 'complete', 'status'])
    parser.add_argument('--name', help='Client name')
    parser.add_argument('--email', help='Client email')
    parser.add_argument('--source', help='Lead source')
    parser.add_argument('--client-id', type=int, help='Client ID')
    parser.add_argument('--direction', help='inbound or outbound')
    parser.add_argument('--channel', help='email, phone, etc')
    parser.add_argument('--message', help='Message content')
    parser.add_argument('--title', help='Project title')
    parser.add_argument('--description', help='Project description')
    parser.add_argument('--price', type=float, help='Agreed price')
    parser.add_argument('--project-id', type=int, help='Project ID')
    parser.add_argument('--deliverables', help='Path to deliverables')
    
    args = parser.parse_args()
    
    manager = ClientManager()
    
    if args.action == 'add':
        if not args.name or not args.email:
            print("Error: --name and --email required")
            sys.exit(1)
        manager.add_client(args.name, args.email, args.source or 'manual', args.message)
    
    elif args.action == 'log':
        if not args.client_id or not args.direction or not args.channel or not args.message:
            print("Error: --client-id, --direction, --channel, --message required")
            sys.exit(1)
        manager.log_communication(
            args.client_id, args.direction, args.channel, args.message,
            args.project_id, requires_response=(args.direction == 'inbound')
        )
    
    elif args.action == 'project':
        if not args.client_id or not args.title or not args.price:
            print("Error: --client-id, --title, --price required")
            sys.exit(1)
        manager.create_project(
            args.client_id, args.title, 
            args.description or args.title,
            args.description or 'TBD',
            args.price
        )
    
    elif args.action == 'complete':
        if not args.project_id:
            print("Error: --project-id required")
            sys.exit(1)
        manager.complete_project(args.project_id, args.deliverables or 'N/A')
    
    elif args.action == 'status':
        manager.show_status()

if __name__ == "__main__":
    main()
