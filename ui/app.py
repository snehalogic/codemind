```python
import sys
import os
import shlex
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from ingestion.cloner import clone_repo, walk_repo
from ingestion.parser import parse_repo
from graph.dependency import build_dependency_graph, get_graph_stats, visualize_graph
from rag.embedder import build_vector_store, query_vector_store
from llm.groq_llm import ask_codebase

st.set_page_config(
    page_title="CodeMind",
    page_icon="",
    layout="wide"
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 600; color: #534AB7; }
    .sub-header { font-size: 1rem; color: #888780; margin-top: -1rem; }
    .stat-box { background: #f8f7ff; border: 0.5px solid #AFA9EC;
                border-radius: 10px; padding: 1rem; text-align: center; }
    .stat-number { font-size: 1.8rem; font-weight: 600; color: #534AB7; }
    .stat-label { font-size: 0.8rem; color: #888780; }
    .chat-msg-user { background: #EEEDFE; border-radius: 10px;
                     padding: 0.75rem 1rem; margin: 0.5rem 0; color: #26215C; }
    .chat-msg-ai { background: #f0f0f0; border-radius: 10px;
                   padding: 0.75rem 1rem; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

if "analyzed" not in st.session_state:
    st.session_state.analyzed = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "repo_stats" not in st.session_state:
    st.session_state.repo_stats = {}
if "graph_stats" not in st.session_state:
    st.session_state.graph_stats = {}
if "repo_name" not in st.session_state:
    st.session_state.repo_name = ""

st.markdown('<div class="main-header">CodeMind</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Paste any GitHub repo — AI explains everything</div>', unsafe_allow_html=True)
st.markdown("---")

with st.sidebar:
    st.markdown("### Analyze a Repo")
    repo_url = st.text_input("GitHub URL", placeholder="https://github.com/user/repo")
    analyze_btn = st.button("Analyze", use_container_width=True, type="primary")

    if analyze_btn and repo_url:
        with st.spinner("Cloning repo..."):
            repo_path = clone_repo(repo_url)
            files = walk_repo(repo_path)
            st.session_state.repo_name = repo_url.rstrip("/").split("/")[-1]

        with st.spinner("Parsing code structure..."):
            parsed = parse_repo(files)

        with st.spinner("Building dependency graph..."):
            G = build_dependency_graph(parsed)
            stats = get_graph_stats(G)
            visualize_graph(G, output_path="ui/codemind_graph.html")
            st.session_state.graph_stats = stats

        with st.spinner("Building AI knowledge base..."):
            python_files = [f for f in files if f["extension"] == ".py"]
            build_vector_store(python_files)
            st.session_state.repo_stats = {
                "total_files": len(files),
                "python_files": len(python_files),
                "total_chars": sum(f["size"] for f in files),
            }

        st.session_state.analyzed = True
        st.session_state.chat_history = []
        st.success("Ready! Ask anything below.")

    if st.session_state.analyzed:
        st.markdown("---")
        st.markdown("### Repo Stats")
        st.metric("Total Files", st.session_state.repo_stats.get("total_files", 0))
        st.metric("Python Files", st.session_state.repo_stats.get("python_files", 0))
        st.metric("Graph Nodes", st.session_state.graph_stats.get("total_nodes", 0))
        st.metric("Dependencies", st.session_state.graph_stats.get("total_edges", 0))

        st.markdown("---")
        st.markdown("### Most Imported")
        for node, count in st.session_state.graph_stats.get("most_imported", []):
            from pathlib import Path
            st.markdown(f"`{Path(node).name}` — {count} imports")

if not st.session_state.analyzed:
    st.info("Paste a GitHub URL in the sidebar and click Analyze to get started.")
    st.markdown("""
    ### What CodeMind can do:
    - Understand every file, class, and function in any repo
    - Visualize the full dependency graph
    - Answer any question about the codebase
    - Explain architecture, data flow, and more
    """)

else:
    tab1, tab2, tab3 = st.tabs(["Chat", "Dependency Graph", "File Stats"])

    with tab1:
        st.markdown(f"### Chatting with `{st.session_state.repo_name}`")

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.info(f" {msg['content']}")
            else:
                st.success(f" {msg['content']}")

        st.markdown("**Suggested questions:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("How does routing work?"):
                st.session_state.prefill = "How does routing work?"
        with col2:
            if st.button("How is auth handled?"):
                st.session_state.prefill = "How is authentication handled?"
        with col3:
            if st.button("What are the core classes?"):
                st.session_state.prefill = "What are the core classes?"

        prefill_val = st.session_state.get("prefill", "")
        question = st.text_input("Ask anything about this codebase...", value=prefill_val)

        if question or prefill_val:
            # Validate the input to prevent command injection attacks
            q = shlex.quote(question or prefill_val)
            st.session_state.prefill = ""
            st.session_state.chat_history.append({"role": "user", "content": q})

            with st.spinner("CodeMind is thinking..."):
                answer = ask_codebase(q)

            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

    with tab2:
        st.markdown("### Dependency Graph")
        try:
            with open("ui/codemind_graph.html", "r", encoding="utf-8") as f:
                graph_html = f.read()
            st.components.v1.html(graph_html, height=600, scrolling=True)
        except:
            st.info("Graph will appear here after analysis.")

    with tab3:
        st.markdown("### File Breakdown")
        st.metric("Total Characters", f"{st.session_state.repo_stats.get('total_chars', 0):,}")
        st.markdown("**Most imported files:**")
        for node, count in st.session_state.graph_stats.get("most_imported", []):
            from pathlib import Path
            st.progress(min(count / 500, 1.0), text=f"{Path(node).name} ({count} imports)")
```