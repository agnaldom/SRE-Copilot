#!/usr/bin/env python3
"""
SRE Copilot - CrewAI-based Incident Response System
==================================================

This module implements an automated incident response system using CrewAI
to coordinate multiple specialized agents for alert triage, investigation,
analysis, and notification.
"""

import os
from typing import List, Dict, Any
from crewai import Agent, Task, Crew, Process
import yaml

# Import enhanced MCP tools
from tools import (
    DatadogMCPClientTool,
    KubernetesMCPClientTool, 
    SlackNotifierTool,
    TeamsNotifierTool
)

# Import LLM factory for multi-provider support
from llm_factory import LLMFactory, create_llm_for_agent_role


class SRECopilot:
    """Main SRE Copilot system coordinating incident response."""
    
    def __init__(self, config_path: str = "sre_copilot_prompt.yaml", llm_provider: str = None):
        """Initialize SRE Copilot with configuration."""
        self.config = self._load_config(config_path)
        self.llm_provider = llm_provider
        self.available_providers = LLMFactory.get_available_providers()
        print(f"🧠 Available LLM providers: {self.available_providers}")
        
        # Initialize default LLM
        self.default_llm = self._create_default_llm()
        
        self.tools = self._initialize_tools()
        self.agents = self._create_agents()
        self.tasks = self._create_tasks()
        self.crew = self._create_crew()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    
    def _create_default_llm(self):
        """Create default LLM instance."""
        try:
            llm = LLMFactory.create_llm(provider=self.llm_provider)
            provider_name = self.llm_provider or LLMFactory.get_default_provider()
            print(f"✅ LLM initialized: {provider_name} ({type(llm).__name__})")
            return llm
        except Exception as e:
            print(f"❌ Failed to initialize LLM: {e}")
            raise
    
    def _initialize_tools(self) -> List:
        """Initialize all available tools with error handling."""
        tools = []
        
        # Try to initialize each tool, skip if environment variables are missing
        try:
            tools.append(DatadogMCPClientTool())
            print("✅ Datadog tool initialized")
        except ValueError as e:
            print(f"⚠️  Datadog tool skipped: {e}")
        
        try:
            tools.append(KubernetesMCPClientTool())
            print("✅ Kubernetes tool initialized")
        except ValueError as e:
            print(f"⚠️  Kubernetes tool skipped: {e}")
        
        try:
            tools.append(SlackNotifierTool())
            print("✅ Slack tool initialized")
        except ValueError as e:
            print(f"⚠️  Slack tool skipped: {e}")
        
        try:
            tools.append(TeamsNotifierTool())
            print("✅ Teams tool initialized")
        except ValueError as e:
            print(f"⚠️  Teams tool skipped: {e}")
        
        return tools
    
    def _create_agents(self) -> Dict[str, Agent]:
        """Create specialized agents based on configuration."""
        agents = {}
        
        # Alert Triage Agent - optimized for fast, deterministic responses
        triage_llm = create_llm_for_agent_role("triage", self.llm_provider)
        agents['alert_triage_agent'] = Agent(
            role="Alert Triage Specialist",
            goal="Identificar e priorizar alertas críticos do Datadog",
            backstory="""Você é um especialista em monitoramento e observabilidade com anos de experiência
            em sistemas de produção. Sua função é analisar alertas do Datadog, identificar
            criticidade e extrair informações relevantes para investigação posterior.""",
            verbose=True,
            allow_delegation=False,
            tools=[tool for tool in self.tools if tool.name == "datadog_client"],
            llm=triage_llm
        )
        
        # Investigator Agent - optimized for balanced investigation tasks
        investigation_llm = create_llm_for_agent_role("investigation", self.llm_provider)
        agents['investigator_agent'] = Agent(
            role="Kubernetes Forensics Specialist",
            goal="Coletar dados técnicos detalhados sobre incidentes",
            backstory="""Você é um engenheiro SRE especializado em Kubernetes forensics e troubleshooting.
            Domina kubectl, análise de logs e eventos de sistema para identificar problemas
            em infraestrutura containerizada.""",
            verbose=True,
            allow_delegation=False,
            tools=[tool for tool in self.tools if tool.name == "kubernetes_client"],
            llm=investigation_llm
        )
        
        # Root Cause Analyzer Agent - uses most powerful model for complex analysis
        analysis_llm = create_llm_for_agent_role("analysis", self.llm_provider)
        agents['root_cause_analyzer_agent'] = Agent(
            role="Root Cause Analysis Expert",
            goal="Sintetizar dados coletados para identificar causa raiz",
            backstory="""Você é um arquiteto de sistemas com expertise em análise de incidentes
            e resolução de problemas complexos. Consegue correlacionar dados de
            múltiplas fontes para identificar a verdadeira causa raiz.""",
            verbose=True,
            allow_delegation=False,
            tools=[],  # This agent focuses on analysis, not tool execution
            llm=analysis_llm
        )
        
        # Notification Agent - optimized for consistent, clear communication
        notification_llm = create_llm_for_agent_role("notification", self.llm_provider)
        agents['notification_agent'] = Agent(
            role="Incident Communication Specialist",
            goal="Comunicar achados e coordenar resposta ao incidente",
            backstory="""Você é um especialista em comunicação de incidentes com experiência
            em coordenar equipes durante crises. Sabe como estruturar informações
            técnicas para diferentes audiências.""",
            verbose=True,
            allow_delegation=False,
            tools=[tool for tool in self.tools if tool.name in ["slack_notifier", "teams_notifier"]],
            llm=notification_llm
        )
        
        return agents
    
    def _create_tasks(self) -> List[Task]:
        """Create tasks based on configuration."""
        tasks = []
        
        # Triage Task
        triage_task = Task(
            description="""Verifique no Datadog por alertas P1 e P2 ativos.
            
            Você deve:
            1. Buscar alertas com severidade P1 e P2
            2. Extrair tags importantes (service, host, environment)
            3. Classificar por criticidade e impacto
            4. Preparar contexto para investigação técnica
            
            Sempre inclua:
            - Timestamp do alerta
            - Severidade
            - Tags relevantes
            - Descrição do problema""",
            agent=self.agents['alert_triage_agent'],
            expected_output="""Lista de alertas críticos com:
            - ID do alerta
            - Severidade
            - Tags extraídas
            - Timestamp
            - Descrição do problema"""
        )
        tasks.append(triage_task)
        
        # Investigation Task
        investigate_task = Task(
            description="""Use as tags do alerta para encontrar o pod relacionado no Kubernetes 
            e colete logs, eventos e descrição.
            
            Seus passos são:
            1. Usar tags do alerta para localizar recursos no K8s
            2. Coletar logs recentes dos pods afetados
            3. Verificar eventos do namespace
            4. Executar kubectl describe nos recursos
            5. Analisar métricas de resource usage
            
            Sempre colete:
            - Logs recentes (últimos 30 minutos)
            - Eventos do pod e namespace
            - Saída do describe do recurso
            - Status de health checks
            - Configuração de resources/limits""",
            agent=self.agents['investigator_agent'],
            context=[triage_task],
            expected_output="""Dados técnicos coletados:
            - Logs dos pods afetados
            - Eventos do Kubernetes
            - Configuração dos recursos
            - Métricas de performance"""
        )
        tasks.append(investigate_task)
        
        # Analysis Task
        analyze_task = Task(
            description="""Conecte os dados do alerta com os dados do Kubernetes 
            para determinar a causa raiz.
            
            Sua função é:
            1. Correlacionar timeline dos eventos
            2. Identificar padrões e anomalias
            3. Determinar causa raiz provável
            4. Sugerir ações de mitigação
            5. Recomendar melhorias preventivas
            
            Estruture sua análise em:
            - Resumo executivo
            - Timeline dos eventos
            - Causa raiz identificada
            - Impacto estimado
            - Ações recomendadas (imediatas e preventivas)""",
            agent=self.agents['root_cause_analyzer_agent'],
            context=[triage_task, investigate_task],
            expected_output="""Análise de causa raiz contendo:
            - Timeline correlacionado
            - Causa raiz identificada
            - Impacto do incidente
            - Recomendações de mitigação"""
        )
        tasks.append(analyze_task)
        
        # Notification Task
        notify_task = Task(
            description="""Monte um relatório de incidente em Markdown e envie 
            para Slack e Teams.
            
            Suas responsabilidades:
            1. Criar relatório executivo do incidente
            2. Preparar comunicação técnica detalhada
            3. Enviar notificações para Slack/Teams
            4. Atualizar status pages se necessário
            5. Documentar lições aprendidas
            
            Formato do relatório:
            - 🚨 Status: [ATIVO/RESOLVIDO/INVESTIGANDO]
            - ⏰ Início: [timestamp]
            - 🎯 Serviços Afetados: [lista]
            - 🔍 Causa Raiz: [resumo]
            - 🛠️ Ações Tomadas: [lista]
            - 👥 Equipes Envolvidas: [tags]""",
            agent=self.agents['notification_agent'],
            context=[analyze_task],
            expected_output="""Relatório de incidente enviado contendo:
            - Resumo executivo
            - Detalhes técnicos
            - Ações recomendadas
            - Links para dashboards relevantes"""
        )
        tasks.append(notify_task)
        
        return tasks
    
    def _create_crew(self) -> Crew:
        """Create the crew with all agents and tasks."""
        return Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,
            max_iterations=3
        )
    
    def run_incident_response(self, incident_context: str = None) -> str:
        """Execute the full incident response workflow."""
        print("🚨 SRE Copilot - Iniciando resposta ao incidente...")
        print("=" * 60)
        
        try:
            result = self.crew.kickoff(
                inputs={"incident_context": incident_context or "Verificar alertas ativos"}
            )
            
            print("✅ Resposta ao incidente concluída!")
            return result
        
        except Exception as e:
            print(f"❌ Erro na resposta ao incidente: {e}")
            raise
    
    def get_crew_status(self) -> Dict[str, Any]:
        """Get current status of the crew."""
        try:
            current_provider = self.llm_provider or LLMFactory.get_default_provider()
        except:
            current_provider = "none"
            
        return {
            "agents_count": len(self.agents),
            "tasks_count": len(self.tasks),
            "tools_available": [tool.name for tool in self.tools],
            "process": "sequential",
            "memory_enabled": True,
            "llm_provider": current_provider,
            "available_providers": self.available_providers,
            "llm_type": type(self.default_llm).__name__ if hasattr(self, 'default_llm') else "unknown"
        }


def main():
    """Main entry point for SRE Copilot."""
    print("🤖 Inicializando SRE Copilot...")
    
    try:
        # Initialize SRE Copilot
        sre_copilot = SRECopilot()
        
        # Show system status
        status = sre_copilot.get_crew_status()
        print(f"📊 Status do Sistema: {status}")
        
        # Run incident response
        result = sre_copilot.run_incident_response()
        
        print("\n" + "=" * 60)
        print("📋 Resultado da Análise:")
        print(result)
        
    except FileNotFoundError:
        print("❌ Arquivo de configuração não encontrado: sre_copilot_prompt.yaml")
    except Exception as e:
        print(f"❌ Erro crítico: {e}")


if __name__ == "__main__":
    main()
