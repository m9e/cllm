#!/usr/bin/env python3
"""
Setup symlinks for ontology framework dependencies.
This script creates symlinks to the core framework ontologies based on the
dependencies declared in the CLLM ontology.
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Framework ontologies we depend on, mapped to their source files
FRAMEWORK_ONTOLOGIES = {
    'meta.ttl': '../ontology-framework/meta.ttl',
    'metameta.ttl': '../ontology-framework/metameta.ttl',
    'problem.ttl': '../ontology-framework/problem.ttl',
    'solution.ttl': '../ontology-framework/solution.ttl',
    'conversation.ttl': '../ontology-framework/conversation.ttl',
    'process.ttl': '../ontology-framework/process.ttl',
    'agent.ttl': '../ontology-framework/agent.ttl',
    'time.ttl': '../ontology-framework/time.ttl',
    'install.ttl': '../ontology-framework/install.ttl'
}


def verify_framework_path(framework_path: Path) -> bool:
    """Verify framework directory exists and contains required ontologies."""
    if not framework_path.exists():
        logger.error(
            f"Ontology framework directory not found: {framework_path}"
        )
        return False
    
    missing_files = []
    for ontology in FRAMEWORK_ONTOLOGIES.values():
        if not (framework_path / Path(ontology).name).exists():
            missing_files.append(ontology)
    
    if missing_files:
        logger.error("Missing framework ontologies:")
        for file in missing_files:
            logger.error(f"  - {file}")
        return False
    
    return True


def create_symlinks(target_dir: Path, framework_path: Path) -> None:
    """Create symlinks for framework ontologies in the target directory."""
    target_dir.mkdir(exist_ok=True)
    
    for link_name, source_path in FRAMEWORK_ONTOLOGIES.items():
        link_path = target_dir / link_name
        source = framework_path / Path(source_path).name
        
        # Remove existing symlink if it exists
        if link_path.exists():
            if link_path.is_symlink():
                link_path.unlink()
            else:
                logger.warning(
                    f"File exists and is not a symlink: {link_path}"
                )
                continue
        
        # Create relative symlink
        try:
            rel_path = os.path.relpath(source, target_dir)
            link_path.symlink_to(rel_path)
            logger.info(f"Created symlink: {link_path} -> {source}")
        except OSError as e:
            logger.error(f"Failed to create symlink {link_path}: {e}")


def main():
    """Main entry point for the script."""
    # Get the directory containing this script
    script_dir = Path(__file__).resolve().parent
    
    # Determine framework path (relative to script location)
    framework_path = script_dir.parent.parent / 'ontology-framework'
    
    # Verify framework directory exists
    if not verify_framework_path(framework_path):
        logger.error(
            "Please ensure the ontology-framework repository is present"
        )
        sys.exit(1)
    
    # Create symlinks
    create_symlinks(script_dir, framework_path)
    logger.info("Symlink setup complete")


if __name__ == "__main__":
    main() 