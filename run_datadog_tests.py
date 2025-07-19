#!/usr/bin/env python3
"""
Script para execução dos testes do Datadog
===========================================

Este script fornece diferentes opções para executar os testes de conexão
com Datadog, incluindo testes unitários, de performance e de integração.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Executa um comando e exibe o resultado."""
    print(f"\n{'='*60}")
    print(f"🔧 {description if description else 'Executando comando'}")
    print(f"{'='*60}")
    print(f"Comando: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent, check=True, capture_output=False)
        print(f"\n✅ {description} - SUCESSO!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - FALHOU! (código de saída: {e.returncode})")
        return False
    except FileNotFoundError:
        print(f"\n❌ Comando não encontrado: {cmd[0]}")
        return False


def install_dependencies():
    """Instala dependências necessárias para os testes."""
    deps = [
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0", 
        "pytest-cov>=4.1.0",
        "pytest-timeout>=2.1.0",
        "psutil>=5.9.0"
    ]
    
    cmd = [sys.executable, "-m", "pip", "install"] + deps
    return run_command(cmd, "Instalando dependências de teste")


def run_unit_tests():
    """Executa apenas testes unitários."""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_datadog_connection.py",
        "-m", "unit or not (performance or slow)",
        "-v", "--tb=short"
    ]
    return run_command(cmd, "Executando testes unitários do Datadog")


def run_performance_tests():
    """Executa testes de performance."""
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_datadog_performance.py",
        "-m", "performance",
        "-v", "--tb=short", "-x"
    ]
    return run_command(cmd, "Executando testes de performance do Datadog")


def run_all_datadog_tests():
    """Executa todos os testes relacionados ao Datadog."""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_datadog_connection.py",
        "tests/test_datadog_performance.py", 
        "-v", "--tb=short",
        "--cov=tools", "--cov-report=term-missing",
        "--cov-report=html:htmlcov/datadog"
    ]
    return run_command(cmd, "Executando todos os testes do Datadog")


def run_integration_tests():
    """Executa testes de integração."""
    cmd = [
        sys.executable, "-m", "pytest",
        "-m", "integration",
        "-v", "--tb=short"
    ]
    return run_command(cmd, "Executando testes de integração")


def run_quick_tests():
    """Executa apenas testes rápidos (exclui performance e slow)."""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_datadog_connection.py",
        "-m", "not (performance or slow)",
        "-v", "--tb=line", "-x"
    ]
    return run_command(cmd, "Executando testes rápidos do Datadog")


def run_stress_tests():
    """Executa testes de stress/carga."""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_datadog_performance.py",
        "-m", "slow",
        "-v", "--tb=short", "-s"
    ]
    return run_command(cmd, "Executando testes de stress do Datadog")


def check_test_environment():
    """Verifica se o ambiente está configurado para testes."""
    print("\n🔍 Verificando ambiente de teste...")
    
    # Verificar se pytest está instalado
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__} instalado")
    except ImportError:
        print("❌ pytest não está instalado")
        return False
    
    # Verificar estrutura de diretórios
    tests_dir = Path(__file__).parent / "tests"
    if not tests_dir.exists():
        print(f"❌ Diretório de testes não encontrado: {tests_dir}")
        return False
    print(f"✅ Diretório de testes encontrado: {tests_dir}")
    
    # Verificar arquivos de teste
    test_files = [
        "test_datadog_connection.py",
        "test_datadog_performance.py",
        "conftest.py"
    ]
    
    for test_file in test_files:
        file_path = tests_dir / test_file
        if file_path.exists():
            print(f"✅ {test_file} encontrado")
        else:
            print(f"❌ {test_file} não encontrado")
            return False
    
    # Verificar arquivo tools.py
    tools_file = Path(__file__).parent / "tools.py"
    if tools_file.exists():
        print(f"✅ tools.py encontrado")
    else:
        print(f"❌ tools.py não encontrado")
        return False
    
    print("\n✅ Ambiente de teste verificado com sucesso!")
    return True


def generate_test_report():
    """Gera relatório completo de testes."""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_datadog_connection.py",
        "tests/test_datadog_performance.py",
        "--cov=tools", 
        "--cov-report=html:htmlcov/datadog",
        "--cov-report=xml:coverage.xml",
        "--junit-xml=junit.xml",
        "--tb=short"
    ]
    return run_command(cmd, "Gerando relatório completo de testes")


def main():
    parser = argparse.ArgumentParser(
        description="Script para executar testes de conexão com Datadog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python run_datadog_tests.py --check          # Verificar ambiente
  python run_datadog_tests.py --install        # Instalar dependências  
  python run_datadog_tests.py --unit           # Testes unitários
  python run_datadog_tests.py --performance    # Testes de performance
  python run_datadog_tests.py --quick          # Testes rápidos
  python run_datadog_tests.py --all            # Todos os testes
  python run_datadog_tests.py --report         # Gerar relatório
        """
    )
    
    parser.add_argument("--check", action="store_true",
                       help="Verificar configuração do ambiente de teste")
    parser.add_argument("--install", action="store_true",
                       help="Instalar dependências necessárias")
    parser.add_argument("--unit", action="store_true", 
                       help="Executar apenas testes unitários")
    parser.add_argument("--performance", action="store_true",
                       help="Executar testes de performance")
    parser.add_argument("--integration", action="store_true",
                       help="Executar testes de integração") 
    parser.add_argument("--quick", action="store_true",
                       help="Executar testes rápidos (exclui performance/slow)")
    parser.add_argument("--stress", action="store_true",
                       help="Executar testes de stress/carga")
    parser.add_argument("--all", action="store_true",
                       help="Executar todos os testes do Datadog")
    parser.add_argument("--report", action="store_true",
                       help="Gerar relatório completo de testes")
    
    args = parser.parse_args()
    
    print("🚀 SRE Copilot - Testes de Conexão com Datadog")
    print("=" * 60)
    
    success = True
    
    # Se nenhum argumento foi fornecido, mostrar ajuda
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # Verificar ambiente
    if args.check:
        success &= check_test_environment()
    
    # Instalar dependências
    if args.install:
        success &= install_dependencies()
    
    # Executar testes específicos
    if args.unit:
        success &= run_unit_tests()
    
    if args.performance:
        success &= run_performance_tests()
    
    if args.integration:
        success &= run_integration_tests()
    
    if args.quick:
        success &= run_quick_tests()
    
    if args.stress:
        success &= run_stress_tests()
        
    if args.all:
        success &= run_all_datadog_tests()
    
    if args.report:
        success &= generate_test_report()
        
        # Mostrar localização do relatório
        report_path = Path(__file__).parent / "htmlcov" / "datadog" / "index.html"
        if report_path.exists():
            print(f"\n📊 Relatório HTML disponível em: {report_path.absolute()}")
    
    # Resultado final
    print("\n" + "=" * 60)
    if success:
        print("✅ TESTES CONCLUÍDOS COM SUCESSO!")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        sys.exit(1)


if __name__ == "__main__":
    main()
