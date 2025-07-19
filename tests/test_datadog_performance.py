#!/usr/bin/env python3
"""
Testes de Performance para Datadog
===================================

Este módulo contém testes de performance, carga e cenários avançados
para a conexão com Datadog.
"""

import os
import json
import time
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading

# Importar a classe que queremos testar
from tools import DatadogMCPClientTool


@pytest.mark.performance
class TestDatadogPerformance:
    """Testes de performance para operações do Datadog."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock das variáveis de ambiente necessárias."""
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': 'test_performance_api_key',
            'DATADOG_APP_KEY': 'test_performance_app_key'
        }):
            yield
    
    @pytest.fixture
    def datadog_tool(self, mock_env_vars):
        """Fixture que cria uma instância da ferramenta Datadog."""
        with patch('tools.ApiClient') as mock_api_client, \
             patch('tools.MonitorsApi') as mock_monitors_api, \
             patch('tools.LogsApi') as mock_logs_api:
            
            tool = DatadogMCPClientTool()
            tool.api_client = mock_api_client.return_value
            tool.monitors_api = mock_monitors_api.return_value
            tool.logs_api = mock_logs_api.return_value
            return tool
    
    def create_mock_monitors(self, count):
        """Cria uma lista de monitores mock para testes de carga."""
        monitors = []
        for i in range(count):
            monitor = Mock()
            monitor.id = i + 1
            monitor.name = f"Monitor {i + 1}"
            monitor.message = f"Test message for monitor {i + 1}"
            monitor.priority = (i % 2) + 1  # Alterna entre P1 e P2
            monitor.overall_state = "Alert"
            monitor.tags = [f"service:service-{i}", "env:test"]
            monitor.created = datetime.now() - timedelta(hours=i)
            monitor.query = f"avg(last_5m):avg:metric.test{i}{{*}} > {i}"
            monitors.append(monitor)
        return monitors
    
    @pytest.mark.slow
    def test_get_monitors_large_dataset(self, datadog_tool):
        """Testa busca de monitores com grande quantidade de dados."""
        # Simular 1000 monitores
        large_monitor_list = self.create_mock_monitors(1000)
        datadog_tool.monitors_api.list_monitors.return_value = large_monitor_list
        
        start_time = time.time()
        result = datadog_tool._run('get_monitors')
        end_time = time.time()
        
        # Verificar que a operação completou em tempo razoável (< 5 segundos)
        processing_time = end_time - start_time
        assert processing_time < 5.0, f"Processing took too long: {processing_time}s"
        
        # Verificar resultado
        result_data = json.loads(result)
        assert result_data["status"] == "success"
        assert result_data["count"] == 1000
        
        # Verificar que apenas P1 e P2 foram incluídos
        priorities = [alert["priority"] for alert in result_data["alerts"]]
        assert all(priority in ["P1", "P2"] for priority in priorities)
    
    def test_concurrent_monitor_requests(self, mock_env_vars):
        """Testa múltiplas requisições concorrentes para monitores."""
        with patch('tools.ApiClient'), \
             patch('tools.MonitorsApi') as mock_monitors_api, \
             patch('tools.LogsApi'):
            
            # Setup do mock
            mock_monitors_instance = mock_monitors_api.return_value
            mock_monitors_instance.list_monitors.return_value = self.create_mock_monitors(10)
            
            def make_request():
                tool = DatadogMCPClientTool()
                return tool._run('get_monitors')
            
            # Executar 10 requisições concorrentes
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [future.result() for future in futures]
            end_time = time.time()
            
            # Verificar que todas as requisições foram bem-sucedidas
            assert len(results) == 10
            for result in results:
                result_data = json.loads(result)
                assert result_data["status"] == "success"
            
            # Verificar tempo total (deve ser menor que execução sequencial)
            total_time = end_time - start_time
            assert total_time < 10.0, f"Concurrent execution took too long: {total_time}s"
    
    @pytest.mark.slow
    def test_memory_usage_large_response(self, datadog_tool):
        """Testa uso de memória com resposta grande."""
        import psutil
        import gc
        
        # Obter uso inicial de memória
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Criar uma resposta muito grande (10000 monitores)
        large_monitor_list = self.create_mock_monitors(10000)
        datadog_tool.monitors_api.list_monitors.return_value = large_monitor_list
        
        result = datadog_tool._run('get_monitors')
        
        # Forçar garbage collection
        gc.collect()
        
        # Verificar uso de memória após processamento
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # A operação não deve consumir mais que 100MB adicionais
        assert memory_increase < 100, f"Memory usage increased by {memory_increase:.2f}MB"
        
        # Verificar que o resultado é válido
        result_data = json.loads(result)
        assert result_data["status"] == "success"
    
    def test_timeout_handling(self, datadog_tool):
        """Testa tratamento de timeout na API."""
        def slow_api_call(*args, **kwargs):
            time.sleep(0.1)  # Simular resposta lenta
            raise Exception("Request timeout")
        
        datadog_tool.monitors_api.list_monitors.side_effect = slow_api_call
        
        start_time = time.time()
        result = datadog_tool._run('get_monitors')
        end_time = time.time()
        
        # Verificar que o erro foi tratado rapidamente
        processing_time = end_time - start_time
        assert processing_time < 1.0
        
        # Verificar resposta de erro
        result_data = json.loads(result)
        assert result_data["status"] == "error"
        assert "timeout" in result_data["message"].lower()


@pytest.mark.integration
class TestDatadogRateLimiting:
    """Testes para rate limiting e throttling."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock das variáveis de ambiente necessárias."""
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': 'test_rate_limit_api_key', 
            'DATADOG_APP_KEY': 'test_rate_limit_app_key'
        }):
            yield
    
    def test_rate_limit_error_handling(self, mock_env_vars):
        """Testa tratamento de erro de rate limit."""
        with patch('tools.ApiClient'), \
             patch('tools.MonitorsApi') as mock_monitors_api, \
             patch('tools.LogsApi'):
            
            # Simular erro de rate limit
            mock_monitors_instance = mock_monitors_api.return_value
            rate_limit_error = Exception("429 Too Many Requests - Rate limit exceeded")
            mock_monitors_instance.list_monitors.side_effect = rate_limit_error
            
            tool = DatadogMCPClientTool()
            result = tool._run('get_monitors')
            
            result_data = json.loads(result)
            assert result_data["status"] == "error"
            assert "Rate limit" in result_data["message"] or "429" in result_data["message"]
    
    def test_burst_requests(self, mock_env_vars):
        """Testa múltiplas requisições em burst."""
        request_times = []
        
        with patch('tools.ApiClient'), \
             patch('tools.MonitorsApi') as mock_monitors_api, \
             patch('tools.LogsApi'):
            
            mock_monitors_instance = mock_monitors_api.return_value
            mock_monitors_instance.list_monitors.return_value = []
            
            def track_request_time(*args, **kwargs):
                request_times.append(time.time())
                return []
            
            mock_monitors_instance.list_monitors.side_effect = track_request_time
            
            # Fazer 5 requisições rapidamente
            tool = DatadogMCPClientTool()
            for _ in range(5):
                tool._run('get_monitors')
            
            # Verificar que todas as requisições foram feitas
            assert len(request_times) == 5
            
            # Verificar intervalo entre requisições (sem rate limiting implementado, devem ser rápidas)
            for i in range(1, len(request_times)):
                interval = request_times[i] - request_times[i-1]
                assert interval < 1.0  # Menos de 1 segundo entre requisições


@pytest.mark.datadog
class TestDatadogErrorScenarios:
    """Testes para cenários de erro específicos do Datadog."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock das variáveis de ambiente necessárias."""
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': 'test_error_api_key',
            'DATADOG_APP_KEY': 'test_error_app_key'
        }):
            yield
    
    @pytest.fixture
    def datadog_tool(self, mock_env_vars):
        """Fixture que cria uma instância da ferramenta Datadog."""
        with patch('tools.ApiClient'), \
             patch('tools.MonitorsApi') as mock_monitors_api, \
             patch('tools.LogsApi') as mock_logs_api:
            
            tool = DatadogMCPClientTool()
            tool.monitors_api = mock_monitors_api.return_value
            tool.logs_api = mock_logs_api.return_value
            return tool
    
    def test_authentication_error(self, datadog_tool):
        """Testa erro de autenticação."""
        auth_error = Exception("401 Unauthorized - Invalid API key")
        datadog_tool.monitors_api.list_monitors.side_effect = auth_error
        
        result = datadog_tool._run('get_monitors')
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "401" in result_data["message"] or "Unauthorized" in result_data["message"]
    
    def test_forbidden_error(self, datadog_tool):
        """Testa erro de permissão."""
        forbidden_error = Exception("403 Forbidden - Insufficient permissions")
        datadog_tool.monitors_api.list_monitors.side_effect = forbidden_error
        
        result = datadog_tool._run('get_monitors')
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "403" in result_data["message"] or "Forbidden" in result_data["message"]
    
    def test_service_unavailable(self, datadog_tool):
        """Testa erro de serviço indisponível."""
        service_error = Exception("503 Service Unavailable - Datadog API is temporarily unavailable")
        datadog_tool.monitors_api.list_monitors.side_effect = service_error
        
        result = datadog_tool._run('get_monitors')
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "503" in result_data["message"] or "unavailable" in result_data["message"].lower()
    
    def test_malformed_api_response(self, datadog_tool):
        """Testa resposta malformada da API."""
        # Mock que retorna objeto sem atributos esperados
        malformed_monitor = object()  # Objeto sem atributos
        datadog_tool.monitors_api.list_monitors.return_value = [malformed_monitor]
        
        result = datadog_tool._run('get_monitors')
        result_data = json.loads(result)
        
        # Deve tratar o erro graciosamente
        assert result_data["status"] == "error"
    
    def test_network_connection_error(self, datadog_tool):
        """Testa erro de conexão de rede."""
        network_error = Exception("ConnectionError - Unable to reach Datadog API")
        datadog_tool.monitors_api.list_monitors.side_effect = network_error
        
        result = datadog_tool._run('get_monitors')
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "connection" in result_data["message"].lower()
    
    def test_json_decode_error_in_response(self, datadog_tool):
        """Testa erro de decodificação JSON na resposta."""
        # Configurar mock que causa erro de JSON
        def json_error(*args, **kwargs):
            # Simular resposta que não pode ser serializada
            monitor = Mock()
            monitor.id = 1
            monitor.name = "Test Monitor"
            monitor.message = "Test"
            monitor.priority = 1
            monitor.overall_state = "Alert"
            monitor.tags = []
            monitor.query = "test"
            # Criar um objeto datetime que não pode ser serializado facilmente
            class NonSerializableDate:
                def isoformat(self):
                    raise Exception("Cannot serialize date")
            monitor.created = NonSerializableDate()
            return [monitor]
        
        datadog_tool.monitors_api.list_monitors.side_effect = json_error
        
        result = datadog_tool._run('get_monitors')
        
        # Deve retornar erro, mas não deve crashar
        result_data = json.loads(result)
        assert result_data["status"] == "error"


@pytest.mark.slow
class TestDatadogStressTest:
    """Testes de stress para conexão com Datadog."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock das variáveis de ambiente necessárias.""" 
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': 'test_stress_api_key',
            'DATADOG_APP_KEY': 'test_stress_app_key'
        }):
            yield
    
    def test_repeated_requests_stability(self, mock_env_vars):
        """Testa estabilidade com requisições repetidas."""
        with patch('tools.ApiClient'), \
             patch('tools.MonitorsApi') as mock_monitors_api, \
             patch('tools.LogsApi'):
            
            mock_monitors_instance = mock_monitors_api.return_value
            mock_monitors_instance.list_monitors.return_value = [Mock()]
            
            tool = DatadogMCPClientTool()
            
            # Fazer 100 requisições
            success_count = 0
            for i in range(100):
                try:
                    result = tool._run('get_monitors')
                    result_data = json.loads(result)
                    if result_data["status"] == "success":
                        success_count += 1
                except Exception:
                    pass  # Contar falhas silenciosamente
            
            # Pelo menos 95% das requisições devem ser bem-sucedidas
            success_rate = success_count / 100
            assert success_rate >= 0.95, f"Success rate too low: {success_rate:.2%}"
    
    def test_memory_leak_detection(self, mock_env_vars):
        """Testa detecção de vazamentos de memória."""
        import psutil
        import gc
        
        with patch('tools.ApiClient'), \
             patch('tools.MonitorsApi') as mock_monitors_api, \
             patch('tools.LogsApi'):
            
            mock_monitors_instance = mock_monitors_api.return_value
            mock_monitors_instance.list_monitors.return_value = [Mock()]
            
            process = psutil.Process()
            initial_memory = process.memory_info().rss
            
            # Criar e destruir muitas instâncias
            for i in range(50):
                tool = DatadogMCPClientTool()
                tool._run('get_monitors')
                del tool
                
                if i % 10 == 0:  # Garbage collection a cada 10 iterações
                    gc.collect()
            
            final_memory = process.memory_info().rss
            memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
            
            # Não deve haver aumento significativo de memória
            assert memory_increase < 50, f"Possible memory leak: {memory_increase:.2f}MB increase"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
