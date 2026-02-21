from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

search = GoogleSerperAPIWrapper()


@tool
def search_tool(query: str) -> str:
    """Tool that does a google search"""
    return search.run(query)
