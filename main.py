from agents.workflow import agent
from langchain.messages import HumanMessage
import asyncio


async def main(user_message: str):
    # result = await agent.ainvoke({"messages": [HumanMessage(content=user_message)]})

    async for event in agent.astream(
        {"messages": [HumanMessage(content=user_message)]}, stream_mode="updates"
    ):
        for node_name, node_output in event.items():
            if node_name == "agent" and "messages" in node_output:
                message = node_output["messages"][-1]
                if hasattr(message, "content") and message.content:
                    if not hasattr(message, "tool_calls") or not message.tool_calls:
                        print(message.content, end="", flush=True)

        print()
    # final_response = result["messages"][-1].content
    # print(f"Answer: {final_response}")


if __name__ == "__main__":
    print("Chat started. Type 'exit' or Ctrl+C to stop/quit.")
    while True:
        user_input = input("👨: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "bye"}:
            print("🤖: Goodbye!")
            break

        asyncio.run(main(user_input))
