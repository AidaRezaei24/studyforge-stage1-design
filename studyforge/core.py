"""Shared application commands, persistence, learning policies, and session orchestration."""
from collections import defaultdict
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone as tz
import json
from pathlib import Path
import sqlite3
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .model import OpenAIModelAdapter


def uid():
    return uuid.uuid4().hex


def now():
    return datetime.now(tz.utc).isoformat()


class SQLiteRepository:
    """JSON aggregates in SQLite, with nested transaction support for use cases."""
    def __init__(self, path='studyforge.db'):
        if str(path) != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(path), check_same_thread=False)
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, course TEXT NOT NULL, data TEXT NOT NULL)')
        self.connection.execute('CREATE INDEX IF NOT EXISTS scope ON records(kind,course)')
        self.connection.commit()
        self.depth = 0

    @contextmanager
    def transaction(self):
        self.depth += 1
        try:
            yield
            if self.depth == 1:
                self.connection.commit()
        except Exception:
            if self.depth == 1:
                self.connection.rollback()
            raise
        finally:
            self.depth -= 1

    def save(self, kind, course, data):
        record = dict(data)
        record.setdefault('id', uid())
        record['course'] = course
        record.setdefault('created_at', now())
        previous = self.connection.execute('SELECT kind,course FROM records WHERE id=?', (record['id'],)).fetchone()
        if previous and previous != (kind, course):
            raise ValueError('A record cannot change its kind or course.')
        self.connection.execute('INSERT INTO records VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',
                                (record['id'], kind, course, json.dumps(record, allow_nan=False)))
        if not self.depth:
            self.connection.commit()
        return record

    def get(self, id, kind=None):
        row = self.connection.execute('SELECT kind,data FROM records WHERE id=?', (id,)).fetchone()
        if not row or (kind and row[0] != kind):
            raise ValueError(f'{kind or "Record"} not found: {id}')
        return json.loads(row[1])

    def list(self, kind, course=None):
        query = 'SELECT data FROM records WHERE kind=?'
        args = [kind]
        if course is not None:
            query += ' AND course=?'
            args.append(course)
        return [json.loads(row[0]) for row in self.connection.execute(query + ' ORDER BY rowid', args)]

    def close(self):
        self.connection.close()


class EventBus:
    """Observer subject decouples domain changes from activity projections."""
    def __init__(self):
        self.observers = defaultdict(list)

    def subscribe(self, name, callback):
        self.observers[name].append(callback)

    def publish(self, name, payload):
        for callback in self.observers[name] + self.observers['*']:
            callback(name, payload)


class ProgressProjector:
    def __init__(self, repo):
        self.repo = repo

    def update(self, name, payload):
        self.repo.save('event', payload.get('course', ''), {'name': name, 'payload': payload})

