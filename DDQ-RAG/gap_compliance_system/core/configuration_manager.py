"""
Configuration Manager
====================

Centralized configuration management for DDQ gap detection and compliance system.
Handles system settings, thresholds, and environment-specific configurations.
"""

import json
try:
    import yaml
except ImportError:
    yaml = None
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import os


@dataclass
class SystemConfiguration:
    """System-wide configuration settings."""
    
    version: str = "1.0.0"
    environment: str = "production"  # production, staging, development
    debug_mode: bool = False
    max_processing_time_seconds: int = 300
    max_concurrent_requests: int = 10


@dataclass
class QualityThresholds:
    """Quality assurance thresholds."""
    
    gap_detection_accuracy: float = 85.0
    compliance_coverage: float = 95.0
    depth_score_minimum: float = 70.0
    risk_score_maximum: float = 25.0
    consistency_score_minimum: float = 75.0


@dataclass
class ProcessingStages:
    """Processing stage configurations."""
    
    gap_detection_enabled: bool = True
    gap_detection_timeout: int = 30
    gap_detection_retries: int = 2
    
    compliance_check_enabled: bool = True
    compliance_check_timeout: int = 40
    compliance_check_retries: int = 3
    
    depth_analysis_enabled: bool = True
    depth_analysis_timeout: int = 45
    depth_analysis_retries: int = 2
    
    risk_assessment_enabled: bool = True
    risk_assessment_timeout: int = 35
    risk_assessment_retries: int = 2
    
    disclaimer_insertion_enabled: bool = True
    disclaimer_insertion_timeout: int = 20
    disclaimer_insertion_retries: int = 2


@dataclass
class AuditSettings:
    """Audit and logging configuration."""
    
    log_directory: str = "/tmp/ddq_audit_logs"
    retention_days: int = 90
    max_file_size_mb: int = 50
    enable_console_output: bool = True
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # Performance tracking
    enable_performance_monitoring: bool = True
    track_processing_times: bool = True
    track_quality_metrics: bool = True


@dataclass
class ComplianceSettings:
    """Compliance checking configuration."""
    
    # Risk scoring
    critical_violation_weight: float = 25.0
    high_violation_weight: float = 15.0
    medium_violation_weight: float = 8.0
    low_violation_weight: float = 3.0
    
    # Grade thresholds
    compliance_grade_a_max: float = 5.0
    compliance_grade_b_max: float = 15.0
    compliance_grade_c_max: float = 30.0
    compliance_grade_d_max: float = 50.0
    
    # Auto-fix settings
    enable_auto_fix: bool = True
    auto_insert_disclaimers: bool = True
    max_auto_fixes_per_response: int = 10


class ConfigurationManager:
    """
    Centralized configuration management system.
    
    Features:
    - Environment-specific configurations
    - Runtime configuration updates
    - Configuration validation
    - Default value management
    - Configuration persistence
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager."""
        
        self.config_path = Path(config_path) if config_path else None
        
        # Initialize with default configurations
        self.system_config = SystemConfiguration()
        self.quality_thresholds = QualityThresholds()
        self.processing_stages = ProcessingStages()
        self.audit_settings = AuditSettings()
        self.compliance_settings = ComplianceSettings()
        
        # Custom configuration overrides
        self.custom_config = {}
        
        # Load configuration from file if provided
        if self.config_path and self.config_path.exists():
            self.load_configuration()
        
        # Apply environment variable overrides
        self._apply_environment_overrides()
    
    def load_configuration(self, config_path: Optional[str] = None):
        """Load configuration from file."""
        
        if config_path:
            self.config_path = Path(config_path)
        
        if not self.config_path or not self.config_path.exists():
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.yaml' or self.config_path.suffix.lower() == '.yml':
                    if yaml is None:
                        raise ImportError("PyYAML not installed, use JSON configuration")
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            # Update configuration objects
            self._update_config_from_dict(config_data)
            
        except Exception as e:
            print(f"Warning: Failed to load configuration from {self.config_path}: {e}")
    
    def save_configuration(self, config_path: Optional[str] = None):
        """Save current configuration to file."""
        
        if config_path:
            self.config_path = Path(config_path)
        
        if not self.config_path:
            raise ValueError("No configuration path specified")
        
        # Create directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare configuration data
        config_data = {
            'system': asdict(self.system_config),
            'quality_thresholds': asdict(self.quality_thresholds),
            'processing_stages': asdict(self.processing_stages),
            'audit_settings': asdict(self.audit_settings),
            'compliance_settings': asdict(self.compliance_settings),
            'custom': self.custom_config,
            'metadata': {
                'version': self.system_config.version,
                'last_updated': datetime.now().isoformat(),
                'environment': self.system_config.environment
            }
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.yaml' or self.config_path.suffix.lower() == '.yml':
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_data, f, indent=2)
                    
        except Exception as e:
            print(f"Error: Failed to save configuration to {self.config_path}: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Examples:
            config.get('system.version')
            config.get('quality_thresholds.gap_detection_accuracy')
            config.get('processing_stages.gap_detection_timeout')
        """
        
        parts = key.split('.')
        
        # Check system configuration
        if parts[0] == 'system':
            return self._get_nested_value(asdict(self.system_config), parts[1:], default)
        
        # Check quality thresholds
        elif parts[0] == 'quality_thresholds' or parts[0] == 'quality':
            return self._get_nested_value(asdict(self.quality_thresholds), parts[1:], default)
        
        # Check processing stages
        elif parts[0] == 'processing_stages' or parts[0] == 'stages':
            return self._get_nested_value(asdict(self.processing_stages), parts[1:], default)
        
        # Check audit settings
        elif parts[0] == 'audit_settings' or parts[0] == 'audit' or parts[0] == 'logging':
            return self._get_nested_value(asdict(self.audit_settings), parts[1:], default)
        
        # Check compliance settings
        elif parts[0] == 'compliance_settings' or parts[0] == 'compliance':
            return self._get_nested_value(asdict(self.compliance_settings), parts[1:], default)
        
        # Check custom configuration
        elif parts[0] == 'custom':
            return self._get_nested_value(self.custom_config, parts[1:], default)
        
        # Direct key lookup in custom config
        else:
            return self._get_nested_value(self.custom_config, parts, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation."""
        
        parts = key.split('.')
        
        # Set in system configuration
        if parts[0] == 'system':
            self._set_nested_value(self.system_config, parts[1:], value)
        
        # Set in quality thresholds
        elif parts[0] == 'quality_thresholds' or parts[0] == 'quality':
            self._set_nested_value(self.quality_thresholds, parts[1:], value)
        
        # Set in processing stages
        elif parts[0] == 'processing_stages' or parts[0] == 'stages':
            self._set_nested_value(self.processing_stages, parts[1:], value)
        
        # Set in audit settings
        elif parts[0] == 'audit_settings' or parts[0] == 'audit' or parts[0] == 'logging':
            self._set_nested_value(self.audit_settings, parts[1:], value)
        
        # Set in compliance settings
        elif parts[0] == 'compliance_settings' or parts[0] == 'compliance':
            self._set_nested_value(self.compliance_settings, parts[1:], value)
        
        # Set in custom configuration
        else:
            self._set_nested_value_dict(self.custom_config, parts, value)
    
    def update_configuration(self, updates: Dict[str, Any]):
        """Update multiple configuration values."""
        
        for key, value in updates.items():
            self.set(key, value)
    
    def validate_configuration(self) -> List[str]:
        """Validate current configuration and return list of issues."""
        
        issues = []
        
        # Validate system configuration
        if self.system_config.max_processing_time_seconds <= 0:
            issues.append("system.max_processing_time_seconds must be positive")
        
        if self.system_config.max_concurrent_requests <= 0:
            issues.append("system.max_concurrent_requests must be positive")
        
        # Validate quality thresholds
        if not (0 <= self.quality_thresholds.gap_detection_accuracy <= 100):
            issues.append("quality_thresholds.gap_detection_accuracy must be between 0-100")
        
        if not (0 <= self.quality_thresholds.compliance_coverage <= 100):
            issues.append("quality_thresholds.compliance_coverage must be between 0-100")
        
        if not (0 <= self.quality_thresholds.depth_score_minimum <= 100):
            issues.append("quality_thresholds.depth_score_minimum must be between 0-100")
        
        if not (0 <= self.quality_thresholds.risk_score_maximum <= 100):
            issues.append("quality_thresholds.risk_score_maximum must be between 0-100")
        
        # Validate processing stage timeouts
        stage_timeouts = [
            ('gap_detection_timeout', self.processing_stages.gap_detection_timeout),
            ('compliance_check_timeout', self.processing_stages.compliance_check_timeout),
            ('depth_analysis_timeout', self.processing_stages.depth_analysis_timeout),
            ('risk_assessment_timeout', self.processing_stages.risk_assessment_timeout),
            ('disclaimer_insertion_timeout', self.processing_stages.disclaimer_insertion_timeout)
        ]
        
        for name, timeout in stage_timeouts:
            if timeout <= 0:
                issues.append(f"processing_stages.{name} must be positive")
            elif timeout > self.system_config.max_processing_time_seconds:
                issues.append(f"processing_stages.{name} cannot exceed max_processing_time_seconds")
        
        # Validate audit settings
        if self.audit_settings.retention_days <= 0:
            issues.append("audit_settings.retention_days must be positive")
        
        if self.audit_settings.max_file_size_mb <= 0:
            issues.append("audit_settings.max_file_size_mb must be positive")
        
        # Validate compliance settings
        if self.compliance_settings.max_auto_fixes_per_response <= 0:
            issues.append("compliance_settings.max_auto_fixes_per_response must be positive")
        
        return issues
    
    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration."""
        
        env = self.system_config.environment.lower()
        
        base_config = {
            'debug_mode': False,
            'enable_console_output': True,
            'max_concurrent_requests': 10
        }
        
        if env == 'development':
            base_config.update({
                'debug_mode': True,
                'log_level': 'DEBUG',
                'enable_console_output': True,
                'max_concurrent_requests': 3
            })
        
        elif env == 'staging':
            base_config.update({
                'debug_mode': False,
                'log_level': 'INFO',
                'enable_console_output': True,
                'max_concurrent_requests': 5
            })
        
        elif env == 'production':
            base_config.update({
                'debug_mode': False,
                'log_level': 'WARNING',
                'enable_console_output': False,
                'max_concurrent_requests': 10
            })
        
        return base_config
    
    def reset_to_defaults(self):
        """Reset all configuration to default values."""
        
        self.system_config = SystemConfiguration()
        self.quality_thresholds = QualityThresholds()
        self.processing_stages = ProcessingStages()
        self.audit_settings = AuditSettings()
        self.compliance_settings = ComplianceSettings()
        self.custom_config = {}
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export complete configuration as dictionary."""
        
        return {
            'system': asdict(self.system_config),
            'quality_thresholds': asdict(self.quality_thresholds),
            'processing_stages': asdict(self.processing_stages),
            'audit_settings': asdict(self.audit_settings),
            'compliance_settings': asdict(self.compliance_settings),
            'custom': self.custom_config
        }
    
    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration objects from dictionary data."""
        
        # Update system configuration
        if 'system' in config_data:
            for key, value in config_data['system'].items():
                if hasattr(self.system_config, key):
                    setattr(self.system_config, key, value)
        
        # Update quality thresholds
        if 'quality_thresholds' in config_data:
            for key, value in config_data['quality_thresholds'].items():
                if hasattr(self.quality_thresholds, key):
                    setattr(self.quality_thresholds, key, value)
        
        # Update processing stages
        if 'processing_stages' in config_data:
            for key, value in config_data['processing_stages'].items():
                if hasattr(self.processing_stages, key):
                    setattr(self.processing_stages, key, value)
        
        # Update audit settings
        if 'audit_settings' in config_data:
            for key, value in config_data['audit_settings'].items():
                if hasattr(self.audit_settings, key):
                    setattr(self.audit_settings, key, value)
        
        # Update compliance settings
        if 'compliance_settings' in config_data:
            for key, value in config_data['compliance_settings'].items():
                if hasattr(self.compliance_settings, key):
                    setattr(self.compliance_settings, key, value)
        
        # Update custom configuration
        if 'custom' in config_data:
            self.custom_config.update(config_data['custom'])
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides."""
        
        # System overrides
        if os.getenv('DDQ_ENVIRONMENT'):
            self.system_config.environment = os.getenv('DDQ_ENVIRONMENT')
        
        if os.getenv('DDQ_DEBUG_MODE'):
            self.system_config.debug_mode = os.getenv('DDQ_DEBUG_MODE').lower() == 'true'
        
        if os.getenv('DDQ_MAX_PROCESSING_TIME'):
            self.system_config.max_processing_time_seconds = int(os.getenv('DDQ_MAX_PROCESSING_TIME'))
        
        # Audit overrides
        if os.getenv('DDQ_LOG_DIRECTORY'):
            self.audit_settings.log_directory = os.getenv('DDQ_LOG_DIRECTORY')
        
        if os.getenv('DDQ_LOG_LEVEL'):
            self.audit_settings.log_level = os.getenv('DDQ_LOG_LEVEL')
        
        if os.getenv('DDQ_RETENTION_DAYS'):
            self.audit_settings.retention_days = int(os.getenv('DDQ_RETENTION_DAYS'))
        
        # Apply environment-specific defaults
        env_config = self.get_environment_config()
        for key, value in env_config.items():
            if hasattr(self.system_config, key):
                setattr(self.system_config, key, value)
            elif hasattr(self.audit_settings, key):
                setattr(self.audit_settings, key, value)
    
    def _get_nested_value(self, obj: Dict[str, Any], keys: List[str], default: Any) -> Any:
        """Get nested dictionary value."""
        
        current = obj
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def _set_nested_value(self, obj: Any, keys: List[str], value: Any):
        """Set nested value in dataclass object."""
        
        if not keys:
            return
        
        if len(keys) == 1:
            if hasattr(obj, keys[0]):
                setattr(obj, keys[0], value)
        else:
            # For now, just handle direct attributes
            if hasattr(obj, keys[0]):
                setattr(obj, keys[0], value)
    
    def _set_nested_value_dict(self, obj: Dict[str, Any], keys: List[str], value: Any):
        """Set nested value in dictionary."""
        
        current = obj
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value


# Default configuration factory
def create_default_configuration() -> ConfigurationManager:
    """Create configuration manager with production defaults."""
    
    config = ConfigurationManager()
    
    # Set production-ready defaults
    config.system_config.environment = "production"
    config.system_config.debug_mode = False
    
    config.audit_settings.enable_console_output = False
    config.audit_settings.log_level = "INFO"
    
    config.compliance_settings.enable_auto_fix = True
    config.compliance_settings.auto_insert_disclaimers = True
    
    return config


# Development configuration factory
def create_development_configuration() -> ConfigurationManager:
    """Create configuration manager with development defaults."""
    
    config = ConfigurationManager()
    
    # Set development-friendly defaults
    config.system_config.environment = "development"
    config.system_config.debug_mode = True
    
    config.audit_settings.enable_console_output = True
    config.audit_settings.log_level = "DEBUG"
    config.audit_settings.log_directory = "/tmp/ddq_dev_logs"
    
    config.processing_stages.gap_detection_timeout = 60  # Longer timeouts for debugging
    config.processing_stages.compliance_check_timeout = 60
    
    return config