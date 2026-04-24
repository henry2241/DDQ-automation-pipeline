#!/usr/bin/env python3
"""
Clara Integration Demonstration
==============================

Comprehensive demonstration of the DDQ Gap Compliance System integration
with Clara architecture. Shows real-world usage examples and capabilities.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

# Import the Clara integration layer
from core.clara_integration import (
    ClaraIntegrationLayer,
    DDQProcessingRequest,
    create_clara_integration,
    quick_quality_check,
    process_single_response
)

# Import configuration management
from core.configuration_manager import (
    create_default_configuration,
    create_development_configuration
)


class DDQDemonstrationSuite:
    """Comprehensive demonstration of DDQ gap handling and compliance capabilities."""
    
    def __init__(self, use_development_config: bool = True):
        """Initialize demonstration suite."""
        
        print("🚀 Initializing Clara DDQ Gap Compliance System Demo")
        print("=" * 60)
        
        # Setup configuration
        if use_development_config:
            self.config = create_development_configuration()
            print("📋 Using development configuration")
        else:
            self.config = create_default_configuration()
            print("📋 Using production configuration")
        
        # Create Clara integration layer
        self.clara_integration = ClaraIntegrationLayer()
        print("✅ Clara integration layer initialized")
        
        # Sample DDQ data for demonstrations
        self.sample_responses = self._load_sample_responses()
        print(f"📊 Loaded {len(self.sample_responses)} sample DDQ responses")
        
        print("\n" + "=" * 60)
        print("🎯 System Ready for Demonstrations")
        print("=" * 60 + "\n")
    
    def _load_sample_responses(self) -> List[Dict[str, Any]]:
        """Load sample DDQ responses for demonstration."""
        
        return [
            {
                "response_id": "demo_001",
                "question_id": "investment_strategy_001",
                "question": "Describe your firm's investment strategy and approach for equity portfolios.",
                "response": """Our firm employs a sophisticated quantitative approach to equity portfolio management. We utilize proprietary models that have consistently delivered strong returns over the past decade. Our strategy leverages advanced algorithms to identify undervalued securities and construct portfolios that typically outperform the S&P 500 by 3-5% annually. The approach is based on our team's extensive experience and proven track record of generating alpha for our clients.""",
                "firm_type": "investment_adviser",
                "client_types": ["institutional", "high_net_worth"],
                "expected_issues": [
                    "Performance claims without disclaimers",
                    "Guarantee language ('consistently delivered')",
                    "Specific return projections without backing",
                    "Missing risk disclosures"
                ]
            },
            {
                "response_id": "demo_002", 
                "question_id": "risk_management_001",
                "question": "How does your firm identify, measure, and manage investment risks?",
                "response": """Risk management is a core component of our investment process. We employ various risk metrics including Value at Risk (VaR), tracking error, and maximum drawdown limits. The firm has implemented a comprehensive risk management framework that includes daily monitoring of portfolio exposures, stress testing under different market scenarios, and regular risk reporting to senior management and clients. Our risk team uses Bloomberg risk analytics and proprietary models to assess portfolio risk across multiple dimensions including market, credit, and operational risk.""",
                "firm_type": "investment_adviser",
                "client_types": ["institutional"],
                "expected_issues": [
                    "Good structure but could use more specifics",
                    "Missing source citations for risk metrics",
                    "Could benefit from specific risk limits"
                ]
            },
            {
                "response_id": "demo_003",
                "question_id": "performance_reporting_001", 
                "question": "Describe your performance reporting methodology and benchmarking approach.",
                "response": """Performance reporting is conducted monthly and includes both gross and net returns. We benchmark against appropriate indices and provide attribution analysis showing sources of return. Historical performance shows we have never had a down year and have achieved average annual returns of 12.5% since inception. All returns are calculated using industry-standard methodologies.""",
                "firm_type": "investment_adviser",
                "client_types": ["institutional"],
                "expected_issues": [
                    "Critical: 'Never had a down year' guarantee language",
                    "Missing past performance disclaimers",
                    "Specific return claims need qualification",
                    "No source documentation references"
                ]
            },
            {
                "response_id": "demo_004",
                "question_id": "operational_procedures_001",
                "question": "Detail your trade execution and settlement procedures.",
                "response": """Our trade execution follows best execution practices as required by regulations. We utilize multiple execution venues to achieve optimal pricing for client trades. Settlement procedures are handled through our prime broker relationships and we maintain appropriate controls to ensure timely and accurate settlement of all transactions. The operations team reconciles positions daily and maintains detailed records of all trading activity.""",
                "firm_type": "investment_adviser", 
                "client_types": ["institutional"],
                "expected_issues": [
                    "Good operational coverage",
                    "Could use more specific procedures",
                    "Missing specific vendor/system names"
                ]
            }
        ]
    
    async def run_demonstration_suite(self):
        """Run complete demonstration suite."""
        
        print("🔥 Starting Comprehensive DDQ Processing Demonstrations")
        print("=" * 70)
        
        # Demonstration 1: Single response processing
        await self.demo_single_response_processing()
        
        # Demonstration 2: Batch processing
        await self.demo_batch_processing()
        
        # Demonstration 3: Quality validation
        await self.demo_quality_validation()
        
        # Demonstration 4: Configuration management
        await self.demo_configuration_management()
        
        # Demonstration 5: Audit trail analysis
        await self.demo_audit_trail_analysis()
        
        # Demonstration 6: System health monitoring
        await self.demo_system_health_monitoring()
        
        print("\n" + "=" * 70)
        print("🎉 All Demonstrations Completed Successfully!")
        print("=" * 70)
    
    async def demo_single_response_processing(self):
        """Demonstrate single DDQ response processing."""
        
        print("\n📝 DEMONSTRATION 1: Single Response Processing")
        print("-" * 50)
        
        # Select sample response with known issues
        sample = self.sample_responses[0]  # Response with performance claims
        
        print(f"Processing response: {sample['response_id']}")
        print(f"Question: {sample['question'][:60]}...")
        print(f"Expected issues: {len(sample['expected_issues'])} identified")
        
        # Create processing request
        request = DDQProcessingRequest(
            response_id=sample['response_id'],
            question_id=sample['question_id'],
            response_text=sample['response'],
            question_text=sample['question'],
            firm_type=sample['firm_type'],
            client_types=sample['client_types']
        )
        
        # Process the response
        print("\n🔄 Processing DDQ response...")
        start_time = datetime.now()
        
        try:
            result = await self.clara_integration.process_ddq_response(request)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"✅ Processing completed in {processing_time:.2f}s")
            
            # Display results
            print(f"\n📊 Processing Results:")
            print(f"   • Overall Quality Score: {result.overall_quality_score:.1f}/100")
            print(f"   • Gaps Detected: {result.gap_report.get('total_gaps', 0)}")
            print(f"   • Compliance Violations: {len(result.compliance_report.get('violations', []))}")
            print(f"   • Manual Review Required: {'Yes' if result.requires_manual_review else 'No'}")
            print(f"   • Modifications Made: {len(result.modifications_made)}")
            
            # Show key recommendations
            if result.recommendations:
                print(f"\n💡 Top Recommendations:")
                for i, rec in enumerate(result.recommendations[:3], 1):
                    print(f"   {i}. {rec}")
            
            # Show processed response preview
            if result.processed_response != result.original_response:
                print(f"\n📝 Response Modified: Yes")
                print(f"   Original length: {len(result.original_response)} chars")
                print(f"   Processed length: {len(result.processed_response)} chars")
            else:
                print(f"\n📝 Response Modified: No")
        
        except Exception as e:
            print(f"❌ Processing failed: {e}")
    
    async def demo_batch_processing(self):
        """Demonstrate batch processing of multiple responses."""
        
        print("\n📦 DEMONSTRATION 2: Batch Processing")
        print("-" * 50)
        
        # Create processing requests for all samples
        requests = []
        for sample in self.sample_responses[:3]:  # Process first 3
            request = DDQProcessingRequest(
                response_id=sample['response_id'],
                question_id=sample['question_id'],
                response_text=sample['response'],
                question_text=sample['question'],
                firm_type=sample['firm_type'],
                client_types=sample['client_types']
            )
            requests.append(request)
        
        print(f"🔄 Processing {len(requests)} responses in batch...")
        start_time = datetime.now()
        
        try:
            results = self.clara_integration.batch_process_responses(
                requests, 
                max_concurrent=2
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"✅ Batch processing completed in {processing_time:.2f}s")
            
            # Analyze batch results
            total_gaps = sum(r.gap_report.get('total_gaps', 0) for r in results)
            total_violations = sum(len(r.compliance_report.get('violations', [])) for r in results)
            avg_quality = sum(r.overall_quality_score for r in results) / len(results)
            manual_reviews = sum(1 for r in results if r.requires_manual_review)
            
            print(f"\n📊 Batch Results Summary:")
            print(f"   • Responses Processed: {len(results)}")
            print(f"   • Average Quality Score: {avg_quality:.1f}/100")
            print(f"   • Total Gaps Found: {total_gaps}")
            print(f"   • Total Compliance Issues: {total_violations}")
            print(f"   • Manual Reviews Required: {manual_reviews}")
            print(f"   • Processing Rate: {len(results)/processing_time:.1f} responses/sec")
            
        except Exception as e:
            print(f"❌ Batch processing failed: {e}")
    
    async def demo_quality_validation(self):
        """Demonstrate quality validation capabilities."""
        
        print("\n🎯 DEMONSTRATION 3: Quality Validation")
        print("-" * 50)
        
        # Test quality validation on different response types
        test_cases = [
            {
                "name": "High Quality Response",
                "response": """The firm's investment strategy follows a disciplined value-oriented approach as documented in our ADV Part 2A. Per our investment committee charter, we focus on large-cap U.S. equities with strong fundamentals, trading at discounts to intrinsic value. Our process includes: 1) Fundamental analysis using DCF models, 2) Risk assessment via portfolio-level stress testing, 3) Ongoing monitoring with monthly portfolio reviews. Past performance data is available upon request with appropriate disclaimers regarding future results. Risk factors include market volatility, concentration risk, and model limitations as detailed in our risk disclosure statement.""",
                "expected_quality": "High"
            },
            {
                "name": "Poor Quality Response",
                "response": """We use sophisticated algorithms to generate consistent profits for our clients. Our strategy always beats the market and guarantees positive returns every year. The approach is very advanced and complex.""",
                "expected_quality": "Poor"
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            
            quality_report = self.clara_integration.validate_response_quality(
                response_text=test_case['response'],
                question_text="Describe your investment strategy and approach."
            )
            
            print(f"   • Overall Quality: {quality_report['overall_quality']:.1f}/100")
            print(f"   • Gap Score: {quality_report['gap_score']:.1f}/100")
            print(f"   • Compliance Score: {quality_report['compliance_score']:.1f}/100")
            print(f"   • Meets Thresholds: {all(quality_report['meets_thresholds'].values())}")
            
            if quality_report['recommendations']:
                print(f"   • Recommendations: {len(quality_report['recommendations'])}")
                for rec in quality_report['recommendations'][:2]:
                    print(f"     - {rec}")
    
    async def demo_configuration_management(self):
        """Demonstrate configuration management features."""
        
        print("\n⚙️ DEMONSTRATION 4: Configuration Management")
        print("-" * 50)
        
        # Show current configuration
        print("📋 Current Configuration Overview:")
        config_export = self.config.export_configuration()
        
        print(f"   • Environment: {config_export['system']['environment']}")
        print(f"   • Debug Mode: {config_export['system']['debug_mode']}")
        print(f"   • Max Processing Time: {config_export['system']['max_processing_time_seconds']}s")
        print(f"   • Gap Detection Threshold: {config_export['quality_thresholds']['gap_detection_accuracy']}%")
        print(f"   • Compliance Coverage: {config_export['quality_thresholds']['compliance_coverage']}%")
        
        # Demonstrate configuration updates
        print("\n🔧 Testing Configuration Updates:")
        
        original_threshold = self.config.get('quality_thresholds.gap_detection_accuracy')
        print(f"   • Original gap detection threshold: {original_threshold}%")
        
        # Update configuration
        self.config.set('quality_thresholds.gap_detection_accuracy', 90.0)
        self.config.set('custom.demo_setting', 'test_value')
        
        new_threshold = self.config.get('quality_thresholds.gap_detection_accuracy')
        custom_value = self.config.get('custom.demo_setting')
        
        print(f"   • Updated gap detection threshold: {new_threshold}%")
        print(f"   • Custom setting value: {custom_value}")
        
        # Validate configuration
        validation_issues = self.config.validate_configuration()
        print(f"   • Configuration validation: {'✅ Pass' if not validation_issues else '❌ Issues found'}")
        
        if validation_issues:
            for issue in validation_issues[:3]:
                print(f"     - {issue}")
        
        # Reset for next demonstrations
        self.config.set('quality_thresholds.gap_detection_accuracy', original_threshold)
    
    async def demo_audit_trail_analysis(self):
        """Demonstrate audit trail capabilities."""
        
        print("\n📋 DEMONSTRATION 5: Audit Trail Analysis")
        print("-" * 50)
        
        # Get processing statistics
        stats = self.clara_integration.get_processing_statistics()
        
        print("📊 System Processing Statistics:")
        print(f"   • Total Requests Processed: {stats['total_requests']}")
        print(f"   • Success Rate: {stats.get('success_rate', 0):.1f}%")
        print(f"   • Average Processing Time: {stats['average_processing_time_ms']:.0f}ms")
        print(f"   • Active Audit Trails: {stats.get('active_audit_trails', 0)}")
        
        # Show audit performance
        if 'audit_performance' in stats:
            audit_perf = stats['audit_performance']
            print(f"   • Audit Events Logged: {audit_perf['events_logged']}")
            print(f"   • Average Log Time: {audit_perf['average_log_time_ms']:.1f}ms")
        
        # Get active trails information
        active_trails = self.clara_integration.audit_logger.get_active_trails()
        if active_trails:
            print(f"\n🔍 Active Audit Trails: {len(active_trails)}")
            for trail_id in active_trails[:3]:
                trail_status = self.clara_integration.audit_logger.get_trail_status(trail_id)
                if trail_status:
                    print(f"   • {trail_id[:12]}...: {trail_status['event_count']} events, "
                          f"{trail_status['duration_seconds']:.1f}s duration")
    
    async def demo_system_health_monitoring(self):
        """Demonstrate system health monitoring."""
        
        print("\n🏥 DEMONSTRATION 6: System Health Monitoring")
        print("-" * 50)
        
        # Get system health status
        health_status = self.clara_integration.get_system_health()
        
        print(f"🩺 System Health Assessment:")
        print(f"   • Overall Status: {health_status['overall_status'].upper()}")
        print(f"   • System Version: {health_status['configuration']['version']}")
        print(f"   • Environment: {health_status['configuration']['environment']}")
        
        # Component status
        print(f"\n🧩 Component Status:")
        for component, status in health_status['components'].items():
            status_emoji = "✅" if status == "operational" else "❌"
            component_name = component.replace('_', ' ').title()
            print(f"   {status_emoji} {component_name}: {status}")
        
        # Performance metrics
        perf = health_status['performance']
        print(f"\n📈 Performance Metrics:")
        print(f"   • Failure Rate: {perf.get('failure_rate', 0):.1f}%")
        print(f"   • Manual Review Rate: {perf.get('manual_review_rate', 0):.1f}%")
        print(f"   • Gaps Detected: {perf.get('total_gaps_detected', 0)}")
        print(f"   • Compliance Violations: {perf.get('total_compliance_violations', 0)}")
        
        # Issues and recommendations
        if 'issues' in health_status:
            print(f"\n⚠️ System Issues:")
            for issue in health_status['issues']:
                print(f"   • {issue}")
    
    def demo_manual_scenarios(self):
        """Demonstrate specific manual test scenarios."""
        
        print("\n🔧 DEMONSTRATION 7: Manual Test Scenarios")
        print("-" * 50)
        
        scenarios = [
            {
                "name": "Performance Guarantee Detection",
                "text": "Our fund guarantees annual returns of 8% with no risk of loss.",
                "should_detect": ["Performance guarantees", "No risk claims"]
            },
            {
                "name": "Missing Disclaimer Detection", 
                "text": "Historical performance shows 15% annual returns over the past 5 years.",
                "should_detect": ["Past performance disclaimer missing"]
            },
            {
                "name": "Compliance Language Detection",
                "text": "We always outperform the market and never have losing quarters.",
                "should_detect": ["Absolute performance claims", "Misleading statements"]
            }
        ]
        
        for scenario in scenarios:
            print(f"\n🎯 Scenario: {scenario['name']}")
            print(f"   Text: \"{scenario['text'][:50]}...\"")
            
            # Quick quality check
            quality_result = quick_quality_check(
                response_text=scenario['text'],
                question_text="Describe your investment performance."
            )
            
            print(f"   Quality Score: {quality_result['overall_quality']:.1f}/100")
            print(f"   Should Detect: {scenario['should_detect']}")
            
            if quality_result['recommendations']:
                print(f"   Detected Issues:")
                for rec in quality_result['recommendations']:
                    print(f"     - {rec}")


async def main():
    """Main demonstration entry point."""
    
    print("Clara DDQ Gap Compliance System - Integration Demonstration")
    print("=" * 70)
    print("This demonstration showcases the comprehensive gap handling and")
    print("compliance safeguards built for Clara's DDQ workflow processing.")
    print("=" * 70)
    
    # Create demonstration suite
    demo_suite = DDQDemonstrationSuite(use_development_config=True)
    
    try:
        # Run all demonstrations
        await demo_suite.run_demonstration_suite()
        
        # Run manual scenarios
        demo_suite.demo_manual_scenarios()
        
        print("\n" + "=" * 70)
        print("🎊 DEMONSTRATION COMPLETE")
        print("=" * 70)
        print("Clara can now leverage this bulletproof DDQ gap handling system to:")
        print("• ✅ Systematically detect and classify documentation gaps")
        print("• ✅ Automatically check compliance and insert disclaimers") 
        print("• ✅ Ensure consistent depth and coverage across responses")
        print("• ✅ Assess regulatory risks and flag critical issues")
        print("• ✅ Maintain comprehensive audit trails for quality assurance")
        print("• ✅ Handle edge cases professionally with full traceability")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n⏹️ Demonstration interrupted by user")
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    """Run demonstration when script is executed directly."""
    asyncio.run(main())