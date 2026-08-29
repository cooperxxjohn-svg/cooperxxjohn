# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Painting estimation tool
- Concrete estimation tool
- MEP estimation tools (electrical, plumbing, HVAC)
- Regional pricing adjustments
- Material cost database updates
- Integration with Bluebeam
- Integration with Procore

---

## [0.1.0] - 2026-05-21

### Added
- Initial release of Construction AI MCP server
- Drywall estimation tool with comprehensive calculations
- Support for walls and ceilings with openings (doors, windows)
- ASTM C840 finish levels (0-5)
- Project type adjustments (residential, commercial, industrial, medical, institutional)
- Material quantity calculations:
  - Drywall sheets (4'×8') with 15% waste factor
  - Joint compound (varies by finish level)
  - Paper tape (linear feet)
  - Screws (quantity)
- Labor breakdown by phase:
  - Hanging hours
  - Taping hours
  - Finishing hours
- Cost calculations:
  - Materials cost
  - Labor cost (varies by project type)
  - Overhead (25%)
  - Profit (25%)
  - Cost per square foot
- Professional markdown output formatting
- MCP protocol compliance (stdio transport)
- TypeScript implementation with full type safety
- Automated test suite
- Comprehensive documentation:
  - README with installation and usage
  - CLAUDE_DESKTOP_SETUP guide
  - Example prompts
  - Contributing guidelines
  - Demo video script

### Technical Details
- Built with `@modelcontextprotocol/sdk` v1.29.0
- TypeScript 6.0.3 with ES2022 target
- Node.js 18+ required
- Cross-platform support (Mac, Linux, Windows)

### Industry Standards
- ASTM C840 compliance for finish levels
- RS Means 2026 labor rates
- GA-214 Gypsum Association standards
- Standard waste factors and overhead calculations

---

## Version History

### Version Numbering
- **Major (X.0.0):** Breaking changes, major new features
- **Minor (0.X.0):** New features, backward compatible
- **Patch (0.0.X):** Bug fixes, minor improvements

### Planned Releases

#### v0.2.0 (Planned: June 2026)
- Painting estimation tool
- Material database expansion
- Regional pricing adjustments

#### v0.3.0 (Planned: July 2026)
- Concrete estimation tool
- Improved accuracy algorithms
- User preference settings

#### v0.4.0 (Planned: August 2026)
- MEP estimation tools (electrical)
- Multi-trade project support
- Export to Excel/PDF

#### v1.0.0 (Planned: September 2026)
- Stable API
- All major construction trades
- Bluebeam integration
- Procore integration
- Official Anthropic partnership

---

## Upgrade Guide

### From Pre-release to 0.1.0
First official release - no upgrade needed.

### Future Breaking Changes
Will be clearly documented here with migration guides.

---

## Support

- **Issues:** https://github.com/cooperxxjohn/construction-ai-mcp/issues
- **Email:** cooperxxjohn@gmail.com
- **Discussions:** GitHub Discussions (coming soon)

---

[Unreleased]: https://github.com/cooperxxjohn/construction-ai-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/cooperxxjohn/construction-ai-mcp/releases/tag/v0.1.0
