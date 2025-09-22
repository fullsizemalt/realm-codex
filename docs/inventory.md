# System Inventory - Phase 0

**Date:** 2025-09-22
**Status:** In Progress

## Running Services

### Production Services
| Service | Type | Port | Status | Critical | Config Notes |
|---------|------|------|--------|----------|---------------|
| arcanum-orchestrator | Docker | 8080 | Running | Yes | Uses Gemini+Claude APIs, writes to chronicle.md |
| ~~tinfoil-game-server~~ | ~~Docker~~ | ~~3000~~ | **REMOVED** | ~~No~~ | Moved to VPS |

### Development Services
| Service | Type | Port | Status | Critical | Project |
|---------|------|------|--------|----------|---------|
| ~~WhisperingOrchids~~ | ~~Node/Vite~~ | ~~5179~~ | **REMOVED** | ~~No~~ | Moved to VPS/GitHub Pages |
| ~~iterm2-theme-editor~~ | ~~Node/Vite~~ | ~~5173~~ | **REMOVED** | ~~No~~ | Pruned |

## Configuration Details

### Arcanum Orchestrator (Critical Service)
- **APIs**: Gemini (gemini-1.5-flash), Claude (claude-3-5-sonnet)
- **Data**: Chronicle logging to `../../docs/chronicle.md`
- **Schema**: `schemas/output.default.json`
- **Secrets**: API keys for Google/Anthropic (ENV vars)

### Tinfoil Game Server
- **Auth**: Username: 10, Password: 2GreenSlugs!
- **Data**: Games stored in `./games` directory
- **Risk**: Hardcoded credentials in ENV

## Infrastructure Components

### Directory Structure
- `~/Aetherweave/` - **DEPRECATED** - Contains PAI-* modules
- `~/realm-refactor/` - New refactor workspace

### PAI Modules (Under Aetherweave - TO MIGRATE)
- PAI-Agent-Instructions
- PAI-Archive-Projects
- PAI-Development-Projects
- PAI-Documentation-Public
- PAI-Knowledge-References
- PAI-Obsidian-Management
- PAI-Personal-Content-Legacy
- PAI-Personal-Workspace
- PAI-System-Infrastructure
- PAI-VPS-Deployment

## Dependencies & Data Flows

### External Dependencies
- **Google Gemini API** (arcanum-orchestrator)
- **Anthropic Claude API** (arcanum-orchestrator)
- **Node.js ecosystem** (WhisperingOrchids, iterm2-theme-editor)
- **Docker runtime** (production services)

### Data Flows
1. **Arcanum**: API calls → Processing → Chronicle markdown file
2. **Tinfoil**: Game files → Local storage in `./games`
3. **Dev projects**: Hot reload, no persistent data

### File System Dependencies
- Arcanum chronicle: `../../docs/chronicle.md` (relative path - location unclear)
- Arcanum schema: `schemas/output.default.json`
- Game data: `./games` directory
- Development assets: Local node_modules, build artifacts

## Immediate Security Risks
- ~~**HIGH**: Tinfoil server has hardcoded credentials in ENV~~ **RESOLVED** - Service removed
- **MEDIUM**: API keys stored in ENV vars (not externalized)
- ~~**LOW**: Development servers running on exposed ports~~ **RESOLVED** - Dev services removed

## Next Steps - Phase 1 Prep
1. ✅ Service inventory complete
2. ⏳ Establish monitoring baselines
3. ⏳ Test backup procedures
4. ⏳ Plan Phase 1 guardrails (health checks, alerts)