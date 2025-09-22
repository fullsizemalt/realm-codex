#!/usr/bin/env python3
"""
Phase 6: Service Audit
Identify running services and containers for decommissioning assessment
"""

import subprocess
import json
import sys
from datetime import datetime
from typing import Dict, List

def audit_docker_services():
    """Audit Docker containers and images"""
    print("🐳 Auditing Docker services...")

    docker_audit = {
        'running_containers': [],
        'stopped_containers': [],
        'images': [],
        'volumes': [],
        'networks': []
    }

    try:
        # Running containers
        result = subprocess.run(['docker', 'ps', '--format', 'json'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    container = json.loads(line)
                    docker_audit['running_containers'].append({
                        'name': container.get('Names', ''),
                        'image': container.get('Image', ''),
                        'status': container.get('Status', ''),
                        'ports': container.get('Ports', ''),
                        'created': container.get('CreatedAt', '')
                    })

        # All containers (including stopped)
        result = subprocess.run(['docker', 'ps', '-a', '--format', 'json'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    container = json.loads(line)
                    if 'Exited' in container.get('Status', ''):
                        docker_audit['stopped_containers'].append({
                            'name': container.get('Names', ''),
                            'image': container.get('Image', ''),
                            'status': container.get('Status', ''),
                            'created': container.get('CreatedAt', '')
                        })

        # Images
        result = subprocess.run(['docker', 'images', '--format', 'json'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    image = json.loads(line)
                    docker_audit['images'].append({
                        'repository': image.get('Repository', ''),
                        'tag': image.get('Tag', ''),
                        'size': image.get('Size', ''),
                        'created': image.get('CreatedAt', '')
                    })

        # Volumes
        result = subprocess.run(['docker', 'volume', 'ls', '--format', 'json'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    volume = json.loads(line)
                    docker_audit['volumes'].append(volume)

    except subprocess.CalledProcessError:
        docker_audit['status'] = 'docker_not_available'
    except Exception as e:
        docker_audit['error'] = str(e)

    return docker_audit

def audit_system_processes():
    """Audit system processes"""
    print("⚙️ Auditing system processes...")

    processes = []

    try:
        # Get processes with network connections
        result = subprocess.run(['lsof', '-i', '-P', '-n'],
                              capture_output=True, text=True)

        if result.returncode == 0:
            lines = result.stdout.split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 9:
                        processes.append({
                            'command': parts[0],
                            'pid': parts[1],
                            'user': parts[2],
                            'connection': parts[8] if len(parts) > 8 else '',
                            'type': 'network_service'
                        })

    except Exception as e:
        print(f"⚠️ Error auditing processes: {e}")

    return processes

def audit_brew_services():
    """Audit Homebrew services"""
    print("🍺 Auditing Homebrew services...")

    brew_services = []

    try:
        result = subprocess.run(['brew', 'services', 'list'],
                              capture_output=True, text=True)

        if result.returncode == 0:
            lines = result.stdout.split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        brew_services.append({
                            'name': parts[0],
                            'status': parts[1],
                            'user': parts[2] if len(parts) > 2 else '',
                            'plist': parts[3] if len(parts) > 3 else ''
                        })

    except Exception as e:
        print(f"⚠️ Error auditing brew services: {e}")

    return brew_services

def generate_decommission_plan(audit_results):
    """Generate decommissioning recommendations"""
    plan = {
        'immediate_actions': [],
        'review_candidates': [],
        'keep_services': []
    }

    # Docker analysis
    docker_data = audit_results.get('docker', {})

    # Stopped containers - immediate removal candidates
    if docker_data.get('stopped_containers'):
        plan['immediate_actions'].append({
            'action': 'Remove stopped containers',
            'command': 'docker container prune -f',
            'items': len(docker_data['stopped_containers']),
            'reason': 'Stopped containers consume disk space'
        })

    # Our production services to keep
    production_services = [
        'prometheus', 'grafana', 'loki', 'promtail', 'alertmanager'
    ]

    running_containers = docker_data.get('running_containers', [])
    for container in running_containers:
        container_name = container.get('name', '').lower()

        if any(prod_service in container_name for prod_service in production_services):
            plan['keep_services'].append({
                'name': container['name'],
                'reason': 'Part of observability stack',
                'image': container['image']
            })
        else:
            plan['review_candidates'].append({
                'name': container['name'],
                'image': container['image'],
                'status': container['status'],
                'reason': 'Review if still needed'
            })

    # Brew services analysis
    brew_services = audit_results.get('brew_services', [])
    for service in brew_services:
        if service['status'] == 'started':
            plan['review_candidates'].append({
                'name': service['name'],
                'type': 'brew_service',
                'reason': 'Running brew service - review necessity'
            })

    return plan

def main():
    print("🔍 Starting Phase 6 service audit...")

    audit_results = {
        'timestamp': datetime.now().isoformat(),
        'docker': audit_docker_services(),
        'processes': audit_system_processes(),
        'brew_services': audit_brew_services()
    }

    # Generate decommission plan
    decommission_plan = generate_decommission_plan(audit_results)

    # Summary
    print(f"\n📊 Service Audit Summary:")
    print(f"  Docker containers running: {len(audit_results['docker'].get('running_containers', []))}")
    print(f"  Docker containers stopped: {len(audit_results['docker'].get('stopped_containers', []))}")
    print(f"  Brew services: {len(audit_results['brew_services'])}")
    print(f"  Network processes: {len(audit_results['processes'])}")

    print(f"\n🎯 Decommission Plan:")
    print(f"  Immediate actions: {len(decommission_plan['immediate_actions'])}")
    print(f"  Review candidates: {len(decommission_plan['review_candidates'])}")
    print(f"  Keep services: {len(decommission_plan['keep_services'])}")

    if decommission_plan['immediate_actions']:
        print(f"\n⚡ Immediate Actions:")
        for action in decommission_plan['immediate_actions']:
            print(f"  • {action['action']}: {action['command']}")

    if decommission_plan['review_candidates']:
        print(f"\n🔍 Review Candidates:")
        for candidate in decommission_plan['review_candidates'][:5]:
            print(f"  • {candidate['name']} - {candidate['reason']}")

    # Save full report
    report_file = f"reports/service_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'audit_results': audit_results,
            'decommission_plan': decommission_plan
        }, f, indent=2)

    print(f"\n📋 Full report saved: {report_file}")

if __name__ == "__main__":
    main()