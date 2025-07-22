#!/usr/bin/env python3
"""
Script para executar a conversão completa em duas etapas:
1. Limpeza HTML usando o conversor existente
2. Conversão para Markdown usando Docling
"""

import subprocess
import sys
from pathlib import Path
import shutil
import argparse
import time
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(cmd: list, description: str, capture_output: bool = True) -> tuple[bool, str]:
    """
    Executa um comando e retorna (sucesso, output)
    """
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"📋 Comando: {' '.join(cmd)}")
    print('='*60)
    
    start_time = time.time()
    
    if capture_output:
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ Sucesso em {elapsed_time:.1f}s")
            return True, result.stdout
        else:
            print(f"❌ Falha após {elapsed_time:.1f}s")
            if result.stderr:
                print("Erro:", result.stderr)
            return False, result.stderr
    else:
        # Modo interativo - mostra output em tempo real
        result = subprocess.run(cmd)
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"\n✅ Sucesso em {elapsed_time:.1f}s")
            return True, ""
        else:
            print(f"\n❌ Falha após {elapsed_time:.1f}s")
            return False, ""


def validate_environment():
    """Valida que o ambiente está configurado corretamente"""
    # Verificar se os scripts necessários existem
    scripts = ['main.py', 'docling_converter.py']
    for script in scripts:
        if not Path(script).exists():
            logger.error(f"Script não encontrado: {script}")
            return False
            
    # Verificar se as dependências estão instaladas
    try:
        import docling
        import yaml
        import bs4
    except ImportError as e:
        logger.error(f"Dependência não instalada: {e}")
        logger.info("Execute: pip install -r requirements.txt")
        return False
        
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Executa conversão Confluence → Markdown em duas etapas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Conversão básica
  python run_two_stage_conversion.py -i input/SA -o output/markdown_docling
  
  # Manter arquivos temporários para debug
  python run_two_stage_conversion.py -i input/SA -o output/markdown_docling --keep-temp
  
  # Usar diretório temporário customizado
  python run_two_stage_conversion.py -i input/SA -o output/markdown_docling --temp-dir temp/my_temp
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help='Diretório com HTML do Confluence'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help='Diretório final para Markdown'
    )
    parser.add_argument(
        '--temp-dir',
        type=Path,
        default=Path('temp/cleaned_html'),
        help='Diretório temporário para HTML limpo (padrão: temp/cleaned_html)'
    )
    parser.add_argument(
        '--keep-temp',
        action='store_true',
        help='Manter arquivos temporários após conversão'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verboso'
    )
    parser.add_argument(
        '--no-interactive',
        action='store_true',
        help='Não mostrar output interativo dos comandos'
    )
    parser.add_argument(
        '--config', '-c',
        type=Path,
        help='Arquivo de configuração YAML (opcional)'
    )
    
    args = parser.parse_args()
    
    # Validar ambiente
    if not validate_environment():
        sys.exit(1)
    
    # Validar entrada
    if not args.input.exists():
        logger.error(f"Diretório de entrada não existe: {args.input}")
        sys.exit(1)
        
    # Banner inicial
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     🚀 Conversão Confluence → Markdown (Duas Etapas)         ║
╚══════════════════════════════════════════════════════════════╝
    
📁 Entrada:        {args.input}
🔄 Temporário:     {args.temp_dir}
📁 Saída:          {args.output}
🔧 Manter temp:    {'Sim' if args.keep_temp else 'Não'}

Etapas:
1️⃣  Limpeza HTML (conversor existente)
2️⃣  Conversão Markdown (Docling)
""")
    
    # Limpar diretório temporário se existir
    if args.temp_dir.exists() and not args.keep_temp:
        logger.info(f"Limpando diretório temporário existente: {args.temp_dir}")
        shutil.rmtree(args.temp_dir)
        
    # Criar diretórios necessários
    args.temp_dir.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    
    total_start_time = time.time()
    
    # ========== ETAPA 1: Limpeza HTML ==========
    stage1_cmd = [
        sys.executable, 'main.py',
        '--input-dir', str(args.input),
        '--output-dir', str(args.temp_dir)
    ]
    
    # Adicionar configuração se fornecida
    if args.config:
        stage1_cmd.extend(['--config', str(args.config)])
    
    if args.verbose:
        stage1_cmd.extend(['--log-level', 'DEBUG'])
        
    stage1_success, _ = run_command(
        stage1_cmd,
        'Etapa 1: Limpeza HTML do Confluence',
        capture_output=args.no_interactive
    )
    
    if not stage1_success:
        logger.error("❌ Falha na Etapa 1. Abortando.")
        sys.exit(1)
        
    # Verificar se há arquivos na saída da etapa 1
    html_files = list(args.temp_dir.rglob('*.html'))
    if not html_files:
        logger.error(f"Nenhum arquivo HTML encontrado em {args.temp_dir} após Etapa 1")
        sys.exit(1)
        
    logger.info(f"✅ Etapa 1 concluída: {len(html_files)} arquivos HTML limpos")
    
    # ========== ETAPA 2: Conversão Docling ==========
    stage2_cmd = [
        sys.executable, 'docling_converter.py',
        '--input', str(args.temp_dir),
        '--output', str(args.output)
    ]
    
    if args.verbose:
        stage2_cmd.append('--verbose')
        
    stage2_success, _ = run_command(
        stage2_cmd,
        'Etapa 2: Conversão Docling (HTML → Markdown)',
        capture_output=args.no_interactive
    )
    
    if not stage2_success:
        logger.error("❌ Falha na Etapa 2.")
        if not args.keep_temp:
            logger.info("💡 Use --keep-temp para manter arquivos temporários para debug")
        sys.exit(1)
        
    # Verificar resultados
    markdown_files = list(args.output.rglob('*.md'))
    logger.info(f"✅ Etapa 2 concluída: {len(markdown_files)} arquivos Markdown criados")
    
    # Limpar temporários se solicitado
    if not args.keep_temp and args.temp_dir.exists():
        logger.info(f"🗑️  Removendo arquivos temporários em {args.temp_dir}")
        shutil.rmtree(args.temp_dir)
    elif args.keep_temp:
        logger.info(f"📁 Arquivos temporários mantidos em: {args.temp_dir}")
    
    total_elapsed = time.time() - total_start_time
    
    # Relatório final
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              ✅ Conversão Concluída com Sucesso!             ║
╚══════════════════════════════════════════════════════════════╝

📊 Resumo:
   HTML processados:     {len(html_files)}
   Markdown criados:     {len(markdown_files)}
   Taxa de conversão:    {len(markdown_files)/max(len(html_files), 1)*100:.1f}%
   Tempo total:          {total_elapsed:.1f}s

📁 Arquivos Markdown disponíveis em: {args.output}/markdown
📁 HTML limpo disponível em:         {args.output}/html
""")


if __name__ == '__main__':
    main()
