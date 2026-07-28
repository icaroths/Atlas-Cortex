import sys
import os
import pytest

# Adiciona a raiz do projeto ao sys.path para importar os scripts
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from scripts.benchmark_token_efficiency import retrieve_top_k

def test_retrieve_top_k_empty_corpus():
    result = retrieve_top_k([], "qualquer pergunta", 3)
    assert result == [], "Corpus vazio deve retornar lista vazia"

def test_retrieve_top_k_no_match():
    corpus = ["texto sobre maçãs", "texto sobre laranjas"]
    # A query não tem NENHUMA palavra em comum com o corpus (nem 'sobre', nem 'texto')
    result = retrieve_top_k(corpus, "fale apenas bananas", 1)
    assert result == [], "Query sem interseção deve retornar lista vazia"

def test_retrieve_top_k_correct_match():
    corpus = [
        "O Atlas Cortex usa Tree-sitter para AST.",
        "O Langchain usa RecursiveCharacterTextSplitter.",
        "LLMs sofrem de colapso de contexto."
    ]
    query = "O que o Atlas Cortex usa?"
    result = retrieve_top_k(corpus, query, top_k=1)
    
    assert len(result) == 1
    assert "Tree-sitter" in result[0], "Deve recuperar o nó que fala sobre o Atlas Cortex"
