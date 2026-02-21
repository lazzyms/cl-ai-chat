from agents.workflow import agent
from langchain.messages import HumanMessage
import asyncio


async def main(user_message: str):
    result = await agent.ainvoke({"messages": [HumanMessage(content=user_message)]})

    final_response = result["messages"][-1].content
    print(f"Answer: {final_response}")


if __name__ == "__main__":
    user_input = input("Enter your message: ")
    asyncio.run(main(user_input))
