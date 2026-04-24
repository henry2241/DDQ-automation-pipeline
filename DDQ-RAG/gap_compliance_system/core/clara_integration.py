"""
Clara Integration Layer
======================

Main integration interface for Clara architecture to leverage
DDQ gap handling and compliance safeguard systems.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.gap_detection.gap_detector import GapDetector
from modules.gap_detection.gap_types import DetectionContext
from modules.compliance_engine.compliance_checker import ComplianceChecker
from modules.compliance_engine.disclaimer_engine import DisclaimerEngine  
from modules.compliance_engine.compliance_types import ComplianceContext
from modules.depth_analyzer.depth_analyzer import DepthAnalyzer
from modules.depth_analyzer.depth_types import DepthAnalysisContext
from modules.risk_assessment.risk_assessor import RiskAssessor
from modules.risk_assessment.risk_types import RiskAssessmentContext
from modules.audit_trail.audit_logger import AuditLogger
from modules.audit_trail.audit_types import AuditEvent, AuditEventType, AuditLevel

from .system_orchestrator import SystemOrchestrator
from .configuration_manager import ConfigurationManager


@dataclass
class DDQProcessingRequest:
    """Request structure for DDQ processing."""
    
    response_id: str
    question_id: str
    response_text: str
    question_text: str
    source_documents: Optional[List[str]] = None
    firm_type: str = "investment_adviser"
    client_types: List[str] = None
    processing_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.client_types is None:
            self.client_types = ["institutional"]
        if self.processing_options is None:
            self.processing_options = {}


@dataclass 
class DDQProcessingResult:
    """Result structure for DDQ processing."""
    
    request_id: str
    session_id: str
    original_response: str
    processed_response: str
    modifications_made: List[str]
    gap_report: Dict[str, Any]
    compliance_report: Dict[str, Any]
    depth_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    overall_quality_score: float
    processing_time_ms: int
    recommendations: List[str]
    requires_manual_review: bool
    audit_trail_id: str


class ClaraIntegrationLayer:
    """
    Main integration interface for Clara DDQ processing.
    
    This class provides a clean, enterprise-ready API for Clara
    to leverage all gap handling and compliance systems.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Clara integration layer."""
        
        # Configuration management
        self.config = ConfigurationManager(config_path)
        
        # Core system components
        self.gap_detector = GapDetector()
        self.compliance_checker = ComplianceChecker()
        self.disclaimer_engine = DisclaimerEngine()
        self.depth_analyzer = DepthAnalyzer()
        self.risk_assessor = RiskAssessor()
        
        # Audit and orchestration
        self.audit_logger = AuditLogger(
            log_directory=self.config.get('logging.directory', '/tmp/ddq_logs'),
            retention_days=self.config.get('logging.retention_days', 90),
            log_level=AuditLevel.INFO
        )
        
        self.orchestrator = SystemOrchestrator(
            gap_detector=self.gap_detector,
            compliance_checker=self.compliance_checker,
            disclaimer_engine=self.disclaimer_engine,
            depth_analyzer=self.depth_analyzer,
            risk_assessor=self.risk_assessor,
            audit_logger=self.audit_logger,
            config=self.config
        )
        
        # Performance tracking
        self.processing_stats = {
            'total_requests': 0,
            'successful_processes': 0,
            'failed_processes': 0,
            'average_processing_time_ms': 0.0,
            'total_gaps_detected': 0,
            'total_compliance_violations': 0,
            'manual_reviews_required': 0
        }
    
    async def process_ddq_response(
        self, 
        request: DDQProcessingRequest,
        async_processing: bool = False
    ) -> DDQProcessingResult:
        """
        Main entry point for Clara to process DDQ responses.
        
        Args:
            request: DDQ processing request with response and metadata
            async_processing: Whether to process asynchronously
            
        Returns:
            Comprehensive processing result with all analysis and improvements
        """
        
        start_time = datetime.now()
        
        # Start audit trail
        session_id = self.audit_logger.start_audit_trail(
            response_id=request.response_id
        )
        
        try:
            # Log processing start
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.RESPONSE_RECEIVED,
                timestamp=datetime.now(),
                level=AuditLevel.INFO,
                description=f"Starting DDQ processing for response {request.response_id}",
                details={
                    'question_id': request.question_id,
                    'response_length': len(request.response_text),
                    'firm_type': request.firm_type,
                    'client_types': request.client_types
                },
                session_id=session_id,
                response_id=request.response_id,
                source_module='clara_integration'
            ))
            
            if async_processing:
                result = await self._process_async(request, session_id)
            else:
                result = await self._process_sync(request, session_id)
            
            # Update statistics
            self._update_processing_stats(result, start_time)
            
            # Finalize audit trail
            final_status = "completed_successfully" if not result.requires_manual_review else "requires_manual_review"
            self.audit_logger.finalize_audit_trail(session_id, final_status)
            
            return result
            
        except Exception as e:
            # Log error
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.PROCESSING_ERROR,
                timestamp=datetime.now(),
                level=AuditLevel.ERROR,
                description=f"Processing failed: {str(e)}",
                details={'error': str(e), 'error_type': type(e).__name__},
                session_id=session_id,
                response_id=request.response_id,
                source_module='clara_integration'
            ))
            
            # Finalize with error status
            self.audit_logger.finalize_audit_trail(session_id, "processing_failed")
            
            # Update error statistics
            self.processing_stats['failed_processes'] += 1
            
            raise
    
    async def _process_sync(
        self,
        request: DDQProcessingRequest,
        session_id: str
    ) -> DDQProcessingResult:
        """Process DDQ response synchronously."""
        
        return await self.orchestrator.orchestrate_processing(
            request=request,
            session_id=session_id
        )
    
    async def _process_async(
        self,
        request: DDQProcessingRequest,
        session_id: str
    ) -> DDQProcessingResult:
        """Process DDQ response asynchronously."""
        
        # For now, same as sync - could be enhanced for true async processing
        return await self.orchestrator.orchestrate_processing(
            request=request,
            session_id=session_id
        )
    
    def batch_process_responses(
        self,
        requests: List[DDQProcessingRequest],
        max_concurrent: int = 5
    ) -> List[DDQProcessingResult]:
        """
        Process multiple DDQ responses in batch.
        
        Args:
            requests: List of DDQ processing requests
            max_concurrent: Maximum concurrent processing tasks
            
        Returns:
            List of processing results
        """
        
        async def process_batch():
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_single(req):
                async with semaphore:
                    return await self.process_ddq_response(req, async_processing=True)
            
            # Process all requests concurrently
            tasks = [process_single(req) for req in requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and log them
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.audit_logger.logger.error(f"Batch processing failed for request {i}: {result}")
                else:
                    valid_results.append(result)
            
            return valid_results
        
        # Run batch processing
        return asyncio.run(process_batch())
    
    def validate_response_quality(
        self,
        response_text: str,
        question_text: str,
        quality_thresholds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Validate response quality against standards.
        
        Args:
            response_text: Response text to validate
            question_text: Original question text
            quality_thresholds: Custom quality thresholds
            
        Returns:
            Quality validation report
        """
        
        if quality_thresholds is None:
            quality_thresholds = self.config.get('quality.thresholds', {
                'gap_detection_accuracy': 85.0,
                'compliance_coverage': 95.0,
                'depth_score': 70.0,
                'risk_score_max': 25.0
            })
        
        # Quick gap analysis
        gap_context = DetectionContext(
            response_text=response_text,
            question_text=question_text,
            source_documents=[],
            response_id="validation_check",
            question_id="validation_check"
        )
        
        gap_report = self.gap_detector.detect_gaps(gap_context)
        
        # Quick compliance check
        compliance_context = ComplianceContext(
            response_text=response_text,
            response_id="validation_check",
            firm_type="investment_adviser",
            client_type="institutional"
        )
        
        compliance_report = self.compliance_checker.check_compliance(compliance_context)
        
        # Calculate quality scores
        gap_score = max(0, 100 - (gap_report.total_gaps * 10))  # Penalty per gap
        compliance_score = 100 - compliance_report.overall_risk_score
        
        quality_result = {
            'overall_quality': (gap_score + compliance_score) / 2,
            'gap_score': gap_score,
            'compliance_score': compliance_score,
            'meets_thresholds': {
                'gap_detection': gap_score >= quality_thresholds.get('gap_detection_accuracy', 85),
                'compliance_coverage': compliance_score >= quality_thresholds.get('compliance_coverage', 95)
            },
            'recommendations': []
        }
        
        # Generate recommendations
        if gap_score < quality_thresholds.get('gap_detection_accuracy', 85):
            quality_result['recommendations'].append(f"Address {gap_report.total_gaps} identified gaps")
        
        if compliance_score < quality_thresholds.get('compliance_coverage', 95):
            quality_result['recommendations'].append(f"Resolve {len(compliance_report.violations)} compliance issues")
        
        return quality_result
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        
        stats = self.processing_stats.copy()
        
        # Add audit logger statistics
        audit_stats = self.audit_logger.get_performance_statistics()
        stats['audit_performance'] = audit_stats
        
        # Add system component statistics
        stats['active_audit_trails'] = len(self.audit_logger.get_active_trails())
        
        # Calculate success rate
        total_requests = stats['total_requests']
        if total_requests > 0:
            stats['success_rate'] = (stats['successful_processes'] / total_requests) * 100
            stats['failure_rate'] = (stats['failed_processes'] / total_requests) * 100
            stats['manual_review_rate'] = (stats['manual_reviews_required'] / total_requests) * 100
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
            stats['manual_review_rate'] = 0.0
        
        return stats
    
    def configure_system(self, configuration: Dict[str, Any]):
        """Update system configuration."""
        
        self.config.update_configuration(configuration)
        
        # Log configuration change
        self.audit_logger.log_event(AuditEvent(
            event_id="",
            event_type=AuditEventType.CONFIGURATION_CHANGE,
            timestamp=datetime.now(),
            level=AuditLevel.INFO,
            description="System configuration updated",
            details=configuration,
            source_module='clara_integration'
        ))
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {
                'gap_detector': 'operational',
                'compliance_checker': 'operational', 
                'disclaimer_engine': 'operational',
                'depth_analyzer': 'operational',
                'risk_assessor': 'operational',
                'audit_logger': 'operational'
            },
            'performance': self.get_processing_statistics(),
            'configuration': {
                'version': self.config.get('system.version', '1.0.0'),
                'environment': self.config.get('system.environment', 'production')
            }
        }
        
        # Check for issues
        perf_stats = health_status['performance']
        
        if perf_stats['failure_rate'] > 5.0:
            health_status['overall_status'] = 'degraded'
            health_status['issues'] = ['High failure rate detected']
        
        if perf_stats['manual_review_rate'] > 20.0:
            health_status['overall_status'] = 'warning'
            health_status['issues'] = health_status.get('issues', []) + ['High manual review rate']
        
        return health_status
    
    def export_processing_report(
        self,
        session_id: str,
        format_type: str = 'json'
    ) -> Optional[str]:
        """
        Export comprehensive processing report.
        
        Args:
            session_id: Processing session ID
            format_type: Export format ('json', 'html', 'pdf')
            
        Returns:
            Formatted report or None if session not found
        """
        
        return self.audit_logger.export_trail_report(session_id, format_type)
    
    def search_processing_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        response_id: Optional[str] = None,
        quality_threshold: Optional[float] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search processing history with filters.
        
        Args:
            start_date: Filter by start date
            end_date: Filter by end date  
            response_id: Filter by response ID
            quality_threshold: Filter by minimum quality score
            limit: Maximum results to return
            
        Returns:
            List of matching processing sessions
        """
        
        # This would typically query a database or search logs
        # For now, we'll use the audit logger's search functionality
        
        events = self.audit_logger.search_events(
            start_date=start_date,
            end_date=end_date,
            response_id=response_id,
            limit=limit
        )
        
        # Group events by session and extract key information
        sessions = {}
        for event in events:
            if event.session_id not in sessions:
                sessions[event.session_id] = {
                    'session_id': event.session_id,
                    'response_id': event.response_id,
                    'start_time': event.timestamp,
                    'events': []
                }
            sessions[event.session_id]['events'].append({
                'timestamp': event.timestamp.isoformat(),
                'event_type': event.event_type.value,
                'description': event.description
            })
        
        return list(sessions.values())
    
    def _update_processing_stats(
        self,
        result: DDQProcessingResult,
        start_time: datetime
    ):
        """Update internal processing statistics."""
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        self.processing_stats['total_requests'] += 1
        self.processing_stats['successful_processes'] += 1
        
        if result.requires_manual_review:
            self.processing_stats['manual_reviews_required'] += 1
        
        # Update average processing time
        current_avg = self.processing_stats['average_processing_time_ms']
        total_requests = self.processing_stats['total_requests']
        
        if total_requests == 1:
            self.processing_stats['average_processing_time_ms'] = processing_time
        else:
            # Rolling average
            alpha = 0.1
            self.processing_stats['average_processing_time_ms'] = (
                alpha * processing_time + (1 - alpha) * current_avg
            )
        
        # Count gaps and violations
        gap_data = result.gap_report
        compliance_data = result.compliance_report
        
        if isinstance(gap_data, dict) and 'total_gaps' in gap_data:
            self.processing_stats['total_gaps_detected'] += gap_data['total_gaps']
        
        if isinstance(compliance_data, dict) and 'violations' in compliance_data:
            self.processing_stats['total_compliance_violations'] += len(compliance_data['violations'])


# Convenience functions for Clara integration
def create_clara_integration(config_path: Optional[str] = None) -> ClaraIntegrationLayer:
    """Create and initialize Clara integration layer."""
    return ClaraIntegrationLayer(config_path)


def quick_quality_check(
    response_text: str,
    question_text: str,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """Quick quality check for a DDQ response."""
    
    integration = create_clara_integration(config_path)
    return integration.validate_response_quality(response_text, question_text)


async def process_single_response(
    response_text: str,
    question_text: str,
    response_id: str,
    question_id: str,
    config_path: Optional[str] = None,
    **kwargs
) -> DDQProcessingResult:
    """Process a single DDQ response with full analysis."""
    
    integration = create_clara_integration(config_path)
    
    request = DDQProcessingRequest(
        response_id=response_id,
        question_id=question_id,
        response_text=response_text,
        question_text=question_text,
        **kwargs
    )
    
    return await integration.process_ddq_response(request)