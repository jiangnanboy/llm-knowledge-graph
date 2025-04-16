import networkx as nx
import pyvis.network as net
import json


def visual_graph(triples_file: str, output_graph_file: str):
    with open(triples_file, 'r', encoding='utf-8') as file:
        triples = json.load(file)
    # 创建图对象
    G = nx.DiGraph()  # 创建一个有向图，适用于表示三元组关系
    # 添加节点和边
    for triple in triples:
        if triple['predicate'] == 'is type of':
            continue
        G.add_node(triple['subject'])
        G.add_node(triple['object'])
        G.add_edge(triple['subject'], triple['object'], label=triple['predicate'])

    # 创建pyvis网络图对象
    nt = net.Network(height="750px", width="100%", bgcolor="#222222", font_color="white")

    # 添加节点和边到pyvis网络图中
    for node in G.nodes():
        nt.add_node(node, label=node)
    for edge in G.edges(data=True):
        nt.add_edge(edge[0], edge[1], label=edge[2]['label'])
    nt.save_graph(output_graph_file)


if __name__ == "__main__":
    html_output_file = 'knowledge_graph.html'
    json_output_file = 'knowledge_graph.json'
    visual_graph(json_output_file, html_output_file)


