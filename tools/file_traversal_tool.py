from langchain.tools import tool
from dotenv import load_dotenv
from utils.database import get_engine
from sqlalchemy import text

load_dotenv()


@tool
def get_tree(file_id):
    """Tool that fetches a file nodes by id from postgres db"""
    engine = get_engine()

    query = text(
        """
        SELECT
            node_id,
            parent_id,
            title
        FROM tree_nodes
        WHERE file_id = :file_id
        ORDER BY depth, position
    """
    )

    rows = []
    with engine.begin() as conn:
        rows = conn.execute(query, {"file_id": str(file_id)}).mappings().all()

    nodes = {row["node_id"]: dict(row, children=[]) for row in rows}

    nodes = {}
    roots = []

    # initialize nodes
    for r in rows:
        nodes[r["node_id"]] = {
            "node_id": r["node_id"],
            "title": r["title"],
            "child": [],
        }

    # build tree
    for r in rows:
        node_id = r["node_id"]
        parent_id = r["parent_id"]

        if parent_id and parent_id in nodes:
            nodes[parent_id]["child"].append(nodes[node_id])
        else:
            roots.append(nodes[node_id])

    # convert empty children → None
    def finalize(node):
        if not node["child"]:
            node["child"] = None
        else:
            for c in node["child"]:
                finalize(c)

    for r in roots:
        finalize(r)

    return {"root": roots}


@tool
def get_node_content(node_id):
    """Tool that fetches a node content by id from postgres db"""
    engine = get_engine()

    query = text(
        """
        SELECT content
        FROM tree_nodes
        WHERE node_id = :node_id
    """
    )

    with engine.begin() as conn:
        result = conn.execute(query, {"node_id": node_id}).scalar()

    return result


@tool
def get_node_summary(node_id):
    """Tool that fetches a node summary by id from postgres db"""
    engine = get_engine()

    query = text(
        """
        SELECT summary
        FROM tree_nodes
        WHERE node_id = :node_id
    """
    )

    with engine.begin() as conn:
        result = conn.execute(query, {"node_id": node_id}).scalar()

    return result
