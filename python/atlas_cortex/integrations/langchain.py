import asyncio
import json
import logging
import os
import subprocess
import tempfile
from typing import List, Optional

logger = logging.getLogger("atlas_cortex.integrations.langchain")

from langchain_core.documents import Document


class AtlasCortexSplitter:
    """
    Integração Nativa do Atlas Cortex para LangChain.
    Usa o motor em Rust (AST via Tree-sitter) para quebrar o texto 
    em nós atômicos mantendo a hierarquia original (Semantic Routing).
    """

    def __init__(self, engine_path: Optional[str] = None):
        """
        Inicializa o splitter.
        
        Args:
            engine_path (str): Caminho para o binário do motor Rust. 
                               Por padrão tenta achar no repositório.
        """
        if engine_path:
            self.engine_path = engine_path
        else:
            # Assumimos que o módulo Python está no repositório Atlas Cortex
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            # Para o script python/atlas_cortex/integrations/langchain.py, base_dir sobe até a raiz
            # Windows
            exe_path = os.path.join(base_dir, "engine", "target", "release", "engine.exe")
            # Linux/Mac
            bin_path = os.path.join(base_dir, "engine", "target", "release", "engine")
            
            if os.path.exists(exe_path):
                self.engine_path = exe_path
            elif os.path.exists(bin_path):
                self.engine_path = bin_path
            else:
                raise FileNotFoundError("Binário do motor Rust não encontrado. Rode 'cargo build --release' em /engine.")

    def split_text(self, text: str) -> List[str]:
        """Quebra um texto cru usando o motor Atlas Cortex e retorna as strings"""
        docs = self.split_documents([Document(page_content=text)])
        return [doc.page_content for doc in docs]

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Interpreta objetos Document do LangChain e passa o conteúdo 
        pelo motor AST do Atlas Cortex.
        """
        final_docs = []

        for doc in documents:
            try:
                # Extrai doc_id se existir, senao None
                doc_id = doc.metadata.get("doc_id")
                
                # Chama a funcao unificada que ja lida com subprocess, doc_id fallback, e timeout
                from atlas_cortex import parse_text
                moc_data = parse_text(doc.page_content, doc_id=doc_id)
                
                nodes = moc_data.get("nodes", [])
                edges = moc_data.get("edges", [])
                
                # Pre-computa arestas de entrada e saida para acesso rapido em O(1)
                edges_out = {}
                edges_in = {}
                for edge in edges:
                    source = edge["source"]
                    target = edge["target"]
                    if source not in edges_out:
                        edges_out[source] = []
                    edges_out[source].append(edge)
                    
                    if target not in edges_in:
                        edges_in[target] = []
                    edges_in[target].append(edge)
                
                for node in nodes:
                    metadata = doc.metadata.copy()
                    node_id = node.get("id")
                    metadata['atlas_node_id'] = node_id
                    metadata['atlas_node_type'] = node.get("type")
                    metadata['atlas_node_title'] = node.get("title")
                    
                    # Salva referências diretas (RAG topology)
                    metadata['atlas_edges_out'] = edges_out.get(node_id, [])
                    metadata['atlas_edges_in'] = edges_in.get(node_id, [])
                    
                    final_docs.append(
                        Document(
                            page_content=node.get("content", ""),
                            metadata=metadata
                        )
                    )
            except Exception as e:
                logger.warning(f"Erro no motor Atlas Cortex: {e}. Fazendo fallback para o documento inteiro sem particionamento.")
                # Fallback em caso de erro grave (Devolve o original)
                final_docs.append(doc)

        return final_docs
        
    async def asplit_documents(self, documents: List[Document]) -> List[Document]:
        """
        Versão assíncrona não bloqueante de split_documents.
        Utiliza ThreadPoolExecutor para evitar travar o event loop principal.
        """
        return await asyncio.to_thread(self.split_documents, documents)
