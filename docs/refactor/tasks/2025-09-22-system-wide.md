# Phase 2 GitOps and Config Hygiene

**Service/Subsystem:** system-wide
**Date:** 2025-09-22

## DoD (Phase 2 - GitOps & Config Hygiene)
- [ ] Secrets externalized to Vaultwarden
- [ ] API keys removed from Docker environment
- [ ] Git repository for configuration management
- [ ] Pull-based deployment mechanism
- [ ] Environment-specific configs (dev/staging/prod)
- [ ] Config validation in CI pipeline

## Plan
1. Set up Vaultwarden for secrets management
2. Extract API keys from arcanum service to Vault
3. Create Git-based config management structure
4. Implement simple GitOps deployment script
5. Add environment separation (dev/prod configs)
6. Integrate config validation into deployment

## Risk & Rollback
- **Risk**: Service downtime during secret migration
- **Rollback**: Keep current .env approach as backup
- **Mitigation**: Test Vault integration locally first

## Links
- Issue: 
- PR: 
- Dashboard: 
