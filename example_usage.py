#!/usr/bin/env python3
"""
SRE Copilot - Example Usage Script
==================================

This script demonstrates how to use the SRE Copilot system for different
incident response scenarios.
"""

import os
import json
from dotenv import load_dotenv
from sre_copilot import SRECopilot


def setup_environment():
    """Load environment variables from .env file."""
    load_dotenv()
    
    # Check for at least one LLM provider
    openai_key = os.getenv('OPENAI_API_KEY')
    gemini_key = os.getenv('GOOGLE_API_KEY')
    
    if not openai_key and not gemini_key:
        print("❌ No LLM providers configured!")
        print("Please set at least one of: OPENAI_API_KEY or GOOGLE_API_KEY")
        print("Copy .env.example to .env and fill in your values.")
        return False
    
    print("🧠 Available LLM providers:")
    if openai_key:
        print("   ✅ OpenAI")
    if gemini_key:
        print("   ✅ Google Gemini Pro")
    
    return True


def example_1_basic_alert_response():
    """Example 1: Basic alert response workflow."""
    print("\n" + "="*60)
    print("📋 EXAMPLE 1: Basic Alert Response")
    print("="*60)
    
    try:
        # Initialize SRE Copilot
        sre_copilot = SRECopilot()
        
        # Run incident response with basic context
        result = sre_copilot.run_incident_response(
            incident_context="Check for high priority alerts and investigate any issues"
        )
        
        print("\n✅ Basic alert response completed!")
        print("📊 Result:", result)
        
    except Exception as e:
        print(f"❌ Example 1 failed: {e}")


def example_2_specific_service_investigation():
    """Example 2: Investigate specific service issues."""
    print("\n" + "="*60)
    print("📋 EXAMPLE 2: Specific Service Investigation")
    print("="*60)
    
    try:
        sre_copilot = SRECopilot()
        
        # Simulate investigating a specific service
        result = sre_copilot.run_incident_response(
            incident_context=json.dumps({
                "service": "checkout-service",
                "environment": "production",
                "alert_type": "high_error_rate",
                "description": "Investigate high error rate in checkout service"
            })
        )
        
        print("\n✅ Service investigation completed!")
        print("📊 Result:", result)
        
    except Exception as e:
        print(f"❌ Example 2 failed: {e}")


def example_3_manual_incident_creation():
    """Example 3: Manual incident creation and response."""
    print("\n" + "="*60)
    print("📋 EXAMPLE 3: Manual Incident Creation")
    print("="*60)
    
    try:
        sre_copilot = SRECopilot()
        
        # Simulate manual incident report
        incident_data = {
            "title": "Database Connection Pool Exhaustion",
            "severity": "P1",
            "affected_services": ["user-service", "order-service"],
            "reported_by": "DevOps Team",
            "initial_symptoms": "Users unable to log in, orders failing",
            "namespace": "production"
        }
        
        result = sre_copilot.run_incident_response(
            incident_context=json.dumps(incident_data)
        )
        
        print("\n✅ Manual incident response completed!")
        print("📊 Result:", result)
        
    except Exception as e:
        print(f"❌ Example 3 failed: {e}")


def example_4_system_status_check():
    """Example 4: System status and crew information."""
    print("\n" + "="*60)
    print("📋 EXAMPLE 4: System Status Check")
    print("="*60)
    
    try:
        sre_copilot = SRECopilot()
        
        # Get system status
        status = sre_copilot.get_crew_status()
        
        print("🤖 SRE Copilot System Status:")
        print(f"   • Agents: {status['agents_count']}")
        print(f"   • Tasks: {status['tasks_count']}")
        print(f"   • Tools Available: {', '.join(status['tools_available'])}")
        print(f"   • Process Type: {status['process']}")
        print(f"   • Memory Enabled: {status['memory_enabled']}")
        
        # Show configuration summary
        print("\n📋 Configuration Summary:")
        print(f"   • Config file loaded: {'✅' if hasattr(sre_copilot, 'config') else '❌'}")
        
    except Exception as e:
        print(f"❌ Example 4 failed: {e}")


def example_5_llm_provider_comparison():
    """Example 5: Compare different LLM providers."""
    print("\n" + "="*60)
    print("🧠 EXAMPLE 5: LLM Provider Comparison")
    print("="*60)
    
    from llm_factory import LLMFactory
    
    available_providers = LLMFactory.get_available_providers()
    
    if len(available_providers) < 2:
        print("\n⚠️  Only one LLM provider available. Configure both OpenAI and Gemini to compare.")
        return
    
    print(f"\n📊 Comparing providers: {available_providers}")
    
    test_context = "Check for high priority alerts in production environment"
    
    for provider in available_providers:
        print(f"\n--- Testing {provider.upper()} ---")
        try:
            sre_copilot = SRECopilot(llm_provider=provider)
            result = sre_copilot.run_incident_response(incident_context=test_context)
            print(f"✅ {provider.upper()} completed successfully")
            print(f"Result preview: {str(result)[:200]}...")
        except Exception as e:
            print(f"❌ {provider.upper()} failed: {e}")


def interactive_mode():
    """Interactive mode for testing different scenarios."""
    print("\n" + "="*60)
    print("🔄 INTERACTIVE MODE")
    print("="*60)
    
    # Ask user which LLM provider to use
    from llm_factory import LLMFactory
    available_providers = LLMFactory.get_available_providers()
    
    if len(available_providers) > 1:
        print(f"\nAvailable LLM providers: {available_providers}")
        provider_choice = input(f"Choose provider ({'/'.join(available_providers)}) or press Enter for default: ").strip().lower()
        if provider_choice not in available_providers and provider_choice != "":
            print("Invalid choice, using default provider.")
            provider_choice = None
    else:
        provider_choice = None
    
    try:
        sre_copilot = SRECopilot(llm_provider=provider_choice)
        
        while True:
            print("\nAvailable commands:")
            print("1. Run basic alert check")
            print("2. Investigate custom incident")
            print("3. Show system status")
            print("4. Switch LLM provider")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                context = "Check for any active P1 or P2 alerts"
                result = sre_copilot.run_incident_response(context)
                print(f"\n📊 Result: {result}")
                
            elif choice == '2':
                service = input("Service name: ").strip()
                issue = input("Issue description: ").strip()
                
                context = json.dumps({
                    "service": service,
                    "issue": issue,
                    "manual_report": True
                })
                
                result = sre_copilot.run_incident_response(context)
                print(f"\n📊 Result: {result}")
                
            elif choice == '3':
                status = sre_copilot.get_crew_status()
                print(f"\n📊 System Status: {json.dumps(status, indent=2)}")
                
            elif choice == '4':
                # Switch LLM provider
                if len(available_providers) > 1:
                    print(f"\nCurrent provider: {sre_copilot.llm_provider or 'default'}")
                    new_provider = input(f"Choose new provider ({'/'.join(available_providers)}): ").strip().lower()
                    if new_provider in available_providers:
                        try:
                            sre_copilot = SRECopilot(llm_provider=new_provider)
                            print(f"✅ Switched to {new_provider}")
                        except Exception as e:
                            print(f"❌ Failed to switch provider: {e}")
                    else:
                        print("❌ Invalid provider choice")
                else:
                    print("⚠️  Only one provider available")
                
            elif choice == '5':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please try again.")
                
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"❌ Interactive mode failed: {e}")


def main():
    """Main function to run examples."""
    print("🚀 SRE Copilot - Example Usage")
    print("=" * 60)
    
    # Setup environment
    if not setup_environment():
        return
    
    # Run examples
    try:
        example_4_system_status_check()  # Always start with status check
        example_1_basic_alert_response()
        example_2_specific_service_investigation()
        example_3_manual_incident_creation()
        
        # Run LLM comparison if multiple providers are available
        from llm_factory import LLMFactory
        if len(LLMFactory.get_available_providers()) > 1:
            if input("\n🧠 Would you like to compare LLM providers? (y/N): ").lower().startswith('y'):
                example_5_llm_provider_comparison()
        
        # Ask if user wants interactive mode
        if input("\n🔄 Would you like to try interactive mode? (y/N): ").lower().startswith('y'):
            interactive_mode()
            
    except Exception as e:
        print(f"\n❌ Examples failed with error: {e}")
        print("\nPossible solutions:")
        print("1. Check your .env configuration")
        print("2. Ensure all required services are accessible")
        print("3. Verify your API keys and tokens")


if __name__ == "__main__":
    main()
