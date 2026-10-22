import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "financial_ai.mcp_server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available MCP tools:")
            for tool in tools.tools:
                print(f"- {tool.name}")

            # The code you asked about belongs here.

            for tool_name in [
                "get_risk_intelligence",
                "compare_forecasting_models",
            ]:
                print(f"\nCalling {tool_name} for AAPL...")

                result = await session.call_tool(
                    tool_name,
                    {"ticker": "AAPL"},
                )
                print("Is error:", result.isError)
                for item in result.content:
                    if hasattr(item, "text"):
                        print(item.text)
                    else:
                        print(item)


if __name__ == "__main__":
    asyncio.run(main())
