"""
Audit Logger Engine
==================

Comprehensive audit logging system for DDQ processing with
full traceability and quality assurance tracking.
"""

import json
import logging
from typing import List, Dict, Optional, Any, TextIO
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import asdict
import threading
from collections import defaultdict, deque

from .audit_types import (
    AuditEvent, AuditEventType, AuditLevel, AuditTrail,
    QualityMetric, VerificationResult, EVENT_CRITICALITY
)


class AuditLogger:
    """
    Enterprise-grade audit logging system.
    
    Features:
    - Comprehensive event logging
    - Real-time audit trail generation
    - Quality metric tracking
    - Multi-format output (JSON, CSV, structured logs)
    - Thread-safe operations
    - Configurable retention policies
    - Performance monitoring
    """
    
    def __init__(
        self,
        log_directory: str = "/tmp/ddq_audit_logs",
        retention_days: int = 90,
        max_file_size_mb: int = 50,
        enable_console_output: bool = True,
        log_level: AuditLevel = AuditLevel.INFO
    ):
        """Initialize audit logger with configuration."""
        
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        self.retention_days = retention_days
        self.max_file_size_mb = max_file_size_mb
        self.enable_console_output = enable_console_output
        self.log_level = log_level
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Active audit trails
        self.active_trails: Dict[str, AuditTrail] = {}
        
        # Event queues for batch processing
        self.event_queue = deque()
        self.metrics_queue = deque()
        
        # Performance tracking
        self.performance_stats = {
            'events_logged': 0,
            'errors_encountered': 0,
            'average_log_time_ms': 0.0,
            'last_cleanup': datetime.now()
        }
        
        # Setup logging infrastructure
        self._setup_logging_infrastructure()
        
        # Start background maintenance
        self._start_background_maintenance()
    
    def _setup_logging_infrastructure(self):
        """Setup logging files and handlers."""
        
        # Main audit log
        self.audit_log_file = self.log_directory / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        # Quality metrics log
        self.metrics_log_file = self.log_directory / f"metrics_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        # Error log
        self.error_log_file = self.log_directory / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Setup standard Python logger for errors
        self.logger = logging.getLogger('ddq_audit')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # File handler
            file_handler = logging.FileHandler(str(self.error_log_file))
            file_handler.setLevel(logging.ERROR)
            
            # Console handler
            if self.enable_console_output:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                self.logger.addHandler(console_handler)
            
            self.logger.addHandler(file_handler)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            for handler in self.logger.handlers:
                handler.setFormatter(formatter)
    
    def start_audit_trail(self, response_id: str, session_id: Optional[str] = None) -> str:
        """
        Start a new audit trail for a DDQ response.
        
        Args:
            response_id: Unique response identifier
            session_id: Optional session identifier
            
        Returns:
            Session ID for the audit trail
        """
        
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{response_id[:8]}"
        
        with self.lock:
            audit_trail = AuditTrail(
                session_id=session_id,
                response_id=response_id,
                start_time=datetime.now()
            )
            
            self.active_trails[session_id] = audit_trail
            
            # Log trail start event
            start_event = AuditEvent(
                event_id="",
                event_type=AuditEventType.RESPONSE_RECEIVED,
                timestamp=datetime.now(),
                level=AuditLevel.INFO,
                description=f"Audit trail started for response {response_id}",
                details={
                    'response_id': response_id,
                    'session_id': session_id,
                    'start_time': audit_trail.start_time.isoformat()
                },
                session_id=session_id,
                response_id=response_id,
                source_module='audit_logger'
            )
            
            self.log_event(start_event)
        
        return session_id
    
    def log_event(self, event: AuditEvent):
        """
        Log an audit event.
        
        Args:
            event: Audit event to log
        """
        
        start_time = datetime.now()
        
        try:
            with self.lock:
                # Check log level
                if event.level.value < self.log_level.value:
                    return
                
                # Add to active trail if exists
                if event.session_id and event.session_id in self.active_trails:
                    self.active_trails[event.session_id].add_event(event)
                
                # Write to audit log file
                self._write_to_audit_log(event)
                
                # Console output for critical events
                if self.enable_console_output and event.level.value >= AuditLevel.WARNING.value:
                    self._console_output(event)
                
                # Queue for batch processing
                self.event_queue.append(event)
                
                # Update performance stats
                self.performance_stats['events_logged'] += 1
                
        except Exception as e:
            self.performance_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to log audit event: {e}")
        
        finally:
            # Update performance timing
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self._update_average_log_time(duration)
    
    def log_quality_metric(self, session_id: str, metric: QualityMetric):
        """
        Log a quality assurance metric.
        
        Args:
            session_id: Session identifier
            metric: Quality metric to log
        """
        
        try:
            with self.lock:
                # Add to active trail
                if session_id in self.active_trails:
                    self.active_trails[session_id].add_quality_metric(metric)
                
                # Write to metrics log
                self._write_to_metrics_log(session_id, metric)
                
                # Create event for significant metrics
                if not metric.passed:
                    failure_event = AuditEvent(
                        event_id="",
                        event_type=AuditEventType.QUALITY_CHECK_FAILED,
                        timestamp=datetime.now(),
                        level=AuditLevel.WARNING,
                        description=f"Quality check failed: {metric.metric_name}",
                        details=metric.to_dict(),
                        session_id=session_id,
                        source_module='quality_assurance'
                    )
                    self.log_event(failure_event)
        
        except Exception as e:
            self.logger.error(f"Failed to log quality metric: {e}")
    
    def log_verification_result(self, session_id: str, result: VerificationResult):
        """
        Log a verification check result.
        
        Args:
            session_id: Session identifier
            result: Verification result to log
        """
        
        try:
            with self.lock:
                # Add to active trail
                if session_id in self.active_trails:
                    self.active_trails[session_id].add_verification_result(result)
                
                # Create appropriate event
                event_type = (AuditEventType.VERIFICATION_COMPLETED 
                             if result.passed else AuditEventType.MANUAL_REVIEW_REQUIRED)
                
                event_level = AuditLevel.INFO if result.passed else AuditLevel.WARNING
                
                verification_event = AuditEvent(
                    event_id="",
                    event_type=event_type,
                    timestamp=datetime.now(),
                    level=event_level,
                    description=f"Verification check: {result.check_name} - {result.status.value}",
                    details=result.to_dict(),
                    session_id=session_id,
                    source_module='verification_engine'
                )
                
                self.log_event(verification_event)
        
        except Exception as e:
            self.logger.error(f"Failed to log verification result: {e}")
    
    def finalize_audit_trail(self, session_id: str, final_status: str) -> Optional[AuditTrail]:
        """
        Finalize an audit trail and generate final report.
        
        Args:
            session_id: Session identifier
            final_status: Final processing status
            
        Returns:
            Completed audit trail or None if not found
        """
        
        try:
            with self.lock:
                if session_id not in self.active_trails:
                    self.logger.warning(f"Audit trail not found for session: {session_id}")
                    return None
                
                trail = self.active_trails[session_id]
                trail.finalize(final_status)
                
                # Log finalization event
                final_event = AuditEvent(
                    event_id="",
                    event_type=AuditEventType.VERIFICATION_COMPLETED,
                    timestamp=datetime.now(),
                    level=AuditLevel.INFO,
                    description=f"Audit trail finalized with status: {final_status}",
                    details={
                        'final_status': final_status,
                        'duration_seconds': trail.summary.get('duration_seconds', 0),
                        'total_events': trail.summary.get('total_events', 0),
                        'quality_scores': trail.summary.get('quality_scores', {}),
                        'verification_summary': trail.summary.get('verification_summary', {})
                    },
                    session_id=session_id,
                    response_id=trail.response_id,
                    source_module='audit_logger'
                )
                
                self.log_event(final_event)
                
                # Save complete audit trail
                self._save_audit_trail(trail)
                
                # Remove from active trails
                completed_trail = self.active_trails.pop(session_id)
                
                return completed_trail
        
        except Exception as e:
            self.logger.error(f"Failed to finalize audit trail: {e}")
            return None
    
    def get_active_trails(self) -> List[str]:
        """Get list of active audit trail session IDs."""
        with self.lock:
            return list(self.active_trails.keys())
    
    def get_trail_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of an audit trail.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Trail status information or None if not found
        """
        
        with self.lock:
            if session_id not in self.active_trails:
                return None
            
            trail = self.active_trails[session_id]
            
            return {
                'session_id': trail.session_id,
                'response_id': trail.response_id,
                'start_time': trail.start_time.isoformat(),
                'duration_seconds': (datetime.now() - trail.start_time).total_seconds(),
                'event_count': len(trail.events),
                'quality_metrics_count': len(trail.quality_metrics),
                'verification_results_count': len(trail.verification_results),
                'status': 'active'
            }
    
    def search_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        response_id: Optional[str] = None,
        session_id: Optional[str] = None,
        level: Optional[AuditLevel] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        Search audit events with filters.
        
        Args:
            start_date: Filter events after this date
            end_date: Filter events before this date
            event_types: Filter by event types
            response_id: Filter by response ID
            session_id: Filter by session ID
            level: Filter by log level
            limit: Maximum number of events to return
            
        Returns:
            List of matching audit events
        """
        
        matching_events = []
        
        try:
            # Search in active trails
            with self.lock:
                for trail in self.active_trails.values():
                    for event in trail.events:
                        if self._event_matches_filters(
                            event, start_date, end_date, event_types, 
                            response_id, session_id, level
                        ):
                            matching_events.append(event)
            
            # Search in archived logs (simplified - would need more sophisticated implementation)
            # For now, just return active trail matches
            
            # Sort by timestamp and apply limit
            matching_events.sort(key=lambda e: e.timestamp, reverse=True)
            return matching_events[:limit]
        
        except Exception as e:
            self.logger.error(f"Failed to search events: {e}")
            return []
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get audit logger performance statistics."""
        
        with self.lock:
            stats = self.performance_stats.copy()
            stats.update({
                'active_trails': len(self.active_trails),
                'queue_sizes': {
                    'events': len(self.event_queue),
                    'metrics': len(self.metrics_queue)
                },
                'log_files': {
                    'audit_log': str(self.audit_log_file),
                    'metrics_log': str(self.metrics_log_file),
                    'error_log': str(self.error_log_file)
                }
            })
            
            return stats
    
    def _write_to_audit_log(self, event: AuditEvent):
        """Write event to audit log file."""
        
        try:
            with open(self.audit_log_file, 'a', encoding='utf-8') as f:
                f.write(event.to_json() + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write to audit log: {e}")
    
    def _write_to_metrics_log(self, session_id: str, metric: QualityMetric):
        """Write metric to metrics log file."""
        
        try:
            metric_entry = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'metric': metric.to_dict()
            }
            
            with open(self.metrics_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(metric_entry) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write to metrics log: {e}")
    
    def _console_output(self, event: AuditEvent):
        """Output important events to console."""
        
        level_symbols = {
            AuditLevel.DEBUG: '🔍',
            AuditLevel.INFO: 'ℹ️',
            AuditLevel.WARNING: '⚠️',
            AuditLevel.ERROR: '❌',
            AuditLevel.CRITICAL: '🚨'
        }
        
        symbol = level_symbols.get(event.level, '📝')
        timestamp = event.timestamp.strftime('%H:%M:%S')
        
        print(f"{symbol} {timestamp} [{event.level.name}] {event.event_type.value}: {event.description}")
        
        if event.details and event.level.value >= AuditLevel.ERROR.value:
            for key, value in event.details.items():
                print(f"    {key}: {value}")
    
    def _save_audit_trail(self, trail: AuditTrail):
        """Save complete audit trail to file."""
        
        try:
            trail_file = self.log_directory / f"trail_{trail.session_id}.json"
            
            with open(trail_file, 'w', encoding='utf-8') as f:
                f.write(trail.to_json())
                
        except Exception as e:
            self.logger.error(f"Failed to save audit trail: {e}")
    
    def _event_matches_filters(
        self,
        event: AuditEvent,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        event_types: Optional[List[AuditEventType]],
        response_id: Optional[str],
        session_id: Optional[str],
        level: Optional[AuditLevel]
    ) -> bool:
        """Check if event matches search filters."""
        
        if start_date and event.timestamp < start_date:
            return False
        
        if end_date and event.timestamp > end_date:
            return False
        
        if event_types and event.event_type not in event_types:
            return False
        
        if response_id and event.response_id != response_id:
            return False
        
        if session_id and event.session_id != session_id:
            return False
        
        if level and event.level.value < level.value:
            return False
        
        return True
    
    def _update_average_log_time(self, duration_ms: float):
        """Update rolling average log time."""
        
        current_avg = self.performance_stats['average_log_time_ms']
        events_logged = self.performance_stats['events_logged']
        
        if events_logged == 1:
            self.performance_stats['average_log_time_ms'] = duration_ms
        else:
            # Rolling average calculation
            alpha = 0.1  # Weight for new observation
            self.performance_stats['average_log_time_ms'] = (
                alpha * duration_ms + (1 - alpha) * current_avg
            )
    
    def _start_background_maintenance(self):
        """Start background maintenance tasks."""
        
        # This would typically be implemented with proper threading
        # For now, we'll implement basic cleanup
        self._cleanup_old_logs()
    
    def _cleanup_old_logs(self):
        """Clean up old log files based on retention policy."""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for log_file in self.log_directory.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
            
            for log_file in self.log_directory.glob("*.jsonl"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
            
            self.performance_stats['last_cleanup'] = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")
    
    def export_trail_report(
        self, 
        session_id: str, 
        format_type: str = 'json'
    ) -> Optional[str]:
        """
        Export audit trail as formatted report.
        
        Args:
            session_id: Session identifier
            format_type: Export format ('json', 'csv', 'html')
            
        Returns:
            Report content as string or None if trail not found
        """
        
        with self.lock:
            if session_id not in self.active_trails:
                # Try to load from file
                trail_file = self.log_directory / f"trail_{session_id}.json"
                if not trail_file.exists():
                    return None
                
                try:
                    with open(trail_file, 'r', encoding='utf-8') as f:
                        trail_data = json.load(f)
                        return json.dumps(trail_data, indent=2) if format_type == 'json' else str(trail_data)
                except Exception:
                    return None
            
            trail = self.active_trails[session_id]
            
            if format_type == 'json':
                return trail.to_json()
            elif format_type == 'csv':
                return self._trail_to_csv(trail)
            elif format_type == 'html':
                return self._trail_to_html(trail)
            else:
                return trail.to_json()
    
    def _trail_to_csv(self, trail: AuditTrail) -> str:
        """Convert audit trail to CSV format."""
        
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Events CSV
        writer.writerow(['timestamp', 'event_type', 'level', 'description', 'source_module'])
        for event in trail.events:
            writer.writerow([
                event.timestamp.isoformat(),
                event.event_type.value,
                event.level.name,
                event.description,
                event.source_module or ''
            ])
        
        return output.getvalue()
    
    def _trail_to_html(self, trail: AuditTrail) -> str:
        """Convert audit trail to HTML report."""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Audit Trail Report - {trail.session_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 10px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .event {{ margin: 5px 0; padding: 5px; border-left: 3px solid #ccc; }}
                .error {{ border-left-color: #f00; }}
                .warning {{ border-left-color: #fa0; }}
                .info {{ border-left-color: #00f; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Audit Trail Report</h1>
                <p>Session ID: {trail.session_id}</p>
                <p>Response ID: {trail.response_id}</p>
                <p>Duration: {trail.summary.get('duration_seconds', 0):.2f} seconds</p>
            </div>
        """
        
        # Events section
        html += "<div class='section'><h2>Events</h2>"
        for event in trail.events:
            css_class = event.level.name.lower()
            html += f"""
            <div class="event {css_class}">
                <strong>{event.timestamp.strftime('%H:%M:%S')}</strong> - 
                {event.event_type.value} - {event.description}
            </div>
            """
        html += "</div>"
        
        # Quality metrics section
        if trail.quality_metrics:
            html += "<div class='section'><h2>Quality Metrics</h2><table>"
            html += "<tr><th>Metric</th><th>Score</th><th>Status</th></tr>"
            for metric in trail.quality_metrics:
                status = "PASS" if metric.passed else "FAIL"
                html += f"<tr><td>{metric.metric_name}</td><td>{metric.score_percentage:.1f}%</td><td>{status}</td></tr>"
            html += "</table></div>"
        
        html += "</body></html>"
        return html