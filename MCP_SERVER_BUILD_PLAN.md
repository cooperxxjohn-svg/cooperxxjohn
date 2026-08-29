# Build Construction AI MCP Server - Week 1 Plan

## Goal: Launch MCP server for Claude Desktop by end of week

**What you're building:**
- MCP server that connects Claude to construction tools
- Start with drywall, expand to all trades
- First-mover advantage in construction AI

---

## Day 1: Setup & Foundation (Today)

### Morning (3 hours): Project Setup
```bash
# Create new project
mkdir construction-ai-mcp
cd construction-ai-mcp
npm init -y

# Install MCP SDK
npm install @modelcontextprotocol/sdk

# Install dependencies
npm install typescript @types/node tsx
npm install -D @types/node

# Create structure
mkdir src
mkdir src/tools
mkdir src/utils
```

**Create files:**
- `src/index.ts` - Main MCP server
- `src/tools/drywall.ts` - Drywall estimation tool
- `src/utils/construction-api.ts` - Your backend API client
- `tsconfig.json` - TypeScript config
- `README.md` - Documentation

### Afternoon (3 hours): Build Core Server

**src/index.ts:**
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { 
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

import { drywallEstimateTool, handleDrywallEstimate } from "./tools/drywall.js";

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
      // Will add more: painting, concrete, etc.
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
  } catch (error) {
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
  console.error("Construction AI MCP server running");
}

main();
```

**src/tools/drywall.ts:**
```typescript
export const drywallEstimateTool = {
  name: "drywall_estimate",
  description: "Generate detailed drywall takeoff estimate from floor plan analysis. Returns material quantities, labor hours, and cost breakdown.",
  inputSchema: {
    type: "object",
    properties: {
      walls: {
        type: "array",
        description: "Array of detected walls with dimensions",
        items: {
          type: "object",
          properties: {
            wall_id: { type: "string" },
            length_ft: { type: "number" },
            height_ft: { type: "number" },
            type: { type: "string", enum: ["interior", "exterior", "partition"] },
            openings: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  type: { type: "string" },
                  width: { type: "number" },
                  height: { type: "number" },
                }
              }
            }
          },
          required: ["wall_id", "length_ft", "height_ft"]
        }
      },
      finish_level: {
        type: "number",
        description: "ASTM C840 finish level (0-5)",
        minimum: 0,
        maximum: 5,
        default: 4
      },
      project_type: {
        type: "string",
        description: "Type of project",
        enum: ["residential", "commercial", "industrial", "medical"],
        default: "commercial"
      }
    },
    required: ["walls"]
  }
};

export async function handleDrywallEstimate(args: any) {
  // Call your existing backend API
  const response = await fetch("http://localhost:8000/drywall/estimate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      walls: args.walls,
      ceilings: args.ceilings || [],
      finish_level: args.finish_level || 4,
      project_type: args.project_type || "commercial"
    })
  });

  const data = await response.json();

  // Format response for Claude
  return {
    content: [
      {
        type: "text",
        text: formatEstimateResponse(data)
      }
    ]
  };
}

function formatEstimateResponse(data: any): string {
  const { line_items, costs, summary } = data;

  let response = `# Drywall Estimate\n\n`;
  response += `**Project Summary:**\n`;
  response += `- Total walls: ${summary.total_walls}\n`;
  response += `- Wall square feet: ${summary.net_wall_sqft.toFixed(0)} sqft\n`;
  response += `- Ceiling square feet: ${summary.ceiling_sqft.toFixed(0)} sqft\n`;
  response += `- Total square feet: ${summary.total_sqft.toFixed(0)} sqft\n\n`;

  response += `**Cost Breakdown:**\n`;
  response += `- Materials: $${costs.material_cost.toFixed(2)}\n`;
  response += `- Labor: $${costs.labor_cost.toFixed(2)}\n`;
  response += `- Overhead (25%): $${costs.overhead.toFixed(2)}\n`;
  response += `- Profit (25%): $${costs.profit.toFixed(2)}\n`;
  response += `- **Total: $${costs.total_cost.toFixed(2)}**\n`;
  response += `- Cost per sqft: $${costs.cost_per_sqft.toFixed(2)}/sqft\n\n`;

  response += `**Detailed Line Items (${line_items.length} items):**\n\n`;

  // Group by division
  const divisions = groupBy(line_items, 'division');
  for (const [division, items] of Object.entries(divisions)) {
    response += `### ${division}\n`;
    for (const item of items.slice(0, 5)) { // First 5 items per division
      response += `- ${item.description}: ${item.quantity.toFixed(2)} ${item.unit} × $${item.unit_cost.toFixed(2)} = $${item.total_cost.toFixed(2)}\n`;
    }
    if (items.length > 5) {
      response += `- ... and ${items.length - 5} more items\n`;
    }
    response += `\n`;
  }

  return response;
}

function groupBy(array: any[], key: string) {
  return array.reduce((result, item) => {
    const group = item[key];
    if (!result[group]) result[group] = [];
    result[group].push(item);
    return result;
  }, {});
}
```

**package.json scripts:**
```json
{
  "name": "construction-ai-mcp",
  "version": "0.1.0",
  "description": "Claude MCP server for construction takeoffs",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "dev": "tsx src/index.ts",
    "prepare": "npm run build"
  },
  "bin": {
    "construction-ai-mcp": "./dist/index.js"
  }
}
```

---

## Day 2: Integration & Testing

### Morning (3 hours): Claude Desktop Integration

**Add to Claude Desktop config:**

`~/.claude/config.json` (Mac/Linux) or `%APPDATA%\Claude\config.json` (Windows):
```json
{
  "mcpServers": {
    "construction": {
      "command": "node",
      "args": ["/path/to/construction-ai-mcp/dist/index.js"],
      "env": {
        "CONSTRUCTION_API_KEY": "your_key_here"
      }
    }
  }
}
```

**Test in Claude Desktop:**
1. Restart Claude Desktop
2. In chat: "Use the construction tool to estimate drywall for a 20x15 room with 9ft ceilings, one door, two windows"
3. Claude should call your MCP tool
4. Returns estimate

### Afternoon (3 hours): Add AI Detection Integration

**Update drywall tool to accept floor plan images:**

```typescript
// Add new tool for full workflow
export const analyzeFloorPlanTool = {
  name: "analyze_floor_plan",
  description: "Analyze floor plan image and generate complete drywall estimate",
  inputSchema: {
    type: "object",
    properties: {
      image_url: {
        type: "string",
        description: "URL or base64 of floor plan image"
      },
      finish_level: { type: "number", default: 4 },
      project_type: { type: "string", default: "commercial" }
    },
    required: ["image_url"]
  }
};

export async function handleAnalyzeFloorPlan(args: any) {
  // Step 1: Detect walls using your AI
  const detectionResponse = await fetch("http://localhost:8000/drywall/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_url: args.image_url })
  });
  const detection = await detectionResponse.json();

  // Step 2: Generate estimate
  const estimateResponse = await fetch("http://localhost:8000/drywall/estimate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      walls: detection.walls,
      ceilings: detection.ceilings,
      finish_level: args.finish_level,
      project_type: args.project_type
    })
  });
  const estimate = await estimateResponse.json();

  return {
    content: [{
      type: "text",
      text: formatFullAnalysis(detection, estimate)
    }]
  };
}
```

---

## Day 3: Documentation & Polish

### Morning (3 hours): Write Docs

**README.md:**
```markdown
# Construction AI - Claude MCP Server

AI-powered construction takeoffs for contractors. Connect Claude to professional estimating tools.

## Features
- 🏗️ Drywall takeoff estimates (40 seconds vs 4 hours)
- 📊 127+ detailed line items
- 💰 Material + labor + cost breakdown
- 🔧 More trades coming soon (painting, concrete, MEP)

## Installation

### Prerequisites
- Node.js 18+
- Claude Desktop

### Quick Start
```bash
npm install -g construction-ai-mcp
```

### Configuration
Add to Claude Desktop config (`~/.claude/config.json`):
```json
{
  "mcpServers": {
    "construction": {
      "command": "construction-ai-mcp"
    }
  }
}
```

Restart Claude Desktop.

## Usage

### Drywall Estimate
```
Ask Claude: "Estimate drywall for a 20x15 room, 9ft ceilings, 
one 3x7 door, two 4x3 windows. Commercial Level 4 finish."

Claude will call the drywall_estimate tool and return:
- Material quantities (sheets, compound, tape)
- Labor hours by phase
- Complete cost breakdown
```

### Floor Plan Analysis
```
Ask Claude: "Analyze this floor plan for drywall scope"
[Attach image]

Claude will:
1. Detect all walls
2. Calculate materials
3. Generate estimate
```

## Tools Available

### `drywall_estimate`
Generate detailed drywall takeoff from wall dimensions.

### `analyze_floor_plan`
Analyze floor plan image and create complete estimate.

## Pricing
- Free: 3 estimates/month
- Pro: $149/mo unlimited estimates
- Enterprise: Custom

Get API key at: construction-ai.com

## Support
- Email: support@construction-ai.com
- Discord: discord.gg/construction-ai
- Docs: docs.construction-ai.com

## Roadmap
- [x] Drywall estimates
- [ ] Painting estimates (Week 2)
- [ ] Concrete estimates (Week 3)
- [ ] MEP estimates (Week 4)
- [ ] Bluebeam integration (Month 2)
- [ ] Procore integration (Month 3)
```

### Afternoon (3 hours): Demo Video

**Record 2-minute demo:**
1. Show Claude Desktop
2. "Watch me estimate a drywall project in 40 seconds"
3. Ask Claude to analyze floor plan
4. Show detailed estimate output
5. "This used to take 4 hours manually"
6. Call to action: "Install at construction-ai.com"

Upload to YouTube, embed on website.

---

## Day 4: Launch Prep

### Morning (3 hours): Website

**Simple landing page:**
```html
<h1>Construction AI</h1>
<h2>Claude, but it knows construction</h2>

<p>AI-powered takeoffs for contractors. Connect Claude Desktop to 
professional estimating tools.</p>

<video src="demo.mp4"></video>

<h3>Features</h3>
- Drywall estimates in 40 seconds
- 127+ detailed line items
- Export to Excel/PDF
- More trades coming soon

<h3>Install</h3>
npm install -g construction-ai-mcp

<h3>Pricing</h3>
- Free: 3 estimates/month
- Pro: $149/mo unlimited

<button>Get Started</button>
```

Deploy to Vercel/Netlify (free).

### Afternoon (3 hours): Publish

**1. Publish to npm:**
```bash
npm login
npm publish
```

**2. Open source on GitHub:**
```bash
git init
git add .
git commit -m "Initial release: Construction AI MCP server"
git remote add origin https://github.com/yourusername/construction-ai-mcp
git push -u origin main
```

**3. Add to Anthropic MCP directory:**
- Fork: https://github.com/anthropics/awesome-mcp-servers
- Add your server to README
- Submit PR

---

## Day 5: Soft Launch

### Morning (2 hours): Social Media

**Twitter/X thread:**
```
I built a Claude MCP server for construction contractors 🏗️

Contractors spend 3-4 hours creating takeoff estimates manually.

With Claude + Construction AI:
- Upload floor plan
- 40 seconds later → 127 detailed line items
- Export to Excel

Demo 👇
[video]

Install: npm install -g construction-ai-mcp

Open source: github.com/you/construction-ai-mcp
```

**Post to:**
- Twitter/X
- LinkedIn
- r/ClaudeAI
- r/Contractors
- Anthropic Discord (#mcp-showcase)

### Afternoon (3 hours): Get First Users

**Outreach:**
- Message 10 contractors from earlier outreach
- "Remember when I showed you the estimate demo? It's now a Claude plugin."
- Send installation link
- Offer to help them set up

**Goal: 10 installs by end of day**

---

## Day 6-7: Iterate

### Collect Feedback
- [ ] Watch users install it (screen share)
- [ ] What breaks?
- [ ] What's confusing?
- [ ] What's missing?

### Fix Issues
- [ ] Installation problems
- [ ] Error handling
- [ ] Output formatting
- [ ] Performance

### Document Issues
- Create GitHub issues
- Prioritize fixes
- Ship updates

---

## Week 2: Expand

### Add Second Trade (Painting)
```typescript
export const paintingEstimateTool = {
  name: "painting_estimate",
  description: "Generate painting estimate from room dimensions",
  // Similar to drywall
};
```

### Add Third Trade (Concrete)
```typescript
export const concreteEstimateTool = {
  name: "concrete_estimate", 
  description: "Estimate concrete foundations and slabs",
  // Similar pattern
};
```

---

## Success Metrics

### Week 1:
- [ ] MCP server published to npm
- [ ] Open source on GitHub
- [ ] 10+ installs
- [ ] 3+ active users
- [ ] Demo video live

### Month 1:
- [ ] 100+ installs
- [ ] 50+ GitHub stars
- [ ] 20+ active users
- [ ] 3 trades (drywall, painting, concrete)
- [ ] 5+ testimonials

### Month 3:
- [ ] 1K+ installs
- [ ] 500+ active users
- [ ] Submit to Anthropic partnership
- [ ] Featured in marketplace

---

## Critical Path

**Must have this week:**
1. Working MCP server (Day 1-2)
2. Claude Desktop integration (Day 2)
3. Documentation (Day 3)
4. Published to npm (Day 4)
5. First 10 users (Day 5)

**Can wait:**
- Perfect pricing page
- Multiple trades
- Integrations
- Official partnership

**Get it working, get it shipped, get users.**

You have the backend. Just need to wrap it in MCP protocol.

Start today. Ship by Friday.
