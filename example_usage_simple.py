#!/usr/bin/env python3
"""
SRE Copilot - Simple Example Usage
==================================

This is a simplified version that works with OpenAI and demonstrates
the basic functionality of the SRE Copilot system.
"""

import os
import json
from dotenv import load_dotenv
from sre_copilot import SRECopilot
from tools import DatadogMCPClientTool


def setup_environment():
    """Load environment variables from .env file."""
    load_dotenv()
    
    # Check for OpenAI key (simplest to configure)
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_key:
        print("❌ No OpenAI API key found!")
        print("Please set OPENAI_API_KEY in your .env file")
        print("Copy .env.example to .env and add your OpenAI API key")
        return False
    
    print("🧠 LLM Provider: OpenAI configured ✅")
    return True


def test_datadog_tool():
    """Test the Datadog tool directly (with mocked data)."""
    print("\n" + "="*60)
    print("🔧 Testing Datadog Tool Directly")
    print("="*60)
    
    # Test if Datadog environment variables are set
    datadog_api_key = os.getenv('DATADOG_API_KEY')
    datadog_app_key = os.getenv('DATADOG_APP_KEY')
    
    if not datadog_api_key or not datadog_app_key:
        print("⚠️  Datadog credentials not configured")
        print("   Set DATADOG_API_KEY and DATADOG_APP_KEY in .env to test real API")
        print("   This example will use mock data instead")
        return simulate_datadog_response()
    
    try:
        # Try to initialize Datadog tool
        datadog_tool = DatadogMCPClientTool()
        print("✅ Datadog tool initialized successfully")
        
        # Test getting monitors (will likely fail without real credentials)
        result = datadog_tool._run("get_monitors")
        print("📊 Monitors result:", result[:200] + "..." if len(result) > 200 else result)
        
    except Exception as e:
        print(f"❌ Datadog tool test failed: {e}")
        print("Using simulated response instead...")
        return simulate_datadog_response()


def simulate_datadog_response():
    """Simulate a Datadog response for demo purposes."""
    mock_response = {
        "status": "success",
        "count": 2,
        "alerts": [
            {
                "id": 12345,
                "name": "High CPU Usage - Web Servers",
                "priority": "P1",
                "state": "Alert",
                "tags": ["env:production", "service:web", "team:backend"],
                "created": "2024-01-15T10:30:00Z",
                "message": "CPU usage is above 80% for more than 5 minutes"
            },
            {
                "id": 67890,
                "name": "Database Connection Pool Exhausted",
                "priority": "P2", 
                "state": "Alert",
                "tags": ["env:production", "service:database", "team:data"],
                "created": "2024-01-15T10:25:00Z",
                "message": "Connection pool has exceeded 90% capacity"
            }
        ]
    }
    
    print("📊 Simulated Datadog response:")
    print(json.dumps(mock_response, indent=2))
    return json.dumps(mock_response)


def test_sre_copilot_status():
    """Test SRE Copilot initialization and status."""
    print("\n" + "="*60)
    print("🤖 Testing SRE Copilot System")
    print("="*60)
    
    try:
        # Initialize with OpenAI (more predictable than Gemini for demos)
        sre_copilot = SRECopilot(llm_provider="openai")
        
        # Get system status
        status = sre_copilot.get_crew_status()
        
        print("✅ SRE Copilot initialized successfully!")
        print("\n🤖 System Status:")
        print(f"   • Agents: {status['agents_count']}")
        print(f"   • Tasks: {status['tasks_count']}")
        print(f"   • Tools Available: {', '.join(status['tools_available'])}")
        print(f"   • Process Type: {status['process']}")
        print(f"   • Memory Enabled: {status['memory_enabled']}")
        
        return sre_copilot
        
    except Exception as e:
        print(f"❌ SRE Copilot initialization failed: {e}")
        return None


def run_simple_incident_response():
    """Run a simple incident response simulation."""
    print("\n" + "="*60)
    print("🚨 Simple Incident Response Test")
    print("="*60)
    
    try:
        sre_copilot = SRECopilot(llm_provider="openai")
        
        # Simple incident context
        incident_context = {
            "service": "web-api",
            "environment": "production", 
            "issue": "High response times and error rates",
            "severity": "P2",
            "reported_by": "Monitoring System"
        }
        
        print("📋 Incident Context:")
        print(json.dumps(incident_context, indent=2))
        
        print("\n🔍 Starting investigation...")
        print("⚠️  Note: This will attempt to run the full crew workflow")
        print("   Press Ctrl+C to interrupt if it takes too long")
        
        # Run with timeout protection
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Operation timed out")
        
        # Set 60 second timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)
        
        try:
            result = sre_copilot.run_incident_response(
                incident_context=json.dumps(incident_context)
            )
            signal.alarm(0)  # Cancel timeout
            
            print("\n✅ Incident response completed!")
            print("📊 Result:", str(result)[:500] + "..." if len(str(result)) > 500 else result)
            
        except TimeoutError:
            print("\n⏰ Operation timed out after 60 seconds")
            print("   This is normal for the first run as models initialize")
        except KeyboardInterrupt:
            print("\n👋 Operation interrupted by user")
        finally:
            signal.alarm(0)
            
    except Exception as e:
        print(f"❌ Incident response test failed: {e}")


def show_menu():
    """Show interactive menu."""
    print("\n" + "="*60)
    print("🔄 SRE Copilot - Interactive Menu")
    print("="*60)
    print("Choose an option:")
    print("1. Test Datadog Tool")
    print("2. Check SRE Copilot Status") 
    print("3. Run Simple Incident Response")
    print("4. Show Mock Data Examples")
    print("5. Exit")
    return input("\nEnter your choice (1-5): ").strip()


def show_mock_examples():
    """Show examples of mock data that can be used."""
    print("\n" + "="*60)
    print("📋 Mock Data Examples")
    print("="*60)
    
    examples = [
        {
            "name": "High CPU Alert",
            "context": {
                "service": "web-servers",
                "environment": "production",
                "metric": "cpu_usage",
                "threshold": "80%",
                "current_value": "92%",
                "duration": "10 minutes"
            }
        },
        {
            "name": "Database Connection Issue", 
            "context": {
                "service": "postgres-db",
                "environment": "production",
                "issue": "connection_pool_exhausted",
                "affected_services": ["user-service", "order-service"],
                "error_rate": "45%"
            }
        },
        {
            "name": "Application Error Spike",
            "context": {
                "service": "checkout-api",
                "environment": "production",
                "error_type": "500_internal_server_error",
                "error_count": 150,
                "time_window": "5 minutes"
            }
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}")
        print(json.dumps(example['context'], indent=3))


def main():
    """Main function with interactive menu."""
    print("🚀 SRE Copilot - Simple Example")
    print("="*60)
    
    # Setup environment
    if not setup_environment():
        return
    
    try:
        while True:
            choice = show_menu()
            
            if choice == '1':
                test_datadog_tool()
            elif choice == '2':
                test_sre_copilot_status()
            elif choice == '3':
                run_simple_incident_response()
            elif choice == '4':
                show_mock_examples()
            elif choice == '5':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please try again.")
                
            input("\nPress Enter to continue...")
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Application error: {e}")


if __name__ == "__main__":
    main()
