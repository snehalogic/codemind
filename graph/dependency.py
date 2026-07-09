import networkx as nx
from pyvis.network import Network
from pathlib import Path


def build_dependency_graph(parsed_files: list[dict]) -> nx.DiGraph:
    """Build a directed dependency graph from parsed files using import relationships."""
    G = nx.DiGraph()

    file_modules = {}
    for f in parsed_files:
        module_name = f["relative_path"].replace("\\", ".").replace("/", ".").replace(".py", "")
        file_modules[module_name] = f["relative_path"]
        G.add_node(f["relative_path"], label=Path(f["relative_path"]).name)

    for f in parsed_files:
        source = f["relative_path"]
        for imp in f["imports"]:
            for module, path in file_modules.items():
                if imp.startswith(module) or module.endswith(imp.split(".")[0]):
                    if source != path:
                        G.add_edge(source, path)
                    break

    return G


def get_graph_stats(G: nx.DiGraph) -> dict:
    """Return stats about the graph including node/edge counts and most imported files."""
    return {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "most_imported": sorted(G.in_degree(), key=lambda x: x[1], reverse=True)[:5],
        "most_dependent": sorted(G.out_degree(), key=lambda x: x[1], reverse=True)[:5]
    }


def visualize_graph(G: nx.DiGraph, output_path: str = "codemind_graph.html"):
    """Generate an interactive HTML visualization of the dependency graph using Pyvis."""
    net = Network(height="800px", width="100%", directed=True, bgcolor="#1e1e1e", font_color="white")
    net.barnes_hut(spring_length=200)

    in_degrees = dict(G.in_degree())

    for node in G.nodes():
        label = Path(node).name
        degree = in_degrees.get(node, 0)

        if degree > 10:
            color = "#534AB7"
            size = 30
        elif degree > 5:
            color = "#1D9E75"
            size = 20
        else:
            color = "#888780"
            size = 12

        net.add_node(node, label=label, color=color, size=size, title=node)

    for edge in G.edges():
        net.add_edge(edge[0], edge[1], color="#444441")

    net.save_graph(output_path)
    print(f"Graph saved to {output_path} — open it in your browser!")


if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from ingestion.cloner import clone_repo, walk_repo
    from ingestion.parser import parse_repo

    repo_path = clone_repo("https://github.com/tiangolo/fastapi")
    files = walk_repo(repo_path)
    parsed = parse_repo(files)

    G = build_dependency_graph(parsed)
    stats = get_graph_stats(G)

    print(f"\n--- Graph Stats ---")
    print(f"Nodes (files): {stats['total_nodes']}")
    print(f"Edges (dependencies): {stats['total_edges']}")
    print(f"\nMost imported files:")
    for node, count in stats['most_imported']:
        print(f"  {Path(node).name}: imported by {count} files")

    visualize_graph(G)