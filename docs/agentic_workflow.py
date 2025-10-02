from diagrams import Cluster, Diagram
from diagrams.custom import Custom

BASE_PATH: str = "./docs/assets/"

graph_attr: dict[str, str] = {
    "fontname": "Arial",
    "fontcolor": "black",
    "style": "bold",
    "bgcolor": "transparent",
}

node_attr: dict[str, str] = {
    "fontname": "Arial",
    "fontcolor": "black",
    "style": "bold",
}

with Diagram(
    "Document Redaction Pipeline Stages",
    show=False,
    filename=f"{BASE_PATH}agentic_workflow",
    direction="LR",
    outformat="png",
    graph_attr=graph_attr,
    node_attr=node_attr,
):
    # User Input → Raw Contract
    with Cluster("Agentic Workflow"), Cluster("User Input"), Cluster("Raw Contract"):
        user = Custom("Document", "user_pdf.png")

    # Stage 1 → Conversion Agent
    with Cluster("Agentic Workflow"), Cluster("Stage 1: Markdown Conversion"), Cluster("Conversion Agent"):
        converted_md = Custom("Converted\nMarkdown", "markdown.png")

    # Stage 2 → Detection Agent
    with Cluster("Agentic Workflow"), Cluster("Stage 2: Sensitive Data\nDetection"), Cluster("Detection Agent"):
        detection_json = Custom("Sensitive Data\nJSON", "json.png")

    # Stage 3 → Redaction Agent
    with Cluster("Agentic Workflow"), Cluster("Stage 3: Document Redaction"), Cluster("Redaction Agent"):
        redacted_md = Custom("Redacted\nMarkdown", "markdown.png")

    # Main process flow
    user >> converted_md >> [detection_json >> redacted_md]

    [converted_md >> detection_json]

    # [converted_md >> Edge(label="confirmation", color="brown", style="dashed") << user]
    # [redacted_md >> Edge(label="confirmation", color="brown", style="dashed") << user]
