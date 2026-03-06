from typing import List

from pydantic import BaseModel


class Tree(BaseModel):
    """
    A simple tree structure to represent the hierarchical organization of document sections.
    """

    node_id: str
    title: str
    content: str
    summary: str
    children: List["Tree"] = []
