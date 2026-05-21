# Claude Desktop Setup Guide

## Quick Start

Follow these steps to connect Construction AI to Claude Desktop.

---

## Step 1: Build the MCP Server

```bash
cd construction-ai-mcp
npm install
npm run build
```

This creates `dist/index.js` - the executable MCP server.

---

## Step 2: Find Your Claude Config File

**Mac/Linux:**
```bash
~/.claude/config.json
```

**Windows:**
```
%APPDATA%\Claude\config.json
```

If the file doesn't exist, create it.

---

## Step 3: Add Construction AI to Config

Edit your `config.json` file:

```json
{
  "mcpServers": {
    "construction": {
      "command": "node",
      "args": ["/FULL/PATH/TO/construction-ai-mcp/dist/index.js"]
    }
  }
}
```

**Important:** Replace `/FULL/PATH/TO/` with the actual path on your system.

### Example (Mac):
```json
{
  "mcpServers": {
    "construction": {
      "command": "node",
      "args": ["/Users/john/projects/construction-ai-mcp/dist/index.js"]
    }
  }
}
```

### Example (Windows):
```json
{
  "mcpServers": {
    "construction": {
      "command": "node",
      "args": ["C:\\Users\\John\\projects\\construction-ai-mcp\\dist\\index.js"]
    }
  }
}
```

---

## Step 4: Restart Claude Desktop

Close and reopen Claude Desktop completely.

---

## Step 5: Test the Integration

Ask Claude:

```
Estimate drywall for a 20x15 room with 9ft ceilings, 
one 3x7 door, and two 4x3 windows. Commercial Level 4 finish.
```

Claude should:
1. Recognize this as a drywall estimation task
2. Call the `drywall_estimate` tool
3. Return a detailed breakdown with:
   - Material quantities
   - Labor hours
   - Cost breakdown
   - Total estimate

---

## Troubleshooting

### "Tool not found" or Claude doesn't use the tool

1. **Check the path:** Make sure the path in config.json is absolute and correct
2. **Rebuild:** Run `npm run build` again
3. **Verify Node.js:** Run `node --version` (need 18+)
4. **Check logs:** Look for MCP server startup messages in Claude Desktop logs

### Permission errors

Make sure the dist/index.js file is executable:
```bash
chmod +x dist/index.js
```

### MCP server not starting

Test manually:
```bash
node dist/index.js
```

You should see:
```
Construction AI MCP server running on stdio
Available tools: drywall_estimate
```

If it crashes, check:
- Node.js version (18+)
- Dependencies installed (`npm install`)
- TypeScript compiled correctly (`npm run build`)

---

## Example Prompts to Try

### Simple Room
```
Estimate drywall for a 12x10 office with 9ft ceilings, 
one door, one window. Level 4 finish.
```

### Multi-Room Project
```
I have 3 offices to drywall:
- Office 1: 12x10, 9ft ceiling, one door, one window
- Office 2: 15x12, 9ft ceiling, one door, two windows  
- Office 3: 14x11, 9ft ceiling, one door, one window

All need Level 4 finish. What's the total estimate?
```

### From Floor Plan Description
```
I have an office renovation:
- North wall: 40ft long, 9ft high, four 3x7 doors
- South wall: 40ft long, 9ft high, no openings
- East wall: 30ft long, 9ft high, three 4x3 windows
- West wall: 30ft long, 9ft high, no openings
- Ceiling: 1,200 sqft

Generate drywall estimate for Level 4 finish.
```

---

## What You Get

Every estimate includes:

### Project Summary
- Total walls and square footage
- Wall area vs ceiling area breakdown

### Materials
- Drywall sheets (4'×8' count)
- Joint compound (lbs)
- Paper tape (linear feet)
- Screws (quantity)

### Labor Breakdown
- Hanging hours
- Taping hours
- Finishing hours
- Total labor hours

### Cost Breakdown
- Materials cost
- Labor cost
- Overhead (25%)
- Profit (25%)
- **Total cost**
- **Cost per square foot**

---

## Advanced Usage

### Specify Finish Level

```
Estimate drywall with Level 5 finish for high-end residential
```

Finish levels (ASTM C840):
- **Level 0:** No finishing
- **Level 1:** Tape only
- **Level 2:** Tape + one coat
- **Level 3:** Tape + two coats
- **Level 4:** Tape + three coats (standard commercial)
- **Level 5:** Tape + skim coat (high-end, critical lighting)

### Specify Project Type

```
Estimate for medical facility (higher labor rates)
```

Project types:
- **residential:** $60-65/hr labor
- **commercial:** $65-70/hr labor (default)
- **industrial:** $70-75/hr labor
- **medical:** $75-80/hr labor
- **institutional:** $70-75/hr labor

---

## Uninstall

Remove from Claude config:

1. Edit `~/.claude/config.json`
2. Delete the `"construction"` entry
3. Restart Claude Desktop

---

## Next Steps

- ⭐ Star the repo: [github.com/yourusername/construction-ai-mcp](https://github.com/yourusername/construction-ai-mcp)
- 📧 Email feedback: support@construction-ai.com
- 🔧 Request features: GitHub Issues

Coming soon:
- Painting estimates
- Concrete estimates
- MEP estimates (electrical, plumbing, HVAC)
- Bluebeam integration
- Procore integration
