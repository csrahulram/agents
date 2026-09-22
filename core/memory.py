"""Persistent memory: short-term (rolling), long-term (embedded, searchable), project state."""
import json
import math
import sqlite3
import threading
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS short_term (
    id INTEGER PRIMARY KEY, project TEXT, agent TEXT, content TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS long_term (
    id INTEGER PRIMARY KEY, project TEXT, kind TEXT, content TEXT, embedding TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS project_state (
    project TEXT, key TEXT, value TEXT, ts REAL, PRIMARY KEY (project, key));
"""


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class Memory:
    def __init__(self, path, embedder=None):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript(SCHEMA)
        self.lock = threading.Lock()
        self.embedder = embedder  # LLM with .embed(), or None for keyword search

    def _exec(self, sql, args=()):
        with self.lock:
            cur = self.db.execute(sql, args)
            self.db.commit()
            return cur.fetchall()

    # ---- short-term: recent conversation / events for a project
    def add_short(self, project, agent, content):
        self._exec("INSERT INTO short_term(project,agent,content,ts) VALUES(?,?,?,?)",
                   (project, agent, content[:4000], time.time()))

    def recent(self, project, n=10):
        rows = self._exec("SELECT agent, content FROM short_term WHERE project=? "
                          "ORDER BY id DESC LIMIT ?", (project, n))
        return list(reversed(rows))

    def short_count(self, project):
        return self._exec("SELECT COUNT(*) FROM short_term WHERE project=?", (project,))[0][0]

    def pop_oldest_short(self, project, keep):
        """Remove all but the newest `keep` rows; return the removed ones for summarising."""
        rows = self._exec("SELECT id, agent, content FROM short_term WHERE project=? "
                          "ORDER BY id DESC LIMIT -1 OFFSET ?", (project, keep))
        if rows:
            self._exec(f"DELETE FROM short_term WHERE id IN ({','.join('?' * len(rows))})",
                       [r[0] for r in rows])
        return [(a, c) for _, a, c in reversed(rows)]

    # ---- long-term: facts, lessons, summaries; searchable across projects
    def remember(self, project, kind, content):
        emb = None
        if self.embedder:
            try:
                emb = json.dumps(self.embedder.embed(content))
            except Exception:
                emb = None
        self._exec("INSERT INTO long_term(project,kind,content,embedding,ts) VALUES(?,?,?,?,?)",
                   (project, kind, content, emb, time.time()))

    def recall(self, query, k=5, project=None, kind=None):
        sql, args = "SELECT project, kind, content, embedding FROM long_term WHERE 1=1", []
        if project:
            sql += " AND project=?"; args.append(project)
        if kind:
            sql += " AND kind=?"; args.append(kind)
        rows = self._exec(sql, args)
        if not rows:
            return []
        qemb = None
        if self.embedder:
            try:
                qemb = self.embedder.embed(query)
            except Exception:
                pass
        words = {w for w in query.lower().split() if len(w) > 3}
        scored = []
        for p, kd, content, emb in rows:
            vec = json.loads(emb) if emb else None
            if qemb and vec and len(vec) == len(qemb):
                score = _cosine(qemb, vec)
            else:
                score = sum(w in content.lower() for w in words) / (len(words) or 1)
            scored.append((score, p, kd, content))
        scored.sort(reverse=True)
        return [(p, kd, c) for s, p, kd, c in scored[:k] if s > 0]

    # ---- project state: key/value persistence for resume
    def set_state(self, project, key, value):
        self._exec("INSERT OR REPLACE INTO project_state VALUES(?,?,?,?)",
                   (project, key, json.dumps(value), time.time()))

    def get_state(self, project, key, default=None):
        rows = self._exec("SELECT value FROM project_state WHERE project=? AND key=?", (project, key))
        return json.loads(rows[0][0]) if rows else default

    def projects(self):
        return self._exec("SELECT project, value FROM project_state WHERE key='status' ORDER BY ts DESC")
