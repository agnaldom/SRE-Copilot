#!/usr/bin/env python3
"""
Configuração global para testes
===============================

Este arquivo contém configurações globais e fixtures comuns para todos os testes.
"""

import os
import pytest
from unittest.mock import patch
import sys

# Adicionar o diretório raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def mock_datadog_env():
    """Fixture de sessão que configura variáveis de ambiente para Datadog."""
    with patch.dict(os.environ, {
        'DATADOG_API_KEY': 'test_session_api_key',
        'DATADOG_APP_KEY': 'test_session_app_key',
        'DATADOG_SITE': 'datadoghq.com'
    }):
        yield


@pytest.fixture(scope="function")  
def clean_env():
    """Fixture que limpa variáveis de ambiente para testes específicos."""
    original_env = os.environ.copy()
    # Remover variáveis específicas do Datadog se existirem
    for key in ['DATADOG_API_KEY', 'DATADOG_APP_KEY']:
        if key in os.environ:
            del os.environ[key]
    
    yield
    
    # Restaurar ambiente original
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_monitor_data():
    """Fixture com dados de exemplo de monitor do Datadog."""
    return {
        "id": 123456,
        "name": "High CPU Usage",
        "message": "CPU usage is above 80% for more than 5 minutes",
        "priority": 1,
        "overall_state": "Alert",
        "tags": ["env:prod", "service:web", "team:backend"],
        "query": "avg(last_5m):avg:system.cpu.user{*} by {host} > 0.8",
        "type": "metric alert"
    }


@pytest.fixture
def sample_logs_data():
    """Fixture com dados de exemplo de logs do Datadog."""
    return {
        "logs": [
            {
                "timestamp": "2024-01-15T10:30:00Z",
                "message": "Error processing payment request",
                "level": "ERROR",
                "service": "payment-api",
                "host": "web-server-01"
            },
            {
                "timestamp": "2024-01-15T10:29:45Z", 
                "message": "Database connection timeout",
                "level": "ERROR",
                "service": "payment-api",
                "host": "web-server-01"
            }
        ],
        "total": 2
    }


# Configuração para markers customizados
def pytest_configure(config):
    """Configurar markers customizados para categorizar testes."""
    config.addinivalue_line("markers", "unit: marca testes unitários")
    config.addinivalue_line("markers", "integration: marca testes de integração")
    config.addinivalue_line("markers", "performance: marca testes de performance")
    config.addinivalue_line("markers", "slow: marca testes que demoram para executar")
    config.addinivalue_line("markers", "datadog: marca testes específicos do Datadog")


# Configuração de logging para testes
@pytest.fixture(autouse=True)
def configure_logging(caplog):
    """Configurar logging para capturar logs durante os testes."""
    import logging
    caplog.set_level(logging.DEBUG)
