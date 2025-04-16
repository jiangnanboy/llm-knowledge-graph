"""
Knowledge Graph Generator and Visualizer.

A tool that takes text input and generates an interactive knowledge graph visualization.
"""

from src.knowledge_graph.visualization import visual_graph
from src.knowledge_graph.llm import call_llm, extract_json_from_text
from src.knowledge_graph.config import load_config

__version__ = "0.1.0"
