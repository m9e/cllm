# Development Dependencies

## Environment Setup

### Option 1: Automated Setup
```bash
# From project root
chmod +x ontology/setup_dev_env.sh
./ontology/setup_dev_env.sh
```
This will:
- Create a conda or venv environment
- Install all dependencies from pyproject.toml
- Install development tools (flake8, rdflib, etc.)

### Option 2: Manual Setup
```bash
# Using conda
conda create -n cllm-dev python=3.10
conda activate cllm-dev
pip install -e ".[dev]"

# Or using venv
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Required Tools

### Python Development
- **rdflib** - RDF library for Python (parsing, querying)
  ```bash
  conda install rdflib
  ```

### Ontology Processing
- **Apache Jena** - RDF/OWL processing and querying framework
  ```bash
  brew install jena  # macOS
  ```
  Primary uses:
  - SPARQL querying and updates
  - RDF/OWL data processing
  - Triple store management
  - Inference engine
  - Command line tools:
    - `riot` - Validates RDF syntax
    - `sparql` - SPARQL query processor
    - `tdbloader/tdbquery` - Triple store management
    - `fuseki-server` - SPARQL endpoint server

## Visualization Tools

### Primary Tool
- **Protégé** - Ontology editor with visualization capabilities
  - Download from [protege.stanford.edu](https://protege.stanford.edu/)
  - Key features:
    - Visual ontology editing
    - Class hierarchy visualization
    - OntoGraf plugin for interactive views
    - Entity relationship visualization

### Supporting Tools
- **GraphViz** - Graph visualization
  ```bash
  brew install graphviz  # macOS
  ```
  - Used for generating static visualizations
  - Can export ontology structure to DOT format
  - Supports various output formats (SVG, PNG, PDF)

### Web-Based Visualization
- **WebVOWL** - Web-based Interactive Visualization
  - [WebVOWL Demo](http://vowl.visualdataweb.org/webvowl/)
  - Supports direct OWL/RDF upload
  - Force-directed layout

- **Graffoo** - Graphical Framework for OWL
  - [Graffoo Specification](https://essepuntato.it/graffoo/)
  - Standardized visual notation
  - Focuses on OWL 2 constructs

## Installation Verification

### Verify Processing Tools
```bash
# Verify rdflib
python -c "import rdflib; print(rdflib.__version__)"

# Verify Jena tools
riot --version
sparql --version
```

### Verify Visualization
```bash
# Verify GraphViz
dot -V
```

## Development Environment Setup
1. Install required tools listed above
2. Clone the ontology framework repository:
   ```bash
   cd ..
   git clone https://github.com/louspringer/ontology-framework.git
   cd cllm
   ```
3. Set up framework symlinks:
   ```bash
   python ontology/setup_symlinks.py
   ```
4. Run all verifications:
   ```bash
   cd ontology
   ./verify_all.sh  # Will be created by test suite
   ``` 