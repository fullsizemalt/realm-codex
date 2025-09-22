# 🚨 The Healer's Compendium

*When Digital Ailments Strike: A Guide to System Restoration*

---

## 🩺 Diagnosing System Afflictions

*"The first rule of system healing: observe before you act. Listen to what the realm is telling you."*

### 🔍 **The Sacred Diagnostic Sequence**

1. **Check the Watchers** - `make observability-status`
2. **Consult the Oracles** - `make service-audit`
3. **Read the Ancient Logs** - `docker logs <service_name>`
4. **Examine Resource Consumption** - `make quota-check`

---

## 🔥 Common Ailments and Their Remedies

### 📊 **The Grafana Darkness** (Dashboard Won't Load)

**Symptoms**: Grafana accessible but dashboards show "No data" or fail to render

**Diagnosis Ritual**:
```bash
make observability-status
docker logs grafana
```

**Healing Incantations**:
```bash
# Restart the visualization spirit
docker-compose restart grafana

# If Prometheus is the issue
docker-compose restart prometheus

# Nuclear option - restart entire observability stack
make observability-stop
make observability-start
```

**Prevention Charm**: Monitor disk space—Grafana spirits become weak when storage is low.

---

### 🤖 **Silent AI Spirits** (Agents Not Responding)

**Symptoms**: AI agents fail quality gates or don't respond to commands

**Diagnosis Ritual**:
```bash
make agents-list
make agents-quality
python3 scripts/agent_registry.py validate-all
```

**Healing Incantations**:
```bash
# Refresh the spirit registry
make agents-update-registry

# Check individual spirit health
make agents-quality-single AGENT=spirit-claude-sonnet

# Reset all spirits to known good state
python3 scripts/agent_registry.py reset
```

**Warning Signs**: Watch for SLO violations in the metrics—early indicators of spirit distress.

---

### 🐳 **Container Possession** (Docker Issues)

**Symptoms**: Services fail to start, containers restart constantly, or resource exhaustion

**Diagnosis Ritual**:
```bash
docker ps -a
docker system df
make docker-cleanup
```

**Healing Incantations**:
```bash
# Exorcise dead containers
docker container prune -f

# Banish unused images
docker image prune -f

# Complete purification ritual
make docker-cleanup

# If containers are possessed by port conflicts
docker-compose down
docker-compose up -d
```

**Ancient Wisdom**: *"When in doubt, restart the container. When still in doubt, restart Docker itself."*

---

### 💾 **Storage Curse** (Disk Space Issues)

**Symptoms**: Services crash, logs mention "no space left on device", system becomes sluggish

**Diagnosis Ritual**:
```bash
make quota-check
make find-duplicates
df -h
```

**Healing Incantations**:
```bash
# Quick cleanup ceremony
make quick-cleanup

# Deep purification
make legacy-scan
make cleanup-dead

# Manual space liberation
docker system prune -a --volumes
```

**Protective Ward**: Set up automated cleanup: `make setup-automation`

---

### 🌐 **Network Maze** (Connectivity Issues)

**Symptoms**: Services can't communicate, external APIs unreachable, DNS resolution fails

**Diagnosis Ritual**:
```bash
docker network ls
docker-compose logs
ping google.com
nslookup localhost
```

**Healing Incantations**:
```bash
# Reset the network bridges
docker-compose down
docker network prune -f
docker-compose up -d

# If DNS is cursed
sudo systemctl restart systemd-resolved  # Linux
sudo dscacheutil -flushcache             # macOS
```

---

### 📜 **Lost Configuration Scrolls** (Config Issues)

**Symptoms**: Services start but behave incorrectly, missing environment variables, invalid YAML

**Diagnosis Ritual**:
```bash
docker-compose config
make agents-validate
python3 -c "import yaml; yaml.safe_load(open('config/file.yaml'))"
```

**Healing Incantations**:
```bash
# Validate all configurations
make agents-validate
python3 scripts/validate_configs.py

# Restore from version control
git checkout HEAD -- config/
git status
```

---

## 🧙‍♂️ Advanced Healing Techniques

### **The Complete System Revival**
*When multiple ailments afflict the realm simultaneously*

```bash
# Step 1: Stop everything
make observability-stop
docker-compose down

# Step 2: Purify the environment
make docker-cleanup
make quick-cleanup

# Step 3: Restore from known good state
git status
git stash  # if needed

# Step 4: Resurrect the realm
make observability-start
make agents-update-registry

# Step 5: Verify healing
make observability-status
make agents-quality
```

### **The Time Travel Remedy**
*When recent changes have cursed the system*

```bash
# View recent changes
git log --oneline -10

# Return to last known good state
git revert <commit_hash>

# Or travel back in time completely
git reset --hard <good_commit_hash>
git push --force-with-lease origin master
```

---

## 🔮 Prophetic Warnings

### **Early Warning Signs**

Monitor these portents to prevent future ailments:

- **Memory Creep**: `docker stats` showing increasing memory usage
- **Log Flood**: Excessive logging indicating underlying issues
- **Response Lag**: API responses taking longer than usual
- **Error Bursts**: Sudden spikes in error rates
- **Certificate Expiry**: SSL/TLS certificates approaching expiration

### **Preventive Medicine**

```bash
# Daily health check
make service-audit

# Weekly deep scan
make legacy-scan

# Monthly purification
make cleanup-dead

# Quarterly system renewal
make codex-update
```

---

## 📞 **Emergency Protocols**

### **When All Else Fails**

1. **Document the Symptoms**: Take screenshots, copy error messages
2. **Preserve the Evidence**: `docker logs` output before restarting
3. **Create a Restoration Point**: `git commit -am "Before emergency fix"`
4. **Apply Nuclear Option**: Complete system rebuild
5. **Learn from the Experience**: Update this compendium

### **The Nuclear Option**
```bash
# Complete realm reconstruction
git clone <backup_repo> ~/realm-backup
cd ~/realm-backup
make observability-start
make agents-update-registry
make codex-update
```

---

*"Every system ailment is a teacher. Every successful healing adds to our wisdom. The strongest realms are those that have survived the most trials."*

*— The Grand Healer*

---

**Remember**: When in doubt, consult the logs. When the logs are unclear, consult the metrics. When the metrics lie, restart everything and check your assumptions.