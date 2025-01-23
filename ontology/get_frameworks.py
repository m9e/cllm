#!/usr/bin/env python3
from pathlib import Path


def get_framework_prefixes(ttl_file):
    """Extract framework ontology prefixes from TTL file."""
    # Read the TTL file as text first to get prefix declarations
    with open(ttl_file) as f:
        content = f.read()
    
    # Look for prefix declarations
    framework_prefixes = []
    for line in content.split('\n'):
        if line.startswith('@prefix'):
            # Parse prefix declaration
            parts = line.split()
            if len(parts) >= 3:
                prefix = parts[1].rstrip(':')
                path = parts[2].rstrip(' .')
                # Only include framework ontologies
                if prefix in [
                    'meta', 'metameta', 'problem', 'solution',
                    'conversation', 'process', 'agent', 'time', 'install'
                ]:
                    framework_prefixes.append((prefix, path))
    
    return framework_prefixes


if __name__ == '__main__':
    ttl_file = Path('cllm.ttl')
    frameworks = get_framework_prefixes(ttl_file)
    print("\nFramework Ontology Dependencies:")
    print("--------------------------------")
    for prefix, path in sorted(frameworks):
        print(f"{prefix:10} -> {path}") 