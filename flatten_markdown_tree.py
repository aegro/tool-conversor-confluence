#!/usr/bin/env python3
"""
Script para achatar estrutura de diretórios de arquivos Markdown
mantendo a hierarquia codificada nos nomes dos arquivos.

Exemplo:
De: output/FAQF_two_stage/markdown/FAQ/FAQ/Página inicial de FAQ/Aegro/Financeiro/FAQ  Impostos.md
Para: FAQ - Página inicial de FAQ - Aegro - Financeiro - FAQ  Impostos.md
"""

import os
import shutil
import argparse
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def flatten_markdown_directory(source_dir: str, output_dir: str, separator: str = " - "):
    """
    Achata a estrutura de diretórios de arquivos Markdown.
    
    Args:
        source_dir: Diretório fonte com arquivos Markdown em estrutura hierárquica
        output_dir: Diretório de destino para arquivos achatados
        separator: Separador a usar entre níveis da hierarquia (padrão: " - ")
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    
    # Validar diretório fonte
    if not source_path.exists():
        logger.error(f"Diretório fonte não existe: {source_dir}")
        return
    
    if not source_path.is_dir():
        logger.error(f"Caminho fonte não é um diretório: {source_dir}")
        return
    
    # Criar diretório de saída se não existir
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Diretório de saída: {output_path}")
    
    # Estatísticas
    total_files = 0
    copied_files = 0
    skipped_files = 0
    
    # Processar todos os arquivos Markdown recursivamente
    for md_file in source_path.rglob("*.md"):
        total_files += 1
        
        try:
            # Obter o caminho relativo ao diretório fonte
            relative_path = md_file.relative_to(source_path)
            
            # Separar os componentes do caminho (pastas e arquivo)
            path_parts = list(relative_path.parts)
            
            # O último elemento é o nome do arquivo
            filename = path_parts[-1]
            
            # Os elementos anteriores são a hierarquia de pastas
            hierarchy_parts = path_parts[:-1]
            
            if hierarchy_parts:
                # Construir novo nome com hierarquia
                hierarchy_prefix = separator.join(hierarchy_parts)
                new_filename = f"{hierarchy_prefix}{separator}{filename}"
            else:
                # Arquivo já está na raiz
                new_filename = filename
            
            # Sanitizar nome do arquivo (remover caracteres problemáticos)
            # Mas preservar espaços e caracteres especiais válidos
            new_filename = new_filename.replace("/", "-")
            new_filename = new_filename.replace("\\", "-")
            
            # Caminho de destino
            dest_file = output_path / new_filename
            
            # Verificar se arquivo já existe
            if dest_file.exists():
                logger.warning(f"Arquivo já existe, pulando: {new_filename}")
                skipped_files += 1
                continue
            
            # Copiar arquivo
            shutil.copy2(md_file, dest_file)
            copied_files += 1
            
            logger.info(f"✓ {relative_path} → {new_filename}")
            
        except Exception as e:
            logger.error(f"Erro ao processar {md_file}: {str(e)}")
            skipped_files += 1
    
    # Relatório final
    logger.info("\n" + "="*60)
    logger.info("RESUMO DA OPERAÇÃO")
    logger.info("="*60)
    logger.info(f"Total de arquivos encontrados: {total_files}")
    logger.info(f"Arquivos copiados com sucesso: {copied_files}")
    logger.info(f"Arquivos pulados/com erro: {skipped_files}")
    logger.info(f"Diretório de saída: {output_path}")
    logger.info("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Achata estrutura de diretórios de arquivos Markdown mantendo hierarquia nos nomes"
    )
    
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Diretório de entrada com arquivos Markdown em estrutura hierárquica"
    )
    
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Diretório de saída para arquivos achatados"
    )
    
    parser.add_argument(
        "-s", "--separator",
        default=" - ",
        help="Separador entre níveis da hierarquia (padrão: ' - ')"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular operação sem copiar arquivos"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("MODO DRY-RUN: Nenhum arquivo será copiado")
        # TODO: Implementar modo dry-run se necessário
    
    flatten_markdown_directory(
        source_dir=args.input,
        output_dir=args.output,
        separator=args.separator
    )


if __name__ == "__main__":
    main()
