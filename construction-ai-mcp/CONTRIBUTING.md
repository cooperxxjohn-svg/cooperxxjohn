# Contributing to Construction AI MCP

Thanks for your interest in contributing! This guide will help you get started.

---

## Quick Start

1. **Fork the repository**
   ```bash
   git clone https://github.com/cooperxxjohn/construction-ai-mcp.git
   cd construction-ai-mcp
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Build the project**
   ```bash
   npm run build
   ```

4. **Run tests**
   ```bash
   npm test
   ```

5. **Test with Claude Desktop**
   - Build the project
   - Configure Claude Desktop to use local version
   - Test with example prompts

---

## Project Structure

```
construction-ai-mcp/
├── src/
│   ├── index.ts          # Main MCP server
│   └── tools/
│       ├── drywall.ts    # Drywall estimation tool
│       ├── painting.ts   # (Coming soon)
│       └── concrete.ts   # (Coming soon)
├── dist/                 # Compiled output
├── test-mcp-server.js    # Integration tests
├── package.json
├── tsconfig.json
└── README.md
```

---

## Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Follow existing code style
- Add TypeScript types for everything
- Keep functions focused and small
- Add comments for complex calculations

### 3. Test Your Changes
```bash
# Run type checking
npm run build

# Run integration tests
npm test

# Test with Claude Desktop manually
```

### 4. Commit
```bash
git add .
git commit -m "feat: Add painting estimation tool"
```

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## Adding a New Tool

Want to add a new estimation tool (painting, concrete, etc.)? Here's how:

### Step 1: Create Tool File

Create `src/tools/yourTool.ts`:

```typescript
interface YourToolArgs {
  // Define your input parameters
  area?: number;
  // ... more parameters
}

export const yourToolDefinition = {
  name: "your_tool_name",
  description: `Clear description of what this tool does...`,
  inputSchema: {
    type: "object",
    properties: {
      // Define JSON schema for inputs
    },
    required: ["requiredField1"]
  }
};

export async function handleYourTool(args: any) {
  // Implement your calculation logic
  const result = calculateYourEstimate(args);
  
  return {
    content: [{
      type: "text",
      text: formatYourResponse(result)
    }]
  };
}

async function calculateYourEstimate(args: YourToolArgs) {
  // Your calculation logic here
}

function formatYourResponse(data: any): string {
  // Format output as markdown
}
```

### Step 2: Register Tool

Update `src/index.ts`:

```typescript
import { yourToolDefinition, handleYourTool } from "./tools/yourTool.js";

// Add to tool list
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      drywallEstimateTool,
      yourToolDefinition,  // Add here
    ],
  };
});

// Add to handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  switch (name) {
    case "drywall_estimate":
      return await handleDrywallEstimate(args);
    case "your_tool_name":
      return await handleYourTool(args);  // Add here
    // ...
  }
});
```

### Step 3: Test

Add test case to `test-mcp-server.js`:

```javascript
const yourToolRequest = {
  jsonrpc: '2.0',
  id: 4,
  method: 'tools/call',
  params: {
    name: 'your_tool_name',
    arguments: {
      // Test data
    }
  }
};

server.stdin.write(JSON.stringify(yourToolRequest) + '\n');
```

### Step 4: Document

Update README.md with:
- Tool description
- Input parameters
- Example usage
- Output format

---

## Code Style Guidelines

### TypeScript
- Use interfaces for data structures
- Avoid `any` type when possible
- Use async/await for async operations
- Export types that might be reused

### Naming Conventions
- Functions: `camelCase`
- Interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Files: `kebab-case.ts`

### Comments
```typescript
// Good: Explains WHY
// Using 15% waste factor per industry standard (RS Means)
const waste = 1.15;

// Bad: Explains WHAT (code already shows this)
// Multiply by 1.15
const waste = 1.15;
```

### Error Handling
```typescript
try {
  // Operation
} catch (error: any) {
  return {
    content: [{
      type: "text",
      text: `Error: ${error.message}`
    }],
    isError: true
  };
}
```

---

## Testing Guidelines

### Unit Tests (Coming Soon)
We'll add Jest for unit testing calculation functions.

### Integration Tests
`test-mcp-server.js` validates:
- MCP protocol compliance
- Tool registration
- Tool execution
- Response formatting

Add new test cases when adding tools.

### Manual Testing
Always test with Claude Desktop:
1. Build: `npm run build`
2. Restart Claude Desktop
3. Try various prompts
4. Verify output accuracy

---

## Industry Standards to Follow

### Drywall
- **ASTM C840** - Finish levels 0-5
- **GA-214** - Gypsum Association standards
- **RS Means 2026** - Labor rates and material costs

### Painting (Coming Soon)
- **PDCA P1** - Application standards
- Coverage rates: 350-400 sqft/gallon

### Concrete (Coming Soon)
- **ACI 318** - Building code requirements
- Coverage: 80 lbs/cubic foot

### General
- Local labor rates vary by region
- Material costs should be updated quarterly
- Always include waste factors
- Overhead: 20-30%
- Profit: 15-25%

---

## Documentation

### Code Comments
- Explain complex calculations
- Reference industry standards
- Note assumptions made

### README Updates
- Keep installation steps current
- Add new tools to feature list
- Update examples

### CHANGELOG
- Document all changes
- Follow semantic versioning
- Note breaking changes

---

## Pull Request Process

1. **Fill out PR template**
   - What does this change?
   - Why is it needed?
   - How was it tested?

2. **Checklist**
   - [ ] Tests pass
   - [ ] Code follows style guide
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)
   - [ ] Tested with Claude Desktop

3. **Review Process**
   - Maintainer will review within 2-3 days
   - Address feedback
   - Once approved, will be merged

4. **After Merge**
   - Change will be in next release
   - Version bump per semver
   - Published to npm

---

## Reporting Issues

### Bug Reports
Include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages
- Your environment (OS, Node version, Claude version)

### Feature Requests
Describe:
- What trade/feature?
- What problem does it solve?
- Example use case
- Willingness to contribute?

---

## Code of Conduct

### Be Respectful
- Professional communication
- Constructive feedback
- Help newcomers

### Be Collaborative
- Share knowledge
- Review others' PRs
- Respond to issues/questions

### Be Inclusive
- Welcome all skill levels
- Document for beginners
- Patient with questions

---

## Recognition

Contributors will be:
- Listed in README
- Credited in release notes
- Thanked in announcements

Significant contributors may be invited as maintainers.

---

## Questions?

- **Email:** cooperxxjohn@gmail.com
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions (coming soon)

---

Thank you for contributing to Construction AI! 🏗️
