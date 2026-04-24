"""
System Orchestrator
==================

Orchestrates the execution of all DDQ processing systems in the correct
order with proper error handling and quality assurance.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from ..modules.gap_detection import GapDetector, DetectionContext
from ..modules.compliance_engine import ComplianceChecker, DisclaimerEngine, ComplianceContext
from ..modules.depth_analyzer import DepthAnalyzer, DepthAnalysisContext
from ..modules.risk_assessment import RiskAssessor, RiskAssessmentContext
from ..modules.audit_trail import AuditLogger, AuditEvent, AuditEventType, AuditLevel, QualityMetric, QualityDimension

from .configuration_manager import ConfigurationManager


@dataclass
class ProcessingStage:
    """Represents a processing stage with its configuration."""
    
    name: str
    enabled: bool
    timeout_seconds: int
    retry_attempts: int
    quality_threshold: float
    dependencies: List[str]


class SystemOrchestrator:
    """
    Orchestrates all DDQ processing systems.
    
    Features:
    - Sequential and parallel processing coordination
    - Quality gate enforcement between stages
    - Error handling and recovery
    - Performance monitoring
    - Configuration-driven processing flow
    """
    
    def __init__(
        self,
        gap_detector: GapDetector,
        compliance_checker: ComplianceChecker,
        disclaimer_engine: DisclaimerEngine,
        depth_analyzer: DepthAnalyzer,
        risk_assessor: RiskAssessor,
        audit_logger: AuditLogger,
        config: ConfigurationManager
    ):
        """Initialize system orchestrator with components."""
        
        self.gap_detector = gap_detector
        self.compliance_checker = compliance_checker
        self.disclaimer_engine = disclaimer_engine
        self.depth_analyzer = depth_analyzer
        self.risk_assessor = risk_assessor
        self.audit_logger = audit_logger
        self.config = config
        
        # Processing stages configuration
        self.processing_stages = self._initialize_processing_stages()
        
        # Quality gates
        self.quality_gates = self._initialize_quality_gates()
        
        # Performance tracking
        self.stage_performance = {}
    
    def _initialize_processing_stages(self) -> Dict[str, ProcessingStage]:
        """Initialize processing stages configuration."""
        
        return {
            'gap_detection': ProcessingStage(
                name='Gap Detection',
                enabled=self.config.get('stages.gap_detection.enabled', True),
                timeout_seconds=self.config.get('stages.gap_detection.timeout', 30),
                retry_attempts=self.config.get('stages.gap_detection.retries', 2),
                quality_threshold=self.config.get('stages.gap_detection.quality_threshold', 85.0),
                dependencies=[]
            ),
            
            'depth_analysis': ProcessingStage(
                name='Depth Analysis',
                enabled=self.config.get('stages.depth_analysis.enabled', True),
                timeout_seconds=self.config.get('stages.depth_analysis.timeout', 45),
                retry_attempts=self.config.get('stages.depth_analysis.retries', 2),
                quality_threshold=self.config.get('stages.depth_analysis.quality_threshold', 70.0),
                dependencies=[]
            ),
            
            'compliance_check': ProcessingStage(
                name='Compliance Check',
                enabled=self.config.get('stages.compliance_check.enabled', True),
                timeout_seconds=self.config.get('stages.compliance_check.timeout', 40),
                retry_attempts=self.config.get('stages.compliance_check.retries', 3),
                quality_threshold=self.config.get('stages.compliance_check.quality_threshold', 95.0),
                dependencies=['gap_detection']
            ),
            
            'risk_assessment': ProcessingStage(
                name='Risk Assessment',
                enabled=self.config.get('stages.risk_assessment.enabled', True),
                timeout_seconds=self.config.get('stages.risk_assessment.timeout', 35),
                retry_attempts=self.config.get('stages.risk_assessment.retries', 2),
                quality_threshold=self.config.get('stages.risk_assessment.quality_threshold', 80.0),
                dependencies=['compliance_check']
            ),
            
            'disclaimer_insertion': ProcessingStage(
                name='Disclaimer Insertion',
                enabled=self.config.get('stages.disclaimer_insertion.enabled', True),
                timeout_seconds=self.config.get('stages.disclaimer_insertion.timeout', 20),
                retry_attempts=self.config.get('stages.disclaimer_insertion.retries', 2),
                quality_threshold=self.config.get('stages.disclaimer_insertion.quality_threshold', 98.0),
                dependencies=['compliance_check', 'risk_assessment']
            )
        }
    
    def _initialize_quality_gates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize quality gates between processing stages."""
        
        return {
            'gap_detection_gate': {
                'critical_gaps_max': self.config.get('quality_gates.critical_gaps_max', 3),
                'total_gaps_max': self.config.get('quality_gates.total_gaps_max', 10),
                'confidence_min': self.config.get('quality_gates.gap_confidence_min', 0.7)
            },
            
            'compliance_gate': {
                'critical_violations_max': self.config.get('quality_gates.critical_violations_max', 0),
                'overall_risk_score_max': self.config.get('quality_gates.risk_score_max', 25.0),
                'compliance_grade_min': self.config.get('quality_gates.compliance_grade_min', 'C')
            },
            
            'depth_gate': {
                'depth_score_min': self.config.get('quality_gates.depth_score_min', 60.0),
                'coverage_gaps_max': self.config.get('quality_gates.coverage_gaps_max', 5),
                'consistency_score_min': self.config.get('quality_gates.consistency_score_min', 70.0)
            },
            
            'risk_gate': {
                'overall_risk_score_max': self.config.get('quality_gates.overall_risk_max', 30.0),
                'critical_risks_max': self.config.get('quality_gates.critical_risks_max', 1),
                'risk_grade_min': self.config.get('quality_gates.risk_grade_min', 'C')
            }
        }
    
    async def orchestrate_processing(
        self,
        request,  # DDQProcessingRequest
        session_id: str
    ):  # -> DDQProcessingResult
        """
        Main orchestration method for DDQ processing.
        
        Args:
            request: DDQ processing request
            session_id: Audit session ID
            
        Returns:
            Comprehensive processing result
        """
        
        processing_start = datetime.now()
        
        # Initialize processing context
        processing_context = {
            'request': request,
            'session_id': session_id,
            'stage_results': {},
            'quality_metrics': [],
            'requires_manual_review': False,
            'modifications_made': [],
            'current_response_text': request.response_text
        }
        
        try:
            # Execute processing stages in order
            await self._execute_processing_pipeline(processing_context)
            
            # Generate final result
            result = self._generate_final_result(processing_context, processing_start)
            
            return result
            
        except Exception as e:
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.PROCESSING_ERROR,
                timestamp=datetime.now(),
                level=AuditLevel.ERROR,
                description=f"Orchestration failed: {str(e)}",
                details={'error': str(e), 'stage_results': list(processing_context['stage_results'].keys())},
                session_id=session_id,
                response_id=request.response_id,
                source_module='system_orchestrator'
            ))
            
            raise
    
    async def _execute_processing_pipeline(self, context: Dict[str, Any]):
        """Execute the complete processing pipeline."""
        
        # Stage 1: Gap Detection
        if self.processing_stages['gap_detection'].enabled:
            await self._execute_gap_detection_stage(context)
            await self._apply_gap_detection_quality_gate(context)
        
        # Stage 2: Depth Analysis (can run in parallel with gap detection)
        if self.processing_stages['depth_analysis'].enabled:
            await self._execute_depth_analysis_stage(context)
            await self._apply_depth_analysis_quality_gate(context)
        
        # Stage 3: Compliance Check (depends on gap detection)
        if self.processing_stages['compliance_check'].enabled:
            await self._execute_compliance_check_stage(context)
            await self._apply_compliance_quality_gate(context)
        
        # Stage 4: Risk Assessment (depends on compliance check)
        if self.processing_stages['risk_assessment'].enabled:
            await self._execute_risk_assessment_stage(context)
            await self._apply_risk_assessment_quality_gate(context)
        
        # Stage 5: Disclaimer Insertion (depends on compliance and risk)
        if self.processing_stages['disclaimer_insertion'].enabled:
            await self._execute_disclaimer_insertion_stage(context)
    
    async def _execute_gap_detection_stage(self, context: Dict[str, Any]):
        """Execute gap detection stage."""
        
        stage_start = datetime.now()
        request = context['request']
        session_id = context['session_id']
        
        self.audit_logger.log_event(AuditEvent(
            event_id="",
            event_type=AuditEventType.GAP_DETECTION_STARTED,
            timestamp=datetime.now(),
            level=AuditLevel.INFO,
            description="Starting gap detection analysis",
            session_id=session_id,
            response_id=request.response_id,
            source_module='gap_detector'
        ))
        
        try:
            # Create detection context
            detection_context = DetectionContext(
                response_text=context['current_response_text'],
                question_text=request.question_text,
                source_documents=request.source_documents or [],
                response_id=request.response_id,
                question_id=request.question_id
            )
            
            # Execute gap detection with timeout
            gap_report = await asyncio.wait_for(
                self._run_gap_detection(detection_context),
                timeout=self.processing_stages['gap_detection'].timeout_seconds
            )
            
            # Store results
            context['stage_results']['gap_detection'] = gap_report
            
            # Log quality metrics
            gap_quality = QualityMetric(
                metric_name='gap_detection_accuracy',
                dimension=QualityDimension.ACCURACY,
                value=max(0, 100 - gap_report.total_gaps * 5),  # 5 points per gap
                max_value=100.0,
                threshold=self.processing_stages['gap_detection'].quality_threshold,
                passed=gap_report.total_gaps <= 5,
                description='Gap detection accuracy score'
            )
            
            self.audit_logger.log_quality_metric(session_id, gap_quality)
            context['quality_metrics'].append(gap_quality)
            
            # Record performance
            stage_duration = (datetime.now() - stage_start).total_seconds() * 1000
            self._record_stage_performance('gap_detection', stage_duration)
            
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.GAP_DETECTION_COMPLETED,
                timestamp=datetime.now(),
                level=AuditLevel.INFO,
                description=f"Gap detection completed: {gap_report.total_gaps} gaps found",
                details={
                    'total_gaps': gap_report.total_gaps,
                    'critical_gaps': gap_report.critical_gaps,
                    'overall_score': gap_report.overall_score,
                    'duration_ms': stage_duration
                },
                session_id=session_id,
                response_id=request.response_id,
                source_module='gap_detector'
            ))
            
        except asyncio.TimeoutError:
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.PROCESSING_ERROR,
                timestamp=datetime.now(),
                level=AuditLevel.ERROR,
                description="Gap detection stage timed out",
                session_id=session_id,
                response_id=request.response_id,
                source_module='gap_detector'
            ))
            raise
    
    async def _execute_depth_analysis_stage(self, context: Dict[str, Any]):
        """Execute depth analysis stage."""
        
        stage_start = datetime.now()
        request = context['request']
        session_id = context['session_id']
        
        try:
            # Create depth analysis context
            depth_context = DepthAnalysisContext(
                response_text=context['current_response_text'],
                question_text=request.question_text,
                response_id=request.response_id,
                source_documents=request.source_documents
            )
            
            # Execute depth analysis
            depth_report = await asyncio.wait_for(
                self._run_depth_analysis(depth_context),
                timeout=self.processing_stages['depth_analysis'].timeout_seconds
            )
            
            # Store results
            context['stage_results']['depth_analysis'] = depth_report
            
            # Log quality metrics
            depth_quality = QualityMetric(
                metric_name='depth_analysis_score',
                dimension=QualityDimension.COMPLETENESS,
                value=depth_report.overall_depth_score,
                max_value=100.0,
                threshold=self.processing_stages['depth_analysis'].quality_threshold,
                passed=depth_report.overall_depth_score >= self.processing_stages['depth_analysis'].quality_threshold,
                description='Response depth analysis score'
            )
            
            self.audit_logger.log_quality_metric(session_id, depth_quality)
            context['quality_metrics'].append(depth_quality)
            
            # Record performance
            stage_duration = (datetime.now() - stage_start).total_seconds() * 1000
            self._record_stage_performance('depth_analysis', stage_duration)
            
        except Exception as e:
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.PROCESSING_ERROR,
                timestamp=datetime.now(),
                level=AuditLevel.ERROR,
                description=f"Depth analysis failed: {str(e)}",
                session_id=session_id,
                response_id=request.response_id,
                source_module='depth_analyzer'
            ))
            raise
    
    async def _execute_compliance_check_stage(self, context: Dict[str, Any]):
        """Execute compliance check stage."""
        
        stage_start = datetime.now()
        request = context['request']
        session_id = context['session_id']
        
        try:
            # Create compliance context
            compliance_context = ComplianceContext(
                response_text=context['current_response_text'],
                response_id=request.response_id,
                firm_type=request.firm_type,
                client_type=request.client_types[0] if request.client_types else 'institutional'
            )
            
            # Execute compliance check
            compliance_report = await asyncio.wait_for(
                self._run_compliance_check(compliance_context),
                timeout=self.processing_stages['compliance_check'].timeout_seconds
            )
            
            # Store results
            context['stage_results']['compliance_check'] = compliance_report
            
            # Log quality metrics
            compliance_quality = QualityMetric(
                metric_name='compliance_score',
                dimension=QualityDimension.COMPLIANCE,
                value=max(0, 100 - compliance_report.overall_risk_score),
                max_value=100.0,
                threshold=self.processing_stages['compliance_check'].quality_threshold,
                passed=compliance_report.compliance_grade in ['A', 'B'],
                description='Compliance adherence score'
            )
            
            self.audit_logger.log_quality_metric(session_id, compliance_quality)
            context['quality_metrics'].append(compliance_quality)
            
            # Record performance
            stage_duration = (datetime.now() - stage_start).total_seconds() * 1000
            self._record_stage_performance('compliance_check', stage_duration)
            
        except Exception as e:
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.PROCESSING_ERROR,
                timestamp=datetime.now(),
                level=AuditLevel.ERROR,
                description=f"Compliance check failed: {str(e)}",
                session_id=session_id,
                response_id=request.response_id,
                source_module='compliance_checker'
            ))
            raise
    
    async def _execute_risk_assessment_stage(self, context: Dict[str, Any]):
        """Execute risk assessment stage."""
        
        stage_start = datetime.now()
        request = context['request']
        session_id = context['session_id']
        
        try:
            # Create risk assessment context
            risk_context = RiskAssessmentContext(
                response_text=context['current_response_text'],
                response_id=request.response_id,
                firm_type=request.firm_type,
                client_types=request.client_types,
                services_provided=['advisory'],  # Default
                regulatory_registrations=[]  # Would be provided in real implementation
            )
            
            # Execute risk assessment
            risk_report = await asyncio.wait_for(
                self._run_risk_assessment(risk_context),
                timeout=self.processing_stages['risk_assessment'].timeout_seconds
            )
            
            # Store results
            context['stage_results']['risk_assessment'] = risk_report
            
            # Log quality metrics
            risk_quality = QualityMetric(
                metric_name='risk_assessment_score',
                dimension=QualityDimension.COMPLIANCE,
                value=max(0, 100 - risk_report.overall_risk_score),
                max_value=100.0,
                threshold=self.processing_stages['risk_assessment'].quality_threshold,
                passed=risk_report.overall_risk_score <= 30.0,
                description='Risk assessment score'
            )
            
            self.audit_logger.log_quality_metric(session_id, risk_quality)
            context['quality_metrics'].append(risk_quality)
            
            # Record performance
            stage_duration = (datetime.now() - stage_start).total_seconds() * 1000
            self._record_stage_performance('risk_assessment', stage_duration)
            
        except Exception as e:
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.PROCESSING_ERROR,
                timestamp=datetime.now(),
                level=AuditLevel.ERROR,
                description=f"Risk assessment failed: {str(e)}",
                session_id=session_id,
                response_id=request.response_id,
                source_module='risk_assessor'
            ))
            raise
    
    async def _execute_disclaimer_insertion_stage(self, context: Dict[str, Any]):
        """Execute disclaimer insertion stage."""
        
        stage_start = datetime.now()
        request = context['request']
        session_id = context['session_id']
        
        try:
            # Determine required disclaimers from compliance and risk results
            required_disclaimers = []
            
            if 'compliance_check' in context['stage_results']:
                compliance_report = context['stage_results']['compliance_check']
                required_disclaimers.extend(compliance_report.required_disclaimers)
            
            if required_disclaimers:
                # Insert disclaimers
                modified_text, insertions = self.disclaimer_engine.auto_insert_disclaimers(
                    context['current_response_text'],
                    required_disclaimers
                )
                
                # Update current response text
                context['current_response_text'] = modified_text
                context['modifications_made'].extend([f"Added {ins.disclaimer_type.name} disclaimer" for ins in insertions])
                
                self.audit_logger.log_event(AuditEvent(
                    event_id="",
                    event_type=AuditEventType.DISCLAIMER_INSERTION,
                    timestamp=datetime.now(),
                    level=AuditLevel.INFO,
                    description=f"Inserted {len(insertions)} disclaimers",
                    details={'disclaimers': [ins.disclaimer_type.name for ins in insertions]},
                    session_id=session_id,
                    response_id=request.response_id,
                    source_module='disclaimer_engine'
                ))
            
            # Record performance
            stage_duration = (datetime.now() - stage_start).total_seconds() * 1000
            self._record_stage_performance('disclaimer_insertion', stage_duration)
            
        except Exception as e:
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.PROCESSING_ERROR,
                timestamp=datetime.now(),
                level=AuditLevel.ERROR,
                description=f"Disclaimer insertion failed: {str(e)}",
                session_id=session_id,
                response_id=request.response_id,
                source_module='disclaimer_engine'
            ))
            raise
    
    async def _apply_gap_detection_quality_gate(self, context: Dict[str, Any]):
        """Apply quality gate after gap detection."""
        
        if 'gap_detection' not in context['stage_results']:
            return
        
        gap_report = context['stage_results']['gap_detection']
        gate_config = self.quality_gates['gap_detection_gate']
        
        # Check quality gate criteria
        if gap_report.critical_gaps > gate_config['critical_gaps_max']:
            context['requires_manual_review'] = True
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.MANUAL_REVIEW_REQUIRED,
                timestamp=datetime.now(),
                level=AuditLevel.WARNING,
                description=f"Critical gaps exceed threshold: {gap_report.critical_gaps} > {gate_config['critical_gaps_max']}",
                session_id=context['session_id'],
                response_id=context['request'].response_id,
                source_module='system_orchestrator'
            ))
        
        if gap_report.total_gaps > gate_config['total_gaps_max']:
            context['requires_manual_review'] = True
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.MANUAL_REVIEW_REQUIRED,
                timestamp=datetime.now(),
                level=AuditLevel.WARNING,
                description=f"Total gaps exceed threshold: {gap_report.total_gaps} > {gate_config['total_gaps_max']}",
                session_id=context['session_id'],
                response_id=context['request'].response_id,
                source_module='system_orchestrator'
            ))
    
    async def _apply_compliance_quality_gate(self, context: Dict[str, Any]):
        """Apply quality gate after compliance check."""
        
        if 'compliance_check' not in context['stage_results']:
            return
        
        compliance_report = context['stage_results']['compliance_check']
        gate_config = self.quality_gates['compliance_gate']
        
        # Check critical violations
        if compliance_report.critical_issues > gate_config['critical_violations_max']:
            context['requires_manual_review'] = True
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.MANUAL_REVIEW_REQUIRED,
                timestamp=datetime.now(),
                level=AuditLevel.WARNING,
                description=f"Critical compliance violations: {compliance_report.critical_issues}",
                session_id=context['session_id'],
                response_id=context['request'].response_id,
                source_module='system_orchestrator'
            ))
        
        # Check overall risk score
        if compliance_report.overall_risk_score > gate_config['overall_risk_score_max']:
            context['requires_manual_review'] = True
    
    async def _apply_depth_analysis_quality_gate(self, context: Dict[str, Any]):
        """Apply quality gate after depth analysis."""
        
        if 'depth_analysis' not in context['stage_results']:
            return
        
        depth_report = context['stage_results']['depth_analysis']
        gate_config = self.quality_gates['depth_gate']
        
        # Check depth score
        if depth_report.overall_depth_score < gate_config['depth_score_min']:
            context['requires_manual_review'] = True
            self.audit_logger.log_event(AuditEvent(
                event_id="",
                event_type=AuditEventType.MANUAL_REVIEW_REQUIRED,
                timestamp=datetime.now(),
                level=AuditLevel.WARNING,
                description=f"Depth score below threshold: {depth_report.overall_depth_score} < {gate_config['depth_score_min']}",
                session_id=context['session_id'],
                response_id=context['request'].response_id,
                source_module='system_orchestrator'
            ))
    
    async def _apply_risk_assessment_quality_gate(self, context: Dict[str, Any]):
        """Apply quality gate after risk assessment."""
        
        if 'risk_assessment' not in context['stage_results']:
            return
        
        risk_report = context['stage_results']['risk_assessment']
        gate_config = self.quality_gates['risk_gate']
        
        # Check overall risk score
        if risk_report.overall_risk_score > gate_config['overall_risk_score_max']:
            context['requires_manual_review'] = True
        
        # Check critical risks
        critical_risks = len([rf for rf in risk_report.risk_factors if rf.level.value >= 4])
        if critical_risks > gate_config['critical_risks_max']:
            context['requires_manual_review'] = True
    
    def _generate_final_result(self, context: Dict[str, Any], processing_start: datetime):
        """Generate final processing result."""
        
        processing_time = (datetime.now() - processing_start).total_seconds() * 1000
        request = context['request']
        
        # Calculate overall quality score
        quality_scores = [metric.score_percentage for metric in context['quality_metrics']]
        overall_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Generate recommendations
        recommendations = []
        for stage_name, stage_result in context['stage_results'].items():
            if hasattr(stage_result, 'recommendations'):
                recommendations.extend(stage_result.recommendations)
        
        # Import here to avoid circular import
        from .clara_integration import DDQProcessingResult
        
        return DDQProcessingResult(
            request_id=request.response_id,
            session_id=context['session_id'],
            original_response=request.response_text,
            processed_response=context['current_response_text'],
            modifications_made=context['modifications_made'],
            gap_report=context['stage_results'].get('gap_detection', {}).to_json() if 'gap_detection' in context['stage_results'] else {},
            compliance_report=context['stage_results'].get('compliance_check', {}).to_json() if 'compliance_check' in context['stage_results'] else {},
            depth_analysis=context['stage_results'].get('depth_analysis', {}).to_json() if 'depth_analysis' in context['stage_results'] else {},
            risk_assessment=context['stage_results'].get('risk_assessment', {}).to_json() if 'risk_assessment' in context['stage_results'] else {},
            overall_quality_score=overall_quality_score,
            processing_time_ms=int(processing_time),
            recommendations=recommendations,
            requires_manual_review=context['requires_manual_review'],
            audit_trail_id=context['session_id']
        )
    
    async def _run_gap_detection(self, context):
        """Run gap detection with proper async handling."""
        return self.gap_detector.detect_gaps(context)
    
    async def _run_compliance_check(self, context):
        """Run compliance check with proper async handling."""
        return self.compliance_checker.check_compliance(context)
    
    async def _run_depth_analysis(self, context):
        """Run depth analysis with proper async handling."""
        return self.depth_analyzer.analyze_depth(context)
    
    async def _run_risk_assessment(self, context):
        """Run risk assessment with proper async handling."""
        return self.risk_assessor.assess_risks(context)
    
    def _record_stage_performance(self, stage_name: str, duration_ms: float):
        """Record performance metrics for a processing stage."""
        
        if stage_name not in self.stage_performance:
            self.stage_performance[stage_name] = {
                'total_executions': 0,
                'total_time_ms': 0,
                'average_time_ms': 0,
                'min_time_ms': float('inf'),
                'max_time_ms': 0
            }
        
        stats = self.stage_performance[stage_name]
        stats['total_executions'] += 1
        stats['total_time_ms'] += duration_ms
        stats['average_time_ms'] = stats['total_time_ms'] / stats['total_executions']
        stats['min_time_ms'] = min(stats['min_time_ms'], duration_ms)
        stats['max_time_ms'] = max(stats['max_time_ms'], duration_ms)
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get orchestrator performance statistics."""
        
        return {
            'stage_performance': self.stage_performance,
            'processing_stages': {
                stage_name: {
                    'enabled': stage.enabled,
                    'timeout_seconds': stage.timeout_seconds,
                    'quality_threshold': stage.quality_threshold
                }
                for stage_name, stage in self.processing_stages.items()
            },
            'quality_gates': self.quality_gates
        }