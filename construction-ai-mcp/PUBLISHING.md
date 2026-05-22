# Publishing Guide

Step-by-step guide to publish Construction AI MCP to npm and launch publicly.

---

## Pre-Publishing Checklist

### Code Quality
- [ ] All tests passing (`npm test`)
- [ ] TypeScript compiles without errors (`npm run build`)
- [ ] No console.log statements (use console.error for stderr)
- [ ] Code follows style guide
- [ ] No secrets or API keys in code

### Documentation
- [ ] README.md is complete and accurate
- [ ] CLAUDE_DESKTOP_SETUP.md has clear instructions
- [ ] CHANGELOG.md updated with version changes
- [ ] Example prompts tested and working
- [ ] CONTRIBUTING.md is up to date

### Package Configuration
- [ ] package.json version is correct
- [ ] package.json repository URL is correct
- [ ] package.json author email is correct
- [ ] LICENSE file exists
- [ ] .gitignore excludes node_modules and dist
- [ ] Files field in package.json lists only necessary files

### Testing
- [ ] Tested on Mac (if available)
- [ ] Tested on Linux
- [ ] Tested on Windows (if available)
- [ ] Tested with Claude Desktop
- [ ] Tested with Node 18, 20, 22
- [ ] Integration test passes

---

## Step 1: Prepare npm Account

### Create npm Account
```bash
# Create account at npmjs.com
# Then login via CLI
npm login
```

### Enable 2FA (Recommended)
```bash
npm profile enable-2fa auth-and-writes
```

### Create Access Token
1. Go to https://www.npmjs.com/settings/tokens
2. Click "Generate New Token"
3. Select "Automation" type
4. Copy token and save securely

---

## Step 2: Test Package Locally

### Build and Test
```bash
# Clean build
rm -rf dist node_modules
npm install
npm run build
npm test
```

### Test Installation Locally
```bash
# Pack the package (creates tarball)
npm pack

# This creates: construction-ai-mcp-0.1.0.tgz

# Test install globally from tarball
npm install -g construction-ai-mcp-0.1.0.tgz

# Test running
construction-ai-mcp
# Should see: "Construction AI MCP server running on stdio"

# Uninstall
npm uninstall -g construction-ai-mcp

# Clean up
rm construction-ai-mcp-0.1.0.tgz
```

### Test with Claude Desktop
1. Build package: `npm run build`
2. Configure Claude Desktop to use local version:
```json
{
  "mcpServers": {
    "construction": {
      "command": "node",
      "args": ["/full/path/to/construction-ai-mcp/dist/index.js"]
    }
  }
}
```
3. Restart Claude Desktop
4. Test with multiple prompts from examples/example-prompts.md
5. Verify all estimates are accurate

---

## Step 3: Version Management

### Update Version
```bash
# Patch version (0.1.0 -> 0.1.1)
npm version patch

# Minor version (0.1.0 -> 0.2.0)
npm version minor

# Major version (0.1.0 -> 1.0.0)
npm version major
```

This will:
- Update package.json version
- Create git commit
- Create git tag

### Update CHANGELOG.md
Edit CHANGELOG.md to document changes:
```markdown
## [0.1.0] - 2026-05-21

### Added
- Initial release
- Drywall estimation tool
...
```

### Commit Changes
```bash
git add CHANGELOG.md
git commit --amend --no-edit
git push origin main --tags
```

---

## Step 4: Publish to npm

### Dry Run (Test without Publishing)
```bash
npm publish --dry-run
```

This shows:
- What files will be included
- Package size
- Package name and version
- Any warnings or errors

Review output carefully!

### Publish for Real
```bash
npm publish --access public
```

Expected output:
```
+ construction-ai-mcp@0.1.0
```

### Verify Publication
1. Check npm: https://www.npmjs.com/package/construction-ai-mcp
2. Test installation:
```bash
npm install -g construction-ai-mcp
construction-ai-mcp --help
```

---

## Step 5: Create GitHub Release

### Tag the Release
```bash
git tag -a v0.1.0 -m "v0.1.0 - Initial release"
git push origin v0.1.0
```

### Create Release on GitHub
1. Go to: https://github.com/cooperxxjohn/construction-ai-mcp/releases
2. Click "Draft a new release"
3. Select tag: v0.1.0
4. Release title: "v0.1.0 - Initial Release"
5. Description: Copy from CHANGELOG.md
6. Click "Publish release"

### Automate with GitHub CLI
```bash
gh release create v0.1.0 \
  --title "v0.1.0 - Initial Release" \
  --notes-file RELEASE_NOTES.md
```

---

## Step 6: Launch Announcement

### Update README Badges
Add to top of README.md:
```markdown
![npm version](https://img.shields.io/npm/v/construction-ai-mcp)
![npm downloads](https://img.shields.io/npm/dm/construction-ai-mcp)
![GitHub stars](https://img.shields.io/github/stars/cooperxxjohn/construction-ai-mcp)
![License](https://img.shields.io/npm/l/construction-ai-mcp)
```

### Social Media Posts

#### LinkedIn
```
🚀 Launching Construction AI for Claude Desktop!

Contractors: Stop spending 4 hours on takeoff estimates.

Now you can estimate drywall projects in 40 seconds using AI.

✅ Professional breakdowns (materials, labor, costs)
✅ Industry-validated formulas (ASTM C840, RS Means)
✅ Works with Claude Desktop
✅ Free to try

Install: npm install -g construction-ai-mcp

Example: "Estimate drywall for a 20x15 office with 9ft ceilings, 
one door, two windows, Level 4 finish"

Claude returns exact quantities, labor hours, and total cost.

Coming soon: Painting, concrete, MEP trades

⭐ Star us: github.com/cooperxxjohn/construction-ai-mcp

#Construction #AI #Contractors #Estimating
```

#### Twitter/X
```
🚀 Just launched Construction AI for @AnthropicAI Claude!

Turn Claude into a construction estimator:
→ 40-second drywall takeoffs
→ Professional breakdowns
→ Industry-accurate pricing

Install: npm install -g construction-ai-mcp

Free to try. More trades coming soon.

github.com/cooperxxjohn/construction-ai-mcp
```

#### Reddit (r/Construction)
Title: "I built an AI tool for instant drywall estimates (free, open source)"

```
Hey contractors,

I built a free tool that gives Claude Desktop construction knowledge.

**What it does:**
Estimate drywall projects in plain English:

"Estimate drywall for a 20x15 room, 9ft ceilings, one door, two windows, Level 4"

Returns:
- Material quantities (sheets, compound, tape, screws)
- Labor hours (hanging, taping, finishing)
- Complete cost breakdown

**Why I built it:**
Spent too many hours on takeoffs. Wanted AI that actually knows construction standards (ASTM C840, RS Means).

**How to use:**
1. npm install -g construction-ai-mcp
2. Configure Claude Desktop (2-line config)
3. Ask Claude to estimate

**Open source:** github.com/cooperxxjohn/construction-ai-mcp

**Coming soon:** Painting, concrete, MEP

Would love feedback from real contractors!
```

### Product Hunt Launch
1. Create Product Hunt account
2. Schedule launch for Tuesday or Wednesday (best days)
3. Prepare:
   - Logo/icon
   - Screenshots
   - Demo video (2-3 min)
   - First comment with details
4. Title: "Construction AI - Give Claude professional estimating skills"
5. Tagline: "AI-powered takeoffs for contractors in 40 seconds"

---

## Step 7: Community Engagement

### GitHub
- [ ] Enable GitHub Discussions
- [ ] Add issue templates
- [ ] Add PR template
- [ ] Set up GitHub Projects for roadmap
- [ ] Pin important issues

### Documentation Site (Optional)
Consider creating docs site with:
- Installation guide
- API reference
- Example gallery
- Video tutorials
- FAQ

Tools: Docusaurus, GitBook, or MkDocs

### Email List (Optional)
Set up newsletter for:
- New releases
- New trades added
- Tips & tricks
- User spotlights

Tools: Mailchimp, ConvertKit, Buttondown

---

## Step 8: Metrics & Tracking

### npm Stats
Monitor at: https://npm-stat.com/charts.html?package=construction-ai-mcp

Track:
- Daily downloads
- Total downloads
- Version adoption

### GitHub Stats
Track:
- Stars
- Forks
- Issues opened/closed
- PR submissions
- Contributors

### Usage Analytics (Optional)
Consider anonymous telemetry:
- Tool calls (which tools used most)
- Error rates
- Average estimation times

Always make telemetry opt-in and privacy-focused.

---

## Step 9: Maintenance Plan

### Weekly
- [ ] Respond to issues
- [ ] Review PRs
- [ ] Check npm download stats
- [ ] Monitor for errors

### Monthly
- [ ] Update material pricing
- [ ] Review labor rates
- [ ] Check for dependency updates
- [ ] Update documentation

### Quarterly
- [ ] Add new trade (painting, concrete, etc.)
- [ ] Major feature release
- [ ] Blog post or case study
- [ ] User survey for feedback

---

## Step 10: Growth Strategy

### Week 1 Post-Launch
- [ ] 50 npm installs
- [ ] 25 GitHub stars
- [ ] 10 active users
- [ ] 5 feedback conversations

### Month 1
- [ ] 200 npm installs
- [ ] 100 GitHub stars
- [ ] 50 active users
- [ ] 10 testimonials

### Month 3
- [ ] 1,000 npm installs
- [ ] 500 GitHub stars
- [ ] 200 active users
- [ ] $10K MRR (paid features)
- [ ] Apply for Anthropic partnership

---

## Troubleshooting

### Publish Fails with 401
```bash
npm login
npm publish --access public
```

### Package Name Already Taken
Change name in package.json:
- construction-ai-mcp
- @username/construction-ai-mcp
- construction-mcp-ai

### Version Already Published
```bash
npm version patch
npm publish --access public
```

### Large Package Size
Check what's included:
```bash
npm pack --dry-run
```

Add to .npmignore:
```
test/
examples/
docs/
*.test.ts
.github/
```

---

## Post-Launch Todo

### Documentation
- [ ] Add video demo to README
- [ ] Create quick start guide
- [ ] Write blog post about launch
- [ ] Create tutorial series

### Features
- [ ] Add painting tool (v0.2.0)
- [ ] Add concrete tool (v0.3.0)
- [ ] Regional pricing
- [ ] Export to Excel/PDF

### Community
- [ ] Respond to all feedback
- [ ] Create Discord/Slack community
- [ ] Host webinar
- [ ] Partner with construction YouTubers

### Business
- [ ] Add pricing tiers
- [ ] Stripe integration
- [ ] Usage limits
- [ ] Premium features

---

## Version Roadmap

### v0.1.0 ✅ (May 2026)
- Drywall estimation tool
- Basic MCP server
- Claude Desktop integration

### v0.2.0 (June 2026)
- Painting estimation tool
- Material database expansion
- Regional pricing

### v0.3.0 (July 2026)
- Concrete estimation tool
- Multi-trade support
- Export features

### v0.4.0 (August 2026)
- MEP tools (electrical, plumbing)
- Bluebeam integration
- API access

### v1.0.0 (September 2026)
- Stable API
- Official Anthropic partnership
- Production-ready for enterprise

---

## Success Criteria

### Technical
- ✅ Published to npm
- ✅ Working with Claude Desktop
- ✅ 95%+ accuracy on estimates
- ✅ <2s response time

### Adoption
- [ ] 1,000+ npm downloads
- [ ] 100+ GitHub stars
- [ ] 50+ active users
- [ ] 10+ testimonials

### Revenue (Optional)
- [ ] 50 paid users at $149/mo
- [ ] $7,450 MRR
- [ ] <10% churn rate

### Partnership
- [ ] Anthropic MCP marketplace listing
- [ ] Official Anthropic partner
- [ ] Featured in Anthropic newsletter

---

Ready to launch! 🚀
