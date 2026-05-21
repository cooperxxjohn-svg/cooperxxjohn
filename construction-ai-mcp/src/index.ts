#!/usr/bin/env node

/**
 * Construction AI MCP Server
 * Claude integration for construction takeoffs and estimates
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

import { drywallEstimateTool, handleDrywallEstimate } from "./tools/drywall.js";

// Create MCP server
const server = new Server(
  {
    name: "construction-ai",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      drywallEstimateTool,
      // More tools coming: painting, concrete, MEP, etc.
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "drywall_estimate":
        return await handleDrywallEstimate(args);

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Log to stderr (stdout is for MCP protocol)
  console.error("Construction AI MCP server running on stdio");
  console.error("Available tools: drywall_estimate");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
