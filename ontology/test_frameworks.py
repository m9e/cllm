#!/usr/bin/env python3
"""Test suite for framework analysis tools."""
import unittest
from pathlib import Path
import tempfile
import os
import logging
from analyze_frameworks import analyze_framework_usage


class TestFrameworkAnalysis(unittest.TestCase):
    """Test cases for framework analysis."""

    def setUp(self):
        """Set up test fixtures."""
        logging.basicConfig(level=logging.INFO)

    def create_test_ttl(self, content):
        """Create a temporary TTL file with test content."""
        os.makedirs("test_data", exist_ok=True)
        test_file = Path("test_data/test.ttl")
        test_file.write_text(content)
        return test_file

    def test_empty_ontology(self):
        """Test analysis of empty ontology."""
        ttl = self.create_test_ttl("""
            @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix meta: <./meta#> .
            @prefix : <http://example.org/> .
        """)
        with self.assertLogs(level='INFO') as logs:
            analyze_framework_usage(ttl)
            print("\n".join(logs.output))
        self.assertTrue(any("No framework usage found" in msg for msg in logs.output))

    def test_framework_class_usage(self):
        """Test detection of framework class usage."""
        ttl = self.create_test_ttl("""
            @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix meta: <./meta#> .
            @prefix : <http://example.org/> .

            :MyClass rdfs:subClassOf meta:BaseClass .
        """)
        with self.assertLogs(level='INFO') as logs:
            analyze_framework_usage(ttl)
            print("\n".join(logs.output))
        self.assertTrue(any("meta -> 1 usages" in msg for msg in logs.output))

    def test_framework_property_usage(self):
        """Test detection of framework property usage."""
        ttl = self.create_test_ttl("""
            @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix process: <./process#> .
            @prefix : <http://example.org/> .

            :MyProperty rdfs:domain process:Task .
        """)
        with self.assertLogs(level='INFO') as logs:
            analyze_framework_usage(ttl)
            print("\n".join(logs.output))
        self.assertTrue(any("process -> 1 usages" in msg for msg in logs.output))

    def test_multiple_frameworks(self):
        """Test detection of multiple framework usage."""
        ttl = self.create_test_ttl("""
            @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix meta: <./meta#> .
            @prefix process: <./process#> .
            @prefix agent: <./agent#> .
            @prefix : <http://example.org/> .

            :Task rdfs:subClassOf process:Task .
            :Agent rdfs:subClassOf agent:Agent .
            :uses meta:hasRelation :Task .
        """)
        with self.assertLogs(level='INFO') as logs:
            analyze_framework_usage(ttl)
            print("\n".join(logs.output))
        self.assertTrue(any("3 frameworks used" in msg for msg in logs.output))

    def test_unused_prefix(self):
        """Test detection of unused framework prefix."""
        ttl = self.create_test_ttl("""
            @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix meta: <./meta#> .
            @prefix time: <./time#> .
            @prefix : <http://example.org/> .

            :MyClass rdfs:subClassOf meta:BaseClass .
        """)
        with self.assertLogs(level='INFO') as logs:
            analyze_framework_usage(ttl)
            print("\n".join(logs.output))
        self.assertTrue(any("Unused prefix: time" in msg for msg in logs.output))


if __name__ == '__main__':
    unittest.main() 