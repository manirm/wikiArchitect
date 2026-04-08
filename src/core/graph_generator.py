import os
import re
import json

class GraphGenerator:
    """
    Scans a directory of Markdown files and generates a D3.js Knowledge Graph.
    Now supports zoom-aware sizing and excludes system folders.
    """
    def __init__(self, base_dir, zoom_level=1.0):
        self.base_dir = base_dir
        self.zoom_level = zoom_level
        self.nodes = []
        self.links = []
        self.node_set = set()
        
        # Folders to ignore in the knowledge graph
        self.exclude_dirs = {'.git', '__pycache__', 'venv', '.env', 'node_modules', '.uv', '.gemini', '.pytest_cache'}

    def generate_graph_html(self):
        """Builds the complete HTML/JS string for the Knowledge Graph."""
        self._scan_files()
        
        data_json = json.dumps({
            "nodes": self.nodes,
            "links": self.links
        })

        # Calculate responsive sizes based on zoom
        base_font = 10
        label_size = int(base_font * self.zoom_level)
        node_radius = int(6 * self.zoom_level)
        link_distance = int(100 * self.zoom_level)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{ margin: 0; overflow: hidden; background: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
                .node {{ cursor: pointer; }}
                .node circle {{ stroke: #fff; stroke-width: 1.5px; }}
                .link {{ stroke: #ccc; stroke-opacity: 0.6; }}
                .label {{ font-size: {label_size}px; fill: #555; pointer-events: none; font-weight: 500; }}
                #controls {{ position: absolute; top: 10px; left: 10px; background: rgba(255,255,255,0.8); padding: 5px; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div id="controls"><small>Knowledge Graph • Zoom {int(self.zoom_level*100)}%</small></div>
            <svg id="graph"></svg>
            <script>
                const data = {data_json};
                const width = window.innerWidth;
                const height = window.innerHeight;

                const svg = d3.select("#graph")
                    .attr("width", width)
                    .attr("height", height)
                    .call(d3.zoom().on("zoom", (event) => {{
                        container.attr("transform", event.transform);
                    }}));

                const container = svg.append("g");

                const simulation = d3.forceSimulation(data.nodes)
                    .force("link", d3.forceLink(data.links).id(d => d.id).distance({link_distance}))
                    .force("charge", d3.forceManyBody().strength(-200))
                    .force("center", d3.forceCenter(width / 2, height / 2));

                const link = container.append("g")
                    .attr("class", "links")
                    .selectAll("line")
                    .data(data.links)
                    .enter().append("line")
                    .attr("class", "link");

                const node = container.append("g")
                    .attr("class", "nodes")
                    .selectAll("g")
                    .data(data.nodes)
                    .enter().append("g")
                    .attr("class", "node")
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended))
                    .on("click", (event, d) => {{
                        window.location.href = "wikilink:" + d.id;
                    }});

                node.append("circle")
                    .attr("r", {node_radius})
                    .attr("fill", d => d.type === "note" ? "#4a90e2" : "#f5a623");

                node.append("text")
                    .attr("class", "label")
                    .attr("dx", {node_radius + 4})
                    .attr("dy", ".35em")
                    .text(d => d.id);

                simulation.on("tick", () => {{
                    link
                        .attr("x1", d => d.source.x)
                        .attr("y1", d => d.source.y)
                        .attr("x2", d => d.target.x)
                        .attr("y2", d => d.target.y);

                    node.attr("transform", d => `translate(${{d.x}}, ${{d.y}})`);
                }});

                function dragstarted(event, d) {{
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x; d.fy = d.y;
                }}
                function dragged(event, d) {{
                    d.fx = event.x; d.fy = event.y;
                }}
                function dragended(event, d) {{
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null; d.fy = null;
                }}
                window.addEventListener('resize', () => {{
                    svg.attr("width", window.innerWidth).attr("height", window.innerHeight);
                }});
            </script>
        </body>
        </html>
        """
        return html

    def _scan_files(self):
        """Scans the directory RECURSIVELY for .md files, ignoring system folders."""
        all_md_files = []
        for root, dirs, files in os.walk(self.base_dir):
            # Prune excluded directories in-place for efficiency
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for f in files:
                if f.endswith('.md'):
                    all_md_files.append({
                        "abs_path": os.path.join(root, f),
                        "id": f[:-3] 
                    })
        
        def normalize(name):
            return re.sub(r'[\s\-_]', '', name).lower()

        normalized_to_id = {}
        for file_info in all_md_files:
            name = file_info["id"]
            if name not in self.node_set:
                self.nodes.append({"id": name, "type": "note"})
                self.node_set.add(name)
                normalized_to_id[normalize(name)] = name

        link_pattern = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
        for file_info in all_md_files:
            source_id = file_info["id"]
            try:
                with open(file_info["abs_path"], 'r', encoding='utf-8') as f:
                    content = f.read()
                    for target_raw in link_pattern.findall(content):
                        target_norm = normalize(target_raw)
                        if target_norm in normalized_to_id:
                            self.links.append({"source": source_id, "target": normalized_to_id[target_norm]})
            except Exception: pass
