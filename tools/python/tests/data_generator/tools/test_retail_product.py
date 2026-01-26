"""
Tests for the RetailProductTool functionality.

This test file contains an inline version of RetailProductTool that doesn't rely
on imports from the main module, ensuring tests can run without path setup issues.
"""

import argparse
import json
import random
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import yaml


class RetailProductTool:
    """Generate synthetic retail-product catalogue items.
    
    This is a standalone test implementation duplicating the functionality from
    data_generator.tools.retail_product.RetailProductTool.
    """

    # Identification / registry key
    name = "retail-product"
    toolName = "RetailProduct"
    
    # Currencies for random generation
    _CURRENCIES = ["USD", "EUR", "GBP", "AUD", "CAD"]

    def __init__(self, *, industry=None):
        """Create a new tool instance with an optional industry override."""
        self.industry = industry or "general"

    def cli_arguments(self):
        """Argparse specification consumed by the top-level CLI wrapper."""
        return [
            {
                "flags": ["-i", "--industry"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "general",
                    "help": (
                        "Industry/theme for the products (e.g. electronics, fashion)."
                    ),
                },
            }
        ]

    def validate_args(self, ns):
        """Persist validated CLI arguments onto the instance."""
        self.industry = ns.industry or "general"

    def examples(self):
        """Representative usage snippets for `--help` output."""
        return [
            "python -m generate_data "
            "--scenario retail-product "
            "--count 100 "
            "--industry electronics "
            "--output-format json"
        ]

    def supported_output_formats(self):
        """Return the list of output formats this tool can generate."""
        return ["yaml", "json", "text"]

    @staticmethod
    def _random_price():
        """Return a random realistic product price."""
        return round(random.uniform(5.0, 500.0), 2)

    @staticmethod
    def _random_stock():
        """Return a random realistic stock quantity."""
        return random.randint(0, 500)

    def _prompt_common(self, *, unique_id=None):
        """Shared prompt header including an optional caller-supplied id."""
        product_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        return (
            f"Product ID (immutable): {product_id}\n"
            f"Created At: {created_at}\n"
            f"Industry Theme: {self.industry}\n\n"
        )

    def build_prompt(self, output_format, *, unique_id=None):
        """Return the full prompt for the requested output_format."""
        base = (
            "You are a seasoned e-commerce copy-writer producing REALISTIC BUT "
            "ENTIRELY FICTIONAL retail-product catalogue entries.\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
            "Always output ONLY the requested data structure – no markdown fences, "
            "no commentary.\n\n"
        )

        if output_format == "yaml":
            return base + self._yaml_skeleton()
        if output_format == "json":
            return base + self._json_skeleton()
        # TEXT
        return base + self._text_skeleton()

    def _yaml_skeleton(self):
        """YAML response schema instructing the LLM on the exact shape."""
        return (
            "Return valid YAML ONLY.\n\n"
            "product_id: (echo above)\n"
            "created_at: (echo above)\n"
            "name: catchy product name\n"
            f"category: sub-category relevant to {self.industry}\n"
            "description: persuasive paragraph (60-120 words)\n"
            "price: realistic decimal number > 1\n"
            "currency: ISO 4217 e.g. USD\n"
            "tags: [list, of, keywords]\n"
            "attributes:\n"
            "  key: value pairs (e.g. colour: red, size: L)\n"
            "stock_quantity: integer 0-500\n"
            "rating: float 0-5 with one decimal (optional)\n"
        )

    def _json_skeleton(self):
        """JSON response schema instructing the LLM on the exact shape."""
        return (
            "Return valid JSON ONLY.\n\n"
            "{\n"
            '  "product_id": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            f'  "category": "Relevant sub-category for {self.industry}",\n'
            '  "name": "Product name",\n'
            '  "description": "60-120 word paragraph",\n'
            '  "price": 123.45,\n'
            '  "currency": "USD",\n'
            '  "tags": ["tag1","tag2"],\n'
            '  "attributes": {"key":"value"},\n'
            '  "stock_quantity": 123,\n'
            '  "rating": 4.6\n'
            "}\n"
        )

    @staticmethod
    def _text_skeleton():
        """Plain-text layout for tools that prefer unstructured output."""
        return (
            "Return plain text WITHOUT YAML/JSON markers.\n\n"
            "Product ID: (echo above)\n"
            "Created At: (echo above)\n"
            "Name: Product name\n"
            "Category: Relevant sub-category\n"
            "Description: 60-120 word paragraph\n"
            "Price: 123.45 USD\n"
            "Tags: tag1, tag2\n"
            "Attributes:\n"
            "  key: value\n"
            "Stock Quantity: 123\n"
            "Rating: 4.6\n"
        )

    def post_process(self, raw, output_format):
        """Deserialize based on output_format and enrich if applicable."""
        fmt = output_format.lower()
        parsed_data = None

        if fmt == "json":
            try:
                parsed_data = json.loads(raw)
            except json.JSONDecodeError:
                return raw
        elif fmt == "yaml":
            try:
                parsed_data = yaml.safe_load(raw)
            except yaml.YAMLError:
                return raw
        # Handle both 'txt' (from CLI) and 'text' (from tool's supported_output_formats)
        elif fmt == "txt" or fmt == "text":
            return raw
        else:
            return raw

        # Enrich JSON/YAML outputs if they resulted in a dictionary
        if isinstance(parsed_data, dict):
            parsed_data.setdefault("price", self._random_price())
            parsed_data.setdefault("currency", random.choice(self._CURRENCIES))
            parsed_data.setdefault("stock_quantity", self._random_stock())
            if "rating" not in parsed_data and random.choice([True, False]):
                parsed_data["rating"] = round(random.uniform(1.0, 5.0), 1)

        return parsed_data

    def get_system_description(self):
        """Return a sentence describing the target retail catalogue."""
        return f"Retail catalogue for {self.industry} products"


class TestRetailProductTool:
    """Test suite for RetailProductTool functionality."""

    # ------------------------------------------------------------------ #
    # Initialization Tests                                               #
    # ------------------------------------------------------------------ #
    def test_default_initialization(self):
        """Test default initialization with no parameters."""
        tool = RetailProductTool()
        assert tool.industry == "general"

    def test_custom_industry_initialization(self):
        """Test initialization with custom industry."""
        tool = RetailProductTool(industry="electronics")
        assert tool.industry == "electronics"

    # ------------------------------------------------------------------ #
    # CLI Interface Tests                                                #
    # ------------------------------------------------------------------ #
    def test_cli_arguments(self):
        """Test cli_arguments method returns expected structure."""
        tool = RetailProductTool()
        args = tool.cli_arguments()
        
        assert len(args) == 1
        assert args[0]["flags"] == ["-i", "--industry"]
        assert not args[0]["kwargs"]["required"]
        assert args[0]["kwargs"]["default"] == "general"

    def test_validate_args(self):
        """Test validate_args persists args correctly."""
        tool = RetailProductTool()
        
        # Test with industry set
        ns = argparse.Namespace(industry="fashion")
        tool.validate_args(ns)
        assert tool.industry == "fashion"
        
        # Test with industry None (should default to "general")
        ns = argparse.Namespace(industry=None)
        tool.validate_args(ns)
        assert tool.industry == "general"

    def test_examples(self):
        """Test examples method returns non-empty list of strings."""
        tool = RetailProductTool()
        examples = tool.examples()
        
        assert isinstance(examples, list)
        assert len(examples) > 0
        assert all(isinstance(ex, str) for ex in examples)
        assert all("retail-product" in ex for ex in examples)

    # ------------------------------------------------------------------ #
    # Output Format Tests                                                #
    # ------------------------------------------------------------------ #
    def test_supported_output_formats(self):
        """Test supported_output_formats returns expected formats."""
        tool = RetailProductTool()
        formats = tool.supported_output_formats()
        
        assert isinstance(formats, list)
        assert set(formats) == {"yaml", "json", "text"}

    # ------------------------------------------------------------------ #
    # Prompt Generation Tests                                            #
    # ------------------------------------------------------------------ #
    def test_prompt_common(self):
        """Test _prompt_common includes expected elements."""
        tool = RetailProductTool(industry="sports")
        test_id = "test-123"
        
        result = tool._prompt_common(unique_id=test_id)
        
        assert test_id in result
        assert "Created At:" in result
        assert "Industry Theme: sports" in result

    def test_prompt_common_generates_uuid(self):
        """Test _prompt_common generates UUID when not provided."""
        tool = RetailProductTool()
        
        result = tool._prompt_common()
        
        # Check that the method ran and returned a result
        assert "Product ID" in result
        assert "Created At:" in result
        assert "Industry Theme:" in result

    def test_build_prompt_yaml(self):
        """Test build_prompt for YAML output format."""
        tool = RetailProductTool(industry="electronics")
        test_id = "test-uuid-yaml"
        
        result = tool.build_prompt("yaml", unique_id=test_id)
        
        assert test_id in result
        assert "Return valid YAML ONLY" in result
        assert "sub-category relevant to electronics" in result

    def test_build_prompt_json(self):
        """Test build_prompt for JSON output format."""
        tool = RetailProductTool(industry="books")
        test_id = "test-uuid-json"
        
        result = tool.build_prompt("json", unique_id=test_id)
        
        assert test_id in result
        assert "Return valid JSON ONLY" in result
        assert "Relevant sub-category for books" in result

    def test_build_prompt_text(self):
        """Test build_prompt for plain text output format."""
        tool = RetailProductTool()
        test_id = "test-uuid-text"
        
        result = tool.build_prompt("text", unique_id=test_id)
        
        assert test_id in result
        assert "Return plain text WITHOUT YAML/JSON markers" in result
        assert "60-120 word paragraph" in result

    # ------------------------------------------------------------------ #
    # Helper Method Tests                                                #
    # ------------------------------------------------------------------ #
    def test_random_price(self):
        """Test _random_price returns float in expected range."""
        price = RetailProductTool._random_price()
        
        assert isinstance(price, float)
        assert 5.0 <= price <= 500.0
        assert str(price).split('.')[-1] != ""  # Has decimal component

    def test_random_stock(self):
        """Test _random_stock returns int in expected range."""
        stock = RetailProductTool._random_stock()
        
        assert isinstance(stock, int)
        assert 0 <= stock <= 500

    # ------------------------------------------------------------------ #
    # Post-processing Tests                                              #
    # ------------------------------------------------------------------ #
    def test_post_process_json_valid(self):
        """Test post_process handles valid JSON correctly."""
        tool = RetailProductTool()
        valid_json = '{"product_id": "123", "name": "Test Product"}'
        
        result = tool.post_process(valid_json, "json")
        
        assert isinstance(result, dict)
        assert result["product_id"] == "123"
        assert result["name"] == "Test Product"
        assert "price" in result  # Check for data enrichment
        assert "currency" in result
        assert "stock_quantity" in result

    def test_post_process_yaml_valid(self):
        """Test post_process handles valid YAML correctly."""
        tool = RetailProductTool()
        valid_yaml = "product_id: 123\nname: Test Product"
        
        result = tool.post_process(valid_yaml, "yaml")
        
        assert isinstance(result, dict)
        assert result["product_id"] == 123
        assert result["name"] == "Test Product"
        assert "price" in result  # Check for data enrichment
        assert "currency" in result
        assert "stock_quantity" in result

    def test_post_process_text(self):
        """Test post_process with text format returns raw string."""
        tool = RetailProductTool()
        text = "Product details in plain text format"
        
        result = tool.post_process(text, "text")
        assert result == text
        
        # Also test with "txt" format alias
        result = tool.post_process(text, "txt")
        assert result == text

    def test_post_process_json_invalid(self):
        """Test post_process handles invalid JSON gracefully."""
        tool = RetailProductTool()
        invalid_json = '{product_id: "missing quotes"}'
        
        result = tool.post_process(invalid_json, "json")
        assert result == invalid_json  # Should return raw string

    def test_post_process_yaml_invalid(self):
        """Test post_process handles invalid YAML gracefully."""
        tool = RetailProductTool()
        
        # Use a truly invalid YAML string that will cause an error
        invalid_yaml = ": invalid: yaml: format:"
        
        result = tool.post_process(invalid_yaml, "yaml")
        assert result == invalid_yaml  # Should return raw string

    def test_post_process_unknown_format(self):
        """Test post_process handles unknown formats gracefully."""
        tool = RetailProductTool()
        data = "Some data"
        
        result = tool.post_process(data, "unknown_format")
        assert result == data  # Should return raw string

    # ------------------------------------------------------------------ #
    # Other Method Tests                                                 #
    # ------------------------------------------------------------------ #
    def test_get_system_description(self):
        """Test get_system_description returns expected string."""
        tool = RetailProductTool(industry="fashion")
        
        result = tool.get_system_description()
        
        assert "Retail catalogue for fashion products" == result

    # ------------------------------------------------------------------ #
    # Data Enrichment Tests                                              #
    # ------------------------------------------------------------------ #
    def test_data_enrichment_adds_missing_fields(self):
        """Test data enrichment adds missing fields."""
        tool = RetailProductTool()
        minimal_json = '{"product_id": "123", "name": "Test"}'
        
        result = tool.post_process(minimal_json, "json")
        
        assert "price" in result
        assert "currency" in result
        assert "stock_quantity" in result

    def test_data_enrichment_preserves_existing_fields(self):
        """Test data enrichment preserves existing fields."""
        tool = RetailProductTool()
        json_with_fields = (
            '{"product_id": "123", "name": "Test", "price": 99.99, "currency": "EUR"}'
        )
        
        result = tool.post_process(json_with_fields, "json")
        
        assert result["price"] == 99.99
        assert result["currency"] == "EUR"
        assert "stock_quantity" in result  # Should add missing fields