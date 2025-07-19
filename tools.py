#!/usr/bin/env python3
"""
SRE Copilot - Enhanced MCP Tools
================================

This module provides enhanced implementations of the MCP (Model Context Protocol)
tools for real integrations with Datadog, Kubernetes, Slack, and Teams.
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from crewai.tools import BaseTool
from kubernetes import client, config
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from datadog_api_client.v1.api.logs_api import LogsApi
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import pymsteams


class DatadogMCPClientTool(BaseTool):
    """Enhanced tool for interacting with Datadog API to fetch alerts and monitors."""
    
    name: str = "datadog_client"
    description: str = "Fetch alerts, monitors, and metrics data from Datadog API"
    
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def model_post_init(self, __context):
        """Initialize Datadog API clients after Pydantic model initialization."""
        super().model_post_init(__context)
        
        api_key = os.getenv("DATADOG_API_KEY")
        app_key = os.getenv("DATADOG_APP_KEY")
        
        if not api_key or not app_key:
            raise ValueError("DATADOG_API_KEY and DATADOG_APP_KEY environment variables are required")
        
        # Configure Datadog API client
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        configuration.api_key["appKeyAuth"] = app_key
        self.api_client = ApiClient(configuration)
        self.monitors_api = MonitorsApi(self.api_client)
        self.logs_api = LogsApi(self.api_client)
        
        # Store keys for test access (not recommended in production)
        self._api_key = api_key
        self._app_key = app_key
    
    def _run(self, query: str) -> str:
        """Execute Datadog API query."""
        try:
            query_data = json.loads(query) if query.startswith('{') else {"action": query}
            action = query_data.get("action", "get_monitors")
            
            if action == "get_monitors":
                return self._get_active_monitors(query_data)
            elif action == "get_logs":
                return self._get_logs(query_data)
            elif action == "get_metrics":
                return self._get_metrics(query_data)
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            return f"Error executing Datadog query: {str(e)}"
    
    def _get_active_monitors(self, params: Dict) -> str:
        """Get active monitors with P1/P2 severity."""
        try:
            # Get monitors that are alerting
            # Note: API parameters may vary by Datadog API version
            tags_list = params.get("tags", [])
            tags_str = ",".join(tags_list) if tags_list else None
            
            try:
                # Try with both group_states and tags as strings
                if tags_str:
                    monitors = self.monitors_api.list_monitors(
                        group_states="Alert,Warn",
                        tags=tags_str
                    )
                else:
                    monitors = self.monitors_api.list_monitors(
                        group_states="Alert,Warn"
                    )
            except Exception as e:
                # Fallback: try without any filters
                try:
                    monitors = self.monitors_api.list_monitors()
                except Exception:
                    # Last resort: return empty list
                    monitors = []
            
            critical_alerts = []
            for monitor in monitors:
                if monitor.priority in [1, 2]:  # P1 and P2
                    alert_info = {
                        "id": monitor.id,
                        "name": monitor.name,
                        "message": monitor.message,
                        "priority": f"P{monitor.priority}",
                        "state": monitor.overall_state,
                        "tags": monitor.tags or [],
                        "created": monitor.created.isoformat() if monitor.created else None,
                        "query": monitor.query
                    }
                    critical_alerts.append(alert_info)
            
            return json.dumps({
                "status": "success",
                "count": len(critical_alerts),
                "alerts": critical_alerts
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to fetch monitors: {str(e)}"
            })
    
    def _get_logs(self, params: Dict) -> str:
        """Get logs for specific service or time range."""
        try:
            # Default to last 30 minutes
            time_from = params.get("from", (datetime.now() - timedelta(minutes=30)).isoformat())
            time_to = params.get("to", datetime.now().isoformat())
            query = params.get("query", "status:error")
            
            logs = self.logs_api.list_logs(
                body={
                    "query": query,
                    "time": {
                        "from": time_from,
                        "to": time_to
                    },
                    "limit": params.get("limit", 100)
                }
            )
            
            return json.dumps({
                "status": "success",
                "logs": logs.to_dict() if hasattr(logs, 'to_dict') else str(logs)
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to fetch logs: {str(e)}"
            })
    
    def _get_metrics(self, params: Dict) -> str:
        """Get metrics data."""
        # This would require the metrics API which is more complex
        return json.dumps({
            "status": "info",
            "message": "Metrics API integration not implemented yet"
        })


class KubernetesMCPClientTool(BaseTool):
    """Enhanced tool for interacting with Kubernetes cluster."""
    
    name: str = "kubernetes_client" 
    description: str = "Execute kubectl commands and gather pod/namespace information"
    
    def __init__(self):
        super().__init__()
        try:
            # Try to load in-cluster config first, then local config
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()
            
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
        except Exception as e:
            raise ValueError(f"Failed to initialize Kubernetes client: {str(e)}")
    
    def _run(self, command: str) -> str:
        """Execute Kubernetes operation."""
        try:
            command_data = json.loads(command) if command.startswith('{') else {"action": command}
            action = command_data.get("action", "get_pods")
            
            if action == "get_pods":
                return self._get_pods_info(command_data)
            elif action == "get_logs":
                return self._get_pod_logs(command_data)
            elif action == "get_events":
                return self._get_events(command_data)
            elif action == "describe_pod":
                return self._describe_pod(command_data)
            elif action == "get_deployments":
                return self._get_deployments(command_data)
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            return f"Error executing Kubernetes command: {str(e)}"
    
    def _get_pods_info(self, params: Dict) -> str:
        """Get pods information."""
        try:
            namespace = params.get("namespace", "default")
            label_selector = params.get("label_selector", "")
            
            pods = self.v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            pod_info = []
            for pod in pods.items:
                info = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "phase": pod.status.phase,
                    "restart_count": sum(c.restart_count for c in (pod.status.container_statuses or [])),
                    "ready": self._is_pod_ready(pod),
                    "labels": pod.metadata.labels or {},
                    "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                    "node": pod.spec.node_name,
                    "containers": [c.name for c in pod.spec.containers]
                }
                pod_info.append(info)
            
            return json.dumps({
                "status": "success",
                "namespace": namespace,
                "count": len(pod_info),
                "pods": pod_info
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error", 
                "message": f"Failed to get pods: {str(e)}"
            })
    
    def _get_pod_logs(self, params: Dict) -> str:
        """Get logs from a specific pod."""
        try:
            pod_name = params.get("pod_name")
            namespace = params.get("namespace", "default")
            container = params.get("container")
            lines = params.get("lines", 100)
            
            if not pod_name:
                return json.dumps({"status": "error", "message": "pod_name is required"})
            
            logs = self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=lines,
                timestamps=True
            )
            
            return json.dumps({
                "status": "success",
                "pod": pod_name,
                "namespace": namespace,
                "container": container,
                "logs": logs
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to get pod logs: {str(e)}"
            })
    
    def _get_events(self, params: Dict) -> str:
        """Get events from a namespace."""
        try:
            namespace = params.get("namespace", "default")
            
            events = self.v1.list_namespaced_event(namespace=namespace)
            
            event_info = []
            for event in events.items:
                info = {
                    "name": event.metadata.name,
                    "namespace": event.metadata.namespace,
                    "reason": event.reason,
                    "message": event.message,
                    "type": event.type,
                    "count": event.count,
                    "first_timestamp": event.first_timestamp.isoformat() if event.first_timestamp else None,
                    "last_timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None,
                    "involved_object": {
                        "kind": event.involved_object.kind,
                        "name": event.involved_object.name,
                        "namespace": event.involved_object.namespace
                    } if event.involved_object else None
                }
                event_info.append(info)
            
            return json.dumps({
                "status": "success",
                "namespace": namespace,
                "count": len(event_info),
                "events": event_info
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to get events: {str(e)}"
            })
    
    def _describe_pod(self, params: Dict) -> str:
        """Get detailed information about a pod."""
        try:
            pod_name = params.get("pod_name")
            namespace = params.get("namespace", "default")
            
            if not pod_name:
                return json.dumps({"status": "error", "message": "pod_name is required"})
            
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            
            pod_details = {
                "metadata": {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "labels": pod.metadata.labels or {},
                    "annotations": pod.metadata.annotations or {},
                    "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                },
                "spec": {
                    "node_name": pod.spec.node_name,
                    "restart_policy": pod.spec.restart_policy,
                    "containers": [
                        {
                            "name": c.name,
                            "image": c.image,
                            "resources": c.resources.to_dict() if c.resources else None
                        } for c in pod.spec.containers
                    ]
                },
                "status": {
                    "phase": pod.status.phase,
                    "pod_ip": pod.status.pod_ip,
                    "conditions": [
                        {
                            "type": c.type,
                            "status": c.status,
                            "reason": c.reason,
                            "message": c.message
                        } for c in (pod.status.conditions or [])
                    ],
                    "container_statuses": [
                        {
                            "name": c.name,
                            "ready": c.ready,
                            "restart_count": c.restart_count,
                            "state": c.state.to_dict() if c.state else None
                        } for c in (pod.status.container_statuses or [])
                    ]
                }
            }
            
            return json.dumps({
                "status": "success",
                "pod_details": pod_details
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to describe pod: {str(e)}"
            })
    
    def _get_deployments(self, params: Dict) -> str:
        """Get deployment information."""
        try:
            namespace = params.get("namespace", "default")
            
            deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
            
            deployment_info = []
            for deployment in deployments.items:
                info = {
                    "name": deployment.metadata.name,
                    "namespace": deployment.metadata.namespace,
                    "replicas": deployment.spec.replicas,
                    "ready_replicas": deployment.status.ready_replicas or 0,
                    "available_replicas": deployment.status.available_replicas or 0,
                    "labels": deployment.metadata.labels or {},
                    "created": deployment.metadata.creation_timestamp.isoformat() if deployment.metadata.creation_timestamp else None
                }
                deployment_info.append(info)
            
            return json.dumps({
                "status": "success",
                "namespace": namespace,
                "count": len(deployment_info),
                "deployments": deployment_info
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to get deployments: {str(e)}"
            })
    
    def _is_pod_ready(self, pod) -> bool:
        """Check if pod is ready."""
        if not pod.status.conditions:
            return False
        
        for condition in pod.status.conditions:
            if condition.type == "Ready":
                return condition.status == "True"
        return False


class SlackNotifierTool(BaseTool):
    """Enhanced tool for sending notifications to Slack."""
    
    name: str = "slack_notifier"
    description: str = "Send incident reports and notifications to Slack channels"
    
    def __init__(self):
        super().__init__()
        self.token = os.getenv("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")
        
        self.client = WebClient(token=self.token)
    
    def _run(self, message: str) -> str:
        """Send message to Slack."""
        try:
            message_data = json.loads(message) if message.startswith('{') else {"text": message}
            channel = message_data.get("channel", "#incidents")
            text = message_data.get("text", message)
            
            # Format message with rich formatting
            if isinstance(text, dict):
                formatted_message = self._format_incident_report(text)
            else:
                formatted_message = text
            
            response = self.client.chat_postMessage(
                channel=channel,
                text=formatted_message,
                parse="full"
            )
            
            return json.dumps({
                "status": "success",
                "message": "Slack notification sent successfully",
                "channel": channel,
                "timestamp": response["ts"]
            }, indent=2)
            
        except SlackApiError as e:
            return json.dumps({
                "status": "error",
                "message": f"Slack API error: {e.response['error']}"
            })
        except Exception as e:
            return json.dumps({
                "status": "error", 
                "message": f"Failed to send Slack notification: {str(e)}"
            })
    
    def _format_incident_report(self, report: Dict) -> str:
        """Format incident report for Slack."""
        formatted = f"""
🚨 *INCIDENT ALERT* 🚨

*Status:* {report.get('status', 'UNKNOWN')}
*Início:* {report.get('start_time', 'N/A')}
*Serviços Afetados:* {', '.join(report.get('affected_services', []))}

*🔍 Causa Raiz:*
{report.get('root_cause', 'Investigating...')}

*🛠️ Ações Tomadas:*
{chr(10).join(f'• {action}' for action in report.get('actions_taken', []))}

*👥 Equipes Envolvidas:*
{', '.join(report.get('teams', []))}

*📊 Dashboards:*
{chr(10).join(report.get('dashboard_links', []))}
"""
        return formatted.strip()


class TeamsNotifierTool(BaseTool):
    """Enhanced tool for sending notifications to Microsoft Teams."""
    
    name: str = "teams_notifier"
    description: str = "Send incident reports and notifications to Microsoft Teams channels"
    
    def __init__(self):
        super().__init__()
        self.webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("TEAMS_WEBHOOK_URL environment variable is required")
    
    def _run(self, message: str) -> str:
        """Send message to Teams."""
        try:
            message_data = json.loads(message) if message.startswith('{') else {"text": message}
            
            teams_message = pymsteams.connectorcard(self.webhook_url)
            
            if isinstance(message_data, dict) and "status" in message_data:
                # Incident report format
                teams_message.title("🚨 INCIDENT ALERT")
                teams_message.color("FF0000" if message_data.get("status") == "ATIVO" else "00FF00")
                teams_message.text(self._format_incident_report(message_data))
            else:
                # Simple text message
                text = message_data.get("text", str(message_data))
                teams_message.text(text)
            
            teams_message.send()
            
            return json.dumps({
                "status": "success",
                "message": "Teams notification sent successfully"
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to send Teams notification: {str(e)}"
            })
    
    def _format_incident_report(self, report: Dict) -> str:
        """Format incident report for Teams."""
        formatted = f"""
**Status:** {report.get('status', 'UNKNOWN')}
**Início:** {report.get('start_time', 'N/A')}
**Serviços Afetados:** {', '.join(report.get('affected_services', []))}

**🔍 Causa Raiz:**
{report.get('root_cause', 'Investigating...')}

**🛠️ Ações Tomadas:**
{chr(10).join(f'• {action}' for action in report.get('actions_taken', []))}

**👥 Equipes Envolvidas:**
{', '.join(report.get('teams', []))}
"""
        return formatted.strip()
