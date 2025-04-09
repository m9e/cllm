#!/usr/bin/env python3
"""Framework analysis tools."""
import logging
from pathlib import Path
from rdflib import Graph, Namespace


def analyze_framework_usage(ttl_path):
    """Analyze framework usage in an ontology file."""
    logging.info("Analyzing framework usage in %s", ttl_path)
    
    # Load the graph
    g = Graph()
    g.parse(ttl_path, format="turtle")
    
    # Get all prefixes
    prefixes = dict(g.namespaces())
    logging.info("Found prefixes: %s", prefixes)
    
    # Track framework usage
    framework_counts = {}
    used_frameworks = set()
    
    # Check each triple for framework usage
    for s, p, o in g:
        logging.info("Checking triple: %s %s %s", s, p, o)
        
        # Check if subject, predicate or object uses a framework prefix
        for prefix, uri in prefixes.items():
            if str(uri).startswith("file:") and str(uri).endswith("#"):
                framework = prefix
                if (str(s).startswith(str(uri)) or 
                    str(p).startswith(str(uri)) or 
                    str(o).startswith(str(uri))):
                    used_frameworks.add(framework)
                    framework_counts[framework] = framework_counts.get(framework, 0) + 1
                    logging.info("%s -> %d usages", framework, framework_counts[framework])
    
    # Log framework usage summary
    if not used_frameworks:
        logging.info("No framework usage found")
    else:
        logging.info("%d frameworks used", len(used_frameworks))
        for framework, count in framework_counts.items():
            logging.info("%s -> %d usages", framework, count)
    
    # Check for unused framework prefixes
    unused_prefixes = {prefix for prefix, uri in prefixes.items() 
                      if str(uri).startswith("file:") and str(uri).endswith("#") 
                      and prefix not in used_frameworks}
    
    # Log unused prefixes
    for prefix in unused_prefixes:
        logging.info("Unused prefix: %s", prefix)
    
    return used_frameworks

if __name__ == '__main__':
    analyze_framework_usage(Path('cllm.ttl')) 