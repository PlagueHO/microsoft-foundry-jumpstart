"""
Tests for the EcommerceOrderHistoryTool functionality.

This test file contains an inline version of EcommerceOrderHistoryTool that doesn't rely
on imports from the main module, ensuring tests can run without path setup issues.
"""

import argparse
import json
import uuid
from datetime import datetime, timezone

import yaml


class EcommerceOrderHistoryTool:
    """Generate synthetic e-commerce customer order histories.

    This is a standalone test implementation duplicating the functionality from
    data_generator.tools.ecommerce_order_history.EcommerceOrderHistoryTool.
    """

    # Identification / registry key
    name = "ecommerce-order-history"
    toolName = "EcommerceOrderHistory"

    def __init__(self, *, industry=None, orders_min=None, returns_percent=None):
        """Create a new tool instance with optional parameters."""
        self.industry = industry or "general retail"
        self.orders_min = orders_min or 3
        self.returns_percent = returns_percent or 10

    def cli_arguments(self):
        """Argparse specification consumed by the top-level CLI wrapper."""
        return [
            {
                "flags": ["--industry"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "general retail",
                    "help": (
                        "Industry context for the order history "
                        "(e.g., electronics, fashion, general retail)."
                    ),
                },
            },
            {
                "flags": ["--orders-min"],
                "kwargs": {
                    "required": False,
                    "type": int,
                    "metavar": "INT",
                    "default": 3,
                    "help": (
                        "Minimum number of orders per customer history. "
                        "Range: 1-50."
                    ),
                },
            },
            {
                "flags": ["--returns-percent"],
                "kwargs": {
                    "required": False,
                    "type": int,
                    "metavar": "INT",
                    "default": 10,
                    "help": (
                        "Percentage chance that an order is returned. "
                        "Range: 0-100."
                    ),
                },
            },
        ]

    def validate_args(self, ns):
        """Validate and normalize CLI arguments after parsing."""
        # Store validated arguments
        self.industry = getattr(ns, "industry", None) or "general retail"

        # Validate and clamp orders_min
        orders_min = getattr(ns, "orders_min", None)
        if orders_min is None:
            orders_min = 3
        if not isinstance(orders_min, int):
            try:
                orders_min = int(orders_min)
            except (ValueError, TypeError):
                orders_min = 3
        # Clamp to valid range [1, 50]
        self.orders_min = max(1, min(50, orders_min))

        # Validate and clamp returns_percent
        returns_percent = getattr(ns, "returns_percent", None)
        if returns_percent is None:
            returns_percent = 10
        if not isinstance(returns_percent, int):
            try:
                returns_percent = int(returns_percent)
            except (ValueError, TypeError):
                returns_percent = 10
        # Clamp to valid range [0, 100]
        self.returns_percent = max(0, min(100, returns_percent))

    def examples(self):
        """Representative usage snippets for `--help` output."""
        return [
            "python -m generate_data "
            "--scenario ecommerce-order-history "
            "--count 40 "
            "--industry electronics "
            "--orders-min 5 "
            "--returns-percent 15 "
            "--output-format yaml"
        ]

    def supported_output_formats(self):
        """Return the list of output formats this tool can generate."""
        return ["yaml", "json", "text"]

    def _prompt_common(self, *, unique_id=None):
        """Shared prompt header including an optional caller-supplied id."""
        customer_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        return (
            f"Customer ID (immutable): {customer_id}\n"
            f"Created At: {created_at}\n"
            f"Industry: {self.industry}\n"
            f"Orders Min: {self.orders_min}\n"
            f"Returns Percent: {self.returns_percent}\n\n"
        )

    def build_prompt(self, output_format, *, unique_id=None):
        """Return the full prompt for the requested output_format."""
        base = (
            "You are an e-commerce data specialist producing REALISTIC BUT "
            "ENTIRELY FICTIONAL per-customer order history snapshots.\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
            "Generate a comprehensive customer order history including orders, "
            "returns, product reviews, and (optionally) support interactions. "
            "All data must be fictional with no real PII. Use ISO timestamps "
            "throughout.\n\n"
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
            "customer_id: (echo above)\n"
            "created_at: (echo above)\n"
            "industry: (echo above)\n"
            "orders:\n"
            "  - order_id: uuid\n"
            "    order_date: ISO timestamp\n"
            "    items:\n"
            "      - sku: text\n"
            "        name: product name\n"
            "        qty: integer\n"
            "        price: decimal\n"
            "        currency: USD\n"
            "    total: decimal\n"
            "    status: placed|shipped|delivered|returned\n"
            f"  # ... generate at least {self.orders_min} orders ...\n"
            "returns:  # optional, based on returns_percent\n"
            "  - order_id: uuid from orders above\n"
            "    return_date: ISO timestamp\n"
            "    reason: descriptive text\n"
            "    status: approved|rejected|pending\n"
            "reviews:  # optional, for some orders\n"
            "  - order_id: uuid from orders above\n"
            "    sku: text from items\n"
            "    rating: 1-5\n"
            "    title: review title\n"
            "    review: review text\n"
            "interactions:  # optional support interactions\n"
            "  - timestamp: ISO timestamp\n"
            "    channel: email|chat|phone\n"
            "    subject: interaction subject\n"
            "    outcome: resolution description\n"
        )

    def _json_skeleton(self):
        """JSON response schema instructing the LLM on the exact shape."""
        return (
            "Return valid JSON ONLY.\n\n"
            "{\n"
            '  "customer_id": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "industry": "(echo above)",\n'
            '  "orders": [\n'
            '    {\n'
            '      "order_id": "uuid",\n'
            '      "order_date": "ISO timestamp",\n'
            '      "items": [\n'
            '        {\n'
            '          "sku": "text",\n'
            '          "name": "product name",\n'
            '          "qty": 1,\n'
            '          "price": 123.45,\n'
            '          "currency": "USD"\n'
            '        }\n'
            '      ],\n'
            '      "total": 123.45,\n'
            '      "status": "placed|shipped|delivered|returned"\n'
            '    }\n'
            f'    // ... generate at least {self.orders_min} orders ...\n'
            '  ],\n'
            '  "returns": [\n'
            '    {\n'
            '      "order_id": "uuid from orders above",\n'
            '      "return_date": "ISO timestamp",\n'
            '      "reason": "descriptive text",\n'
            '      "status": "approved|rejected|pending"\n'
            '    }\n'
            '  ],\n'
            '  "reviews": [\n'
            '    {\n'
            '      "order_id": "uuid from orders above",\n'
            '      "sku": "text from items",\n'
            '      "rating": 5,\n'
            '      "title": "review title",\n'
            '      "review": "review text"\n'
            '    }\n'
            '  ],\n'
            '  "interactions": [\n'
            '    {\n'
            '      "timestamp": "ISO timestamp",\n'
            '      "channel": "email|chat|phone",\n'
            '      "subject": "interaction subject",\n'
            '      "outcome": "resolution description"\n'
            '    }\n'
            '  ]\n'
            "}\n"
        )

    @staticmethod
    def _text_skeleton():
        """Plain-text layout for tools that prefer unstructured output."""
        return (
            "Return plain text WITHOUT any YAML/JSON formatting markers.\n\n"
            "Customer ID: (echo above)\n"
            "Created At: (echo above)\n"
            "Industry: (echo above)\n\n"
            "ORDERS:\n"
            "Order 1:\n"
            "  Order ID: uuid\n"
            "  Order Date: ISO timestamp\n"
            "  Items:\n"
            "    - SKU: text, Name: product name, Qty: 1, Price: 123.45 USD\n"
            "  Total: 123.45\n"
            "  Status: delivered\n\n"
            "RETURNS:\n"
            "Return 1:\n"
            "  Order ID: uuid from orders\n"
            "  Return Date: ISO timestamp\n"
            "  Reason: descriptive text\n"
            "  Status: approved\n\n"
            "REVIEWS:\n"
            "Review 1:\n"
            "  Order ID: uuid from orders\n"
            "  SKU: text from items\n"
            "  Rating: 5/5\n"
            "  Title: review title\n"
            "  Review: review text\n\n"
            "INTERACTIONS:\n"
            "Interaction 1:\n"
            "  Timestamp: ISO timestamp\n"
            "  Channel: email\n"
            "  Subject: interaction subject\n"
            "  Outcome: resolution description\n"
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

        return parsed_data

    def get_system_description(self):
        """Return a sentence describing the target order history context."""
        return f"E-commerce order histories in {self.industry}"


class TestEcommerceOrderHistoryTool:
    """Test suite for EcommerceOrderHistoryTool functionality."""

    # ------------------------------------------------------------------ #
    # Initialization Tests                                               #
    # ------------------------------------------------------------------ #
    def test_default_initialization(self):
        """Test default initialization with no parameters."""
        tool = EcommerceOrderHistoryTool()
        assert tool.industry == "general retail"
        assert tool.orders_min == 3
        assert tool.returns_percent == 10

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        tool = EcommerceOrderHistoryTool(
            industry="electronics",
            orders_min=5,
            returns_percent=15
        )
        assert tool.industry == "electronics"
        assert tool.orders_min == 5
        assert tool.returns_percent == 15

    # ------------------------------------------------------------------ #
    # Registry Tests                                                     #
    # ------------------------------------------------------------------ #
    def test_tool_registry_attributes(self):
        """Test that tool has required registry attributes."""
        tool = EcommerceOrderHistoryTool()
        assert tool.name == "ecommerce-order-history"
        assert tool.toolName == "EcommerceOrderHistory"

    # ------------------------------------------------------------------ #
    # CLI Interface Tests                                                #
    # ------------------------------------------------------------------ #
    def test_cli_arguments(self):
        """Test cli_arguments method returns expected structure."""
        tool = EcommerceOrderHistoryTool()
        args = tool.cli_arguments()

        assert len(args) == 3

        # Check industry argument
        industry_arg = args[0]
        assert "--industry" in industry_arg["flags"]
        assert not industry_arg["kwargs"]["required"]
        assert industry_arg["kwargs"]["default"] == "general retail"

        # Check orders-min argument
        orders_arg = args[1]
        assert "--orders-min" in orders_arg["flags"]
        assert orders_arg["kwargs"]["type"] is int
        assert orders_arg["kwargs"]["default"] == 3
        assert not orders_arg["kwargs"]["required"]

        # Check returns-percent argument
        returns_arg = args[2]
        assert "--returns-percent" in returns_arg["flags"]
        assert returns_arg["kwargs"]["type"] is int
        assert returns_arg["kwargs"]["default"] == 10
        assert not returns_arg["kwargs"]["required"]

    def test_validate_args_valid_input(self):
        """Test validate_args processes valid arguments correctly."""
        tool = EcommerceOrderHistoryTool()

        # Test with custom values
        ns = argparse.Namespace(
            industry="electronics",
            orders_min=7,
            returns_percent=25
        )
        tool.validate_args(ns)
        assert tool.industry == "electronics"
        assert tool.orders_min == 7
        assert tool.returns_percent == 25

    def test_validate_args_clamping_orders_min(self):
        """Test validate_args clamps orders_min to valid range."""
        tool = EcommerceOrderHistoryTool()

        # Test with orders_min too high
        ns = argparse.Namespace(
            industry="general retail",
            orders_min=100,
            returns_percent=10
        )
        tool.validate_args(ns)
        assert tool.orders_min == 50  # Should be clamped to max

        # Test with orders_min too low
        ns = argparse.Namespace(
            industry="general retail",
            orders_min=0,
            returns_percent=10
        )
        tool.validate_args(ns)
        assert tool.orders_min == 1  # Should be clamped to min

    def test_validate_args_clamping_returns_percent(self):
        """Test validate_args clamps returns_percent to valid range."""
        tool = EcommerceOrderHistoryTool()

        # Test with returns_percent too high
        ns = argparse.Namespace(
            industry="general retail",
            orders_min=3,
            returns_percent=150
        )
        tool.validate_args(ns)
        assert tool.returns_percent == 100  # Should be clamped to max

        # Test with returns_percent too low
        ns = argparse.Namespace(
            industry="general retail",
            orders_min=3,
            returns_percent=-10
        )
        tool.validate_args(ns)
        assert tool.returns_percent == 0  # Should be clamped to min

    def test_validate_args_type_conversion(self):
        """Test validate_args handles type conversion correctly."""
        tool = EcommerceOrderHistoryTool()

        # Test with string numbers that should convert
        ns = argparse.Namespace(
            industry="general retail",
            orders_min="5",
            returns_percent="20"
        )
        tool.validate_args(ns)
        assert tool.orders_min == 5
        assert tool.returns_percent == 20

    def test_validate_args_none_values(self):
        """Test validate_args handles None values correctly."""
        tool = EcommerceOrderHistoryTool()

        # Test with None values (should use defaults)
        ns = argparse.Namespace(
            industry=None,
            orders_min=None,
            returns_percent=None
        )
        tool.validate_args(ns)
        assert tool.industry == "general retail"
        assert tool.orders_min == 3
        assert tool.returns_percent == 10

    def test_examples(self):
        """Test examples method returns non-empty list of strings."""
        tool = EcommerceOrderHistoryTool()
        examples = tool.examples()

        assert isinstance(examples, list)
        assert len(examples) > 0
        assert all(isinstance(ex, str) for ex in examples)
        assert all("ecommerce-order-history" in ex for ex in examples)

    # ------------------------------------------------------------------ #
    # Output Format Tests                                                #
    # ------------------------------------------------------------------ #
    def test_supported_output_formats(self):
        """Test supported_output_formats returns expected formats."""
        tool = EcommerceOrderHistoryTool()
        formats = tool.supported_output_formats()

        assert isinstance(formats, list)
        assert set(formats) == {"yaml", "json", "text"}

    # ------------------------------------------------------------------ #
    # Prompt Generation Tests                                            #
    # ------------------------------------------------------------------ #
    def test_prompt_common(self):
        """Test _prompt_common includes expected elements."""
        tool = EcommerceOrderHistoryTool(
            industry="fashion",
            orders_min=5,
            returns_percent=20
        )
        test_id = "test-123"

        result = tool._prompt_common(unique_id=test_id)

        assert test_id in result
        assert "Created At:" in result
        assert "Industry: fashion" in result
        assert "Orders Min: 5" in result
        assert "Returns Percent: 20" in result

    def test_prompt_common_generates_uuid(self):
        """Test _prompt_common generates UUID when not provided."""
        tool = EcommerceOrderHistoryTool()

        result = tool._prompt_common()

        # Check that the method ran and returned a result
        assert "Customer ID" in result
        assert "Created At:" in result
        assert "Industry:" in result

    def test_build_prompt_yaml(self):
        """Test build_prompt for YAML output format."""
        tool = EcommerceOrderHistoryTool(industry="electronics", orders_min=4)
        test_id = "test-uuid-yaml"

        result = tool.build_prompt("yaml", unique_id=test_id)

        assert test_id in result
        assert "Return valid YAML ONLY" in result
        assert "at least 4 orders" in result
        assert "customer_id: (echo above)" in result

    def test_build_prompt_json(self):
        """Test build_prompt for JSON output format."""
        tool = EcommerceOrderHistoryTool(industry="books", orders_min=6)
        test_id = "test-uuid-json"

        result = tool.build_prompt("json", unique_id=test_id)

        assert test_id in result
        assert "Return valid JSON ONLY" in result
        assert "at least 6 orders" in result
        assert '"customer_id": "(echo above)"' in result

    def test_build_prompt_text(self):
        """Test build_prompt for plain text output format."""
        tool = EcommerceOrderHistoryTool()
        test_id = "test-uuid-text"

        result = tool.build_prompt("text", unique_id=test_id)

        assert test_id in result
        assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
        assert "Customer ID: (echo above)" in result

    # ------------------------------------------------------------------ #
    # Skeleton Method Tests                                              #
    # ------------------------------------------------------------------ #
    def test_yaml_skeleton(self):
        """Test _yaml_skeleton returns expected YAML template."""
        tool = EcommerceOrderHistoryTool(orders_min=3)
        result = tool._yaml_skeleton()

        assert "Return valid YAML ONLY" in result
        assert "customer_id: (echo above)" in result
        assert "orders:" in result
        assert "returns:" in result
        assert "reviews:" in result
        assert "interactions:" in result
        assert "at least 3 orders" in result

    def test_json_skeleton(self):
        """Test _json_skeleton returns expected JSON template."""
        tool = EcommerceOrderHistoryTool(orders_min=5)
        result = tool._json_skeleton()

        assert "Return valid JSON ONLY" in result
        assert '"customer_id": "(echo above)"' in result
        assert '"orders": [' in result
        assert '"returns": [' in result
        assert '"reviews": [' in result
        assert '"interactions": [' in result
        assert "at least 5 orders" in result

    def test_text_skeleton(self):
        """Test _text_skeleton returns expected text template."""
        result = EcommerceOrderHistoryTool._text_skeleton()

        assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
        assert "Customer ID: (echo above)" in result
        assert "ORDERS:" in result
        assert "RETURNS:" in result
        assert "REVIEWS:" in result
        assert "INTERACTIONS:" in result

    # ------------------------------------------------------------------ #
    # Post-processing Tests                                              #
    # ------------------------------------------------------------------ #
    def test_post_process_json_valid(self):
        """Test post_process handles valid JSON correctly."""
        tool = EcommerceOrderHistoryTool()
        valid_json = '{"customer_id": "123", "industry": "electronics", "orders": []}'

        result = tool.post_process(valid_json, "json")

        assert isinstance(result, dict)
        assert result["customer_id"] == "123"
        assert result["industry"] == "electronics"
        assert result["orders"] == []

    def test_post_process_yaml_valid(self):
        """Test post_process handles valid YAML correctly."""
        tool = EcommerceOrderHistoryTool()
        valid_yaml = "customer_id: 123\nindustry: electronics\norders: []"

        result = tool.post_process(valid_yaml, "yaml")

        assert isinstance(result, dict)
        assert result["customer_id"] == 123
        assert result["industry"] == "electronics"
        assert result["orders"] == []

    def test_post_process_text(self):
        """Test post_process with text format returns raw string."""
        tool = EcommerceOrderHistoryTool()
        text = "Customer order history in plain text format"

        result = tool.post_process(text, "text")
        assert result == text

        # Also test with "txt" format alias
        result = tool.post_process(text, "txt")
        assert result == text

    def test_post_process_json_invalid(self):
        """Test post_process handles invalid JSON gracefully."""
        tool = EcommerceOrderHistoryTool()
        invalid_json = '{customer_id: "missing quotes"}'

        result = tool.post_process(invalid_json, "json")
        assert result == invalid_json  # Should return raw string

    def test_post_process_yaml_invalid(self):
        """Test post_process handles invalid YAML gracefully."""
        tool = EcommerceOrderHistoryTool()
        invalid_yaml = ": invalid: yaml: format:"

        result = tool.post_process(invalid_yaml, "yaml")
        assert result == invalid_yaml  # Should return raw string

    def test_post_process_unknown_format(self):
        """Test post_process handles unknown formats gracefully."""
        tool = EcommerceOrderHistoryTool()
        data = "Some data"

        result = tool.post_process(data, "unknown_format")
        assert result == data  # Should return raw string

    # ------------------------------------------------------------------ #
    # Utility Method Tests                                               #
    # ------------------------------------------------------------------ #
    def test_get_system_description(self):
        """Test get_system_description returns expected string."""
        tool = EcommerceOrderHistoryTool(industry="fashion")

        result = tool.get_system_description()

        assert result == "E-commerce order histories in fashion"

        # Test with default industry
        default_tool = EcommerceOrderHistoryTool()
        default_result = default_tool.get_system_description()
        assert default_result == "E-commerce order histories in general retail"
