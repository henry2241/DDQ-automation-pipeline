# DDQ Gap Compliance System Configuration

This directory contains configuration files for the DDQ Gap Compliance System used by Clara for bulletproof DDQ processing.

## Configuration Files

### `production.json`
- **Environment**: Production
- **Debug Mode**: Disabled
- **Log Level**: INFO
- **Quality Thresholds**: Strict (85%+ accuracy required)
- **Processing Timeouts**: Optimized for performance
- **Audit Logging**: Full retention (90 days)
- **Disclaimer Insertion**: Automatic and comprehensive

### `development.json`
- **Environment**: Development  
- **Debug Mode**: Enabled
- **Log Level**: DEBUG
- **Quality Thresholds**: Relaxed (75%+ accuracy)
- **Processing Timeouts**: Extended for debugging
- **Audit Logging**: Reduced retention (30 days)
- **Additional Features**: Detailed logging, intermediate result saving

## Configuration Sections

### System Settings
- Environment configuration (production/development/staging)
- Processing timeouts and concurrency limits
- Debug mode and performance monitoring

### Quality Thresholds
- Gap detection accuracy requirements
- Compliance coverage minimums
- Depth analysis score targets
- Risk score maximums

### Processing Stages
- Enable/disable individual processing modules
- Timeout settings for each stage
- Retry policies for failed operations

### Audit Settings
- Log directory and retention policies
- Console output configuration
- Performance monitoring options

### Compliance Settings
- Violation severity weights
- Compliance grade thresholds
- Auto-fix capabilities
- Disclaimer insertion policies

### Custom Configuration
- Regulatory framework priorities
- Firm-specific defaults
- Tuning parameters for detection algorithms
- Risk assessment weights

## Environment Variables

The system supports environment variable overrides:

```bash
export DDQ_ENVIRONMENT=production
export DDQ_LOG_DIRECTORY=/var/log/clara/ddq
export DDQ_DEBUG_MODE=false
export DDQ_LOG_LEVEL=INFO
```

## Usage Examples

### Loading Configuration
```python
from core.configuration_manager import ConfigurationManager

# Load production configuration
config = ConfigurationManager('config/production.json')

# Load development configuration  
config = ConfigurationManager('config/development.json')

# Use default configuration
config = ConfigurationManager()
```

### Accessing Configuration Values
```python
# Get system settings
environment = config.get('system.environment')
debug_mode = config.get('system.debug_mode')

# Get quality thresholds
gap_threshold = config.get('quality_thresholds.gap_detection_accuracy')
compliance_threshold = config.get('quality_thresholds.compliance_coverage')

# Get custom settings
firm_type = config.get('custom.firm_defaults.default_firm_type')
```

### Updating Configuration
```python
# Update individual settings
config.set('quality_thresholds.gap_detection_accuracy', 90.0)
config.set('custom.firm_specific.client_focus', 'retail')

# Batch updates
updates = {
    'system.max_concurrent_requests': 20,
    'audit_settings.retention_days': 180,
    'custom.priority_framework': 'SEC_FIDUCIARY'
}
config.update_configuration(updates)

# Save changes
config.save_configuration('config/custom.json')
```

## Configuration Validation

The system automatically validates configuration values:

```python
# Check for configuration issues
issues = config.validate_configuration()

if issues:
    print("Configuration issues found:")
    for issue in issues:
        print(f"  - {issue}")
```

## Best Practices

1. **Production Deployment**: Always use `production.json` for live systems
2. **Development**: Use `development.json` for testing and debugging  
3. **Custom Configurations**: Create environment-specific files as needed
4. **Environment Variables**: Use for sensitive or deployment-specific settings
5. **Validation**: Always validate configuration before system startup
6. **Backup**: Keep configuration backups for rollback capability

## Security Considerations

- Store sensitive configuration values in environment variables
- Use appropriate file permissions (644 for config files)
- Avoid committing secrets to version control
- Regularly review and update configuration settings
- Monitor configuration changes through audit logs

## Troubleshooting

### Common Issues

1. **File Not Found**: Ensure configuration file exists and path is correct
2. **Validation Errors**: Check configuration values against validation rules
3. **Permission Denied**: Verify file permissions and directory access
4. **Environment Override**: Check environment variables aren't overriding settings unexpectedly

### Debug Steps

1. Enable debug mode: `DDQ_DEBUG_MODE=true`
2. Check system health: Use `get_system_health()` API
3. Review audit logs: Check processing statistics
4. Validate configuration: Run `validate_configuration()` 

## Support

For configuration support and questions:
- Review system documentation
- Check audit logs for configuration-related errors
- Use development mode for troubleshooting
- Consult Clara integration examples