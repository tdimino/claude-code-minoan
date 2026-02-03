#!/usr/bin/env python3
"""
RLAMA Logger - Centralized progress logging for RLAMA operations.

Provides:
- JSON Lines log file at ~/.rlama/logs/rlama.log
- Active operations state at ~/.rlama/logs/operations.json
- ETA calculation
- Buffered writes for performance

Usage:
    from rlama_logger import get_logger

    logger = get_logger()
    op_id = logger.start_operation('ingest', 'my-rag', 100)
    logger.update_progress(op_id, 45, 100, 'current-file.pdf')
    logger.complete_operation(op_id, success=True, summary={'added': 95, 'skipped': 5})
"""

import atexit
import json
import os
import threading
import time
import uuid
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Log directory
LOG_DIR = Path.home() / '.rlama' / 'logs'
LOG_FILE = LOG_DIR / 'rlama.log'
OPERATIONS_FILE = LOG_DIR / 'operations.json'

# Buffer settings
BUFFER_FLUSH_INTERVAL = 0.05  # 50ms
MAX_BUFFER_SIZE = 100


class RlamaLogger:
    """Centralized logger for RLAMA operations with file-based output."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        # Thread-safe singleton - always acquire lock first
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._buffer: deque = deque()
        self._buffer_lock = threading.Lock()
        self._operations: Dict[str, Dict[str, Any]] = {}
        self._recent_operations: List[Dict[str, Any]] = []
        self._flush_thread: Optional[threading.Thread] = None
        self._running = True
        self._timing_data: Dict[str, List[float]] = {}  # For ETA calculation

        # Ensure log directory exists
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Load existing operations state
        self._load_operations_state()

        # Start background flush thread
        self._start_flush_thread()

        # Register cleanup on exit
        atexit.register(self._cleanup)

    def _load_operations_state(self):
        """Load operations state from disk."""
        if OPERATIONS_FILE.exists():
            try:
                with open(OPERATIONS_FILE) as f:
                    data = json.load(f)
                    # Only load recent, active operations might be stale
                    self._recent_operations = data.get('recent', [])[-20:]  # Keep last 20
            except (json.JSONDecodeError, IOError):
                pass

    def _save_operations_state(self):
        """Save operations state to disk."""
        try:
            data = {
                'active': self._operations,
                'recent': self._recent_operations[-20:],
                'updated': datetime.now().isoformat()
            }
            with open(OPERATIONS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            import sys
            print(f"Warning: Failed to save operations state: {e}", file=sys.stderr)

    def _start_flush_thread(self):
        """Start background thread for buffered writes."""
        def flush_loop():
            while self._running:
                time.sleep(BUFFER_FLUSH_INTERVAL)
                self._flush_buffer()

        self._flush_thread = threading.Thread(target=flush_loop, daemon=True)
        self._flush_thread.start()

    def _flush_buffer(self):
        """Flush buffered log entries to file."""
        with self._buffer_lock:
            if not self._buffer:
                return

            entries = list(self._buffer)
            self._buffer.clear()

        try:
            with open(LOG_FILE, 'a') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
        except IOError:
            pass

    def _cleanup(self):
        """Cleanup on exit."""
        self._running = False
        self._flush_buffer()
        self._save_operations_state()

    def _log(self, level: str, category: str, message: str, data: Optional[Dict] = None):
        """Write a log entry."""
        entry = {
            'ts': datetime.now().isoformat(timespec='milliseconds'),
            'level': level,
            'cat': category,
            'msg': message
        }
        if data:
            entry['data'] = data

        with self._buffer_lock:
            self._buffer.append(entry)
            # Note: flush happens via background thread at regular intervals
            # Large buffer sizes will be handled by the next flush cycle

    def _calculate_eta(self, op_id: str, processed: int, total: int) -> Optional[int]:
        """Calculate ETA based on processing times."""
        if op_id not in self._timing_data or processed == 0:
            return None

        times = self._timing_data[op_id]
        if len(times) < 2:
            return None

        # Use average of recent times (last 10)
        recent_times = times[-10:]
        avg_time = sum(recent_times) / len(recent_times)
        remaining = total - processed

        return int(avg_time * remaining)

    def _record_timing(self, op_id: str, elapsed: float):
        """Record timing for ETA calculation. Keeps last 100 samples to prevent memory growth."""
        if op_id not in self._timing_data:
            self._timing_data[op_id] = []
        self._timing_data[op_id].append(elapsed)
        # Limit to last 100 samples to prevent memory growth
        if len(self._timing_data[op_id]) > 100:
            self._timing_data[op_id] = self._timing_data[op_id][-100:]

    # === Public API ===

    def start_operation(
        self,
        op_type: str,
        rag_name: str,
        total_items: int,
        extra_data: Optional[Dict] = None
    ) -> str:
        """Start tracking a new operation. Returns operation ID."""
        op_id = f"{op_type}_{uuid.uuid4().hex[:8]}"

        operation = {
            'id': op_id,
            'type': op_type,
            'rag_name': rag_name,
            'started': datetime.now().isoformat(),
            'processed': 0,
            'total': total_items,
            'current_item': None,
            'status': 'running',
            'eta_sec': None
        }
        if extra_data:
            operation.update(extra_data)

        self._operations[op_id] = operation
        self._timing_data[op_id] = []
        self._save_operations_state()

        self._log('info', op_type.upper(), f'Started {op_type} operation', {
            'op_id': op_id,
            'rag_name': rag_name,
            'total': total_items
        })

        return op_id

    def update_progress(
        self,
        op_id: str,
        processed: int,
        total: int,
        current_item: Optional[str] = None,
        status: str = 'ok',
        extra_data: Optional[Dict] = None
    ):
        """Update progress for an operation."""
        if op_id not in self._operations:
            return

        op = self._operations[op_id]

        # Calculate timing
        if 'last_update' in op:
            elapsed = time.time() - op['last_update_time']
            self._record_timing(op_id, elapsed)

        eta = self._calculate_eta(op_id, processed, total)

        op['processed'] = processed
        op['total'] = total
        op['current_item'] = current_item
        op['eta_sec'] = eta
        op['last_update'] = datetime.now().isoformat()
        op['last_update_time'] = time.time()

        self._save_operations_state()

        log_data = {
            'op_id': op_id,
            'i': processed,
            'total': total,
            'status': status
        }
        if current_item:
            log_data['file'] = current_item
        if eta:
            log_data['eta_sec'] = eta
        if extra_data:
            log_data.update(extra_data)

        self._log('info', op['type'].upper(), f'Progress {processed}/{total}', log_data)

    def complete_operation(
        self,
        op_id: str,
        success: bool,
        summary: Optional[Dict] = None
    ):
        """Mark an operation as complete."""
        if op_id not in self._operations:
            return

        op = self._operations[op_id]

        # Calculate duration
        started = datetime.fromisoformat(op['started'])
        duration_sec = (datetime.now() - started).total_seconds()

        completion_record = {
            'id': op_id,
            'type': op['type'],
            'rag_name': op['rag_name'],
            'started': op['started'],
            'completed': datetime.now().isoformat(),
            'duration_sec': round(duration_sec, 1),
            'success': success,
            'processed': op['processed'],
            'total': op['total']
        }
        if summary:
            completion_record['summary'] = summary

        self._recent_operations.append(completion_record)
        self._recent_operations = self._recent_operations[-20:]  # Keep last 20

        # Remove from active operations
        del self._operations[op_id]
        if op_id in self._timing_data:
            del self._timing_data[op_id]

        self._save_operations_state()

        status_msg = 'completed' if success else 'failed'
        log_data = {
            'op_id': op_id,
            'success': success,
            'duration_sec': round(duration_sec, 1)
        }
        if summary:
            log_data.update(summary)

        level = 'info' if success else 'error'
        self._log(level, op['type'].upper(), f'Operation {status_msg}', log_data)

    def log_error(self, category: str, message: str, data: Optional[Dict] = None):
        """Log an error."""
        self._log('error', category, message, data)

    def log_warning(self, category: str, message: str, data: Optional[Dict] = None):
        """Log a warning."""
        self._log('warn', category, message, data)

    def log_info(self, category: str, message: str, data: Optional[Dict] = None):
        """Log an info message."""
        self._log('info', category, message, data)

    def log_debug(self, category: str, message: str, data: Optional[Dict] = None):
        """Log a debug message."""
        self._log('debug', category, message, data)

    # === Category-specific helpers ===

    def ingest_start(self, rag_name: str, folder_path: str, total_files: int) -> str:
        """Start an ingest operation."""
        return self.start_operation('ingest', rag_name, total_files, {
            'folder': str(folder_path)
        })

    def ingest_progress(
        self,
        op_id: str,
        processed: int,
        total: int,
        filename: str,
        status: str = 'ok'
    ):
        """Update ingest progress."""
        self.update_progress(op_id, processed, total, filename, status)

    def ingest_complete(
        self,
        op_id: str,
        added: int,
        skipped: int,
        elapsed_sec: float
    ):
        """Complete an ingest operation."""
        self.complete_operation(op_id, success=True, summary={
            'added': added,
            'skipped': skipped,
            'elapsed_sec': round(elapsed_sec, 1)
        })

    def dedupe_start(self, rag_name: str, total_duplicates: int) -> str:
        """Start a deduplication operation."""
        return self.start_operation('dedupe', rag_name, total_duplicates)

    def dedupe_progress(
        self,
        op_id: str,
        processed: int,
        total: int,
        doc_id: str,
        status: str = 'ok'
    ):
        """Update dedupe progress."""
        self.update_progress(op_id, processed, total, doc_id, status)

    def dedupe_complete(self, op_id: str, removed: int, failed: int):
        """Complete a dedupe operation."""
        self.complete_operation(op_id, success=True, summary={
            'removed': removed,
            'failed': failed
        })

    def batch_start(self, rag_name: str, total_batches: int, total_files: int) -> str:
        """Start a batch ingest operation."""
        return self.start_operation('batch', rag_name, total_files, {
            'total_batches': total_batches
        })

    def batch_progress(
        self,
        op_id: str,
        batch_num: int,
        total_batches: int,
        files_processed: int,
        total_files: int
    ):
        """Update batch progress."""
        self.update_progress(
            op_id, files_processed, total_files,
            f'batch {batch_num}/{total_batches}',
            extra_data={'batch': batch_num, 'total_batches': total_batches}
        )

    def batch_complete(self, op_id: str, files_ingested: int, batches_completed: int):
        """Complete a batch operation."""
        self.complete_operation(op_id, success=True, summary={
            'files_ingested': files_ingested,
            'batches': batches_completed
        })

    # === State accessors ===

    def get_active_operations(self) -> Dict[str, Dict]:
        """Get all active operations."""
        return dict(self._operations)

    def get_recent_operations(self, limit: int = 10) -> List[Dict]:
        """Get recent completed operations."""
        return self._recent_operations[-limit:]

    def flush(self):
        """Force flush the buffer."""
        self._flush_buffer()
        self._save_operations_state()


def get_logger() -> RlamaLogger:
    """Get the singleton logger instance."""
    return RlamaLogger()


def get_log_file_path() -> Path:
    """Get the log file path."""
    return LOG_FILE


def clear_log():
    """Clear the log file."""
    try:
        LOG_FILE.unlink(missing_ok=True)
    except IOError:
        pass


if __name__ == '__main__':
    # Test the logger
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        logger = get_logger()

        # Simulate an ingest operation
        op_id = logger.ingest_start('test-rag', '/tmp/test', 10)

        for i in range(1, 11):
            time.sleep(0.1)  # Simulate processing
            logger.ingest_progress(op_id, i, 10, f'file{i}.pdf', 'ok')

        logger.ingest_complete(op_id, added=8, skipped=2, elapsed_sec=1.5)
        logger.flush()

        print(f"Test complete. Check {LOG_FILE}")
        print(f"Active: {logger.get_active_operations()}")
        print(f"Recent: {logger.get_recent_operations()}")
    else:
        print(f"Log file: {LOG_FILE}")
        print(f"Operations state: {OPERATIONS_FILE}")
        print("\nUsage: python3 rlama_logger.py test")
