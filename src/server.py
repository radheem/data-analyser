from mcp.server.fastmcp import FastMCP

# Instantiate the FastMCP server
mcp = FastMCP("political-ads-mcp")

if __name__ == "__main__":
    mcp.run()
