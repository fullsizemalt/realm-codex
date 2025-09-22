#!/usr/bin/env python3
import sys, os, re, yaml

def load_realm(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def build_context(cfg):
    envs = cfg.get('environments', {})
    spirits = cfg.get('spirits', {})
    services = cfg.get('services', {})
    ctx = {
        "REALM_SLUG": cfg.get('realm_slug', 'realm'),
        "ENV_DEV": envs.get('dev', 'dev'),
        "ENV_STG": envs.get('stg', 'stg'),
        "ENV_PROD": envs.get('prod', 'prod'),
        "REGION": cfg.get('region', 'usw'),
        "ORACLE_NAME": services.get('oracle', {}).get('name', 'oracle'),
        "SANCTUM_NAME": services.get('sanctum', {}).get('name', 'sanctum'),
        "SCRIPTORIUM_NAME": services.get('scriptorium', {}).get('name', 'scriptorium'),
        "FORGE_NAME": services.get('forge', {}).get('name', 'forge'),
        "MENAGERIE_NAME": services.get('menagerie', {}).get('name', 'menagerie'),
        "CONCLAVE_NAME": services.get('conclave', {}).get('name', 'conclave'),
        "ARCANUM_NAME": services.get('arcanum', {}).get('name', 'arcanum'),
        "SPIRIT_CLAUDE_TITLE": spirits.get('claude', {}).get('title', 'Claude'),
        "SPIRIT_CODEX_TITLE": spirits.get('codex', {}).get('title', 'CodeX'),
        "SPIRIT_GEMINI_TITLE": spirits.get('gemini', {}).get('title', 'Gemini'),
        "SPIRIT_LOCAL_TITLE": spirits.get('local', {}).get('title', 'Local Spirits'),
        "SPIRIT_CLAUDE_SUMMON": spirits.get('claude', {}).get('summoning', 'spirit-claude'),
        "SPIRIT_CODEX_SUMMON": spirits.get('codex', {}).get('summoning', 'spirit-codex'),
        "SPIRIT_GEMINI_SUMMON": spirits.get('gemini', {}).get('summoning', 'spirit-gemini'),
        "SPIRIT_LOCAL_SUMMON": spirits.get('local', {}).get('summoning', 'spirit-local'),
    }
    return ctx

def render_file(path, ctx):
    text = open(path, 'r', encoding='utf-8').read()
    def repl(m):
        key = m.group(1)
        if '|' in key:
            k, default = key.split('|', 1)
            return str(ctx.get(k.strip(), default.strip()))
        return str(ctx.get(key.strip(), m.group(0)))
    new = re.sub(r"\{\{([^}]+)\}\}", repl, text)
    if new != text:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new)

def render_tree(root, ctx):
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.endswith(('.md', '.yml', '.yaml', '.tmpl.sh')) or fn == 'mkdocs.yml':
                render_file(os.path.join(dirpath, fn), ctx)

def render_aliases(root, ctx):
    src = os.path.join(root, 'mystic_aliases.tmpl.sh')
    dst = os.path.join(root, 'mystic_aliases.sh')
    text = open(src, 'r', encoding='utf-8').read()
    for k, v in ctx.items():
        text = text.replace('{{'+k+'}}', str(v))
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(text)

def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(repo_root)  # up from scripts/
    cfg = load_realm(os.path.join(repo_root, 'realm.yml'))
    ctx = build_context(cfg)
    render_tree(repo_root, ctx)
    render_aliases(repo_root, ctx)
    print("✔ Applied realm.yml across docs and aliases.")

if __name__ == '__main__':
    try:
        import yaml  # noqa
    except ImportError:
        print("Missing pyyaml. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    main()
