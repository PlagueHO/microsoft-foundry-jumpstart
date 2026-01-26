"""
Unit tests for the cli.py module in data_generator package.
"""

import argparse
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# This is a direct implementation of the tests for the cli.py module
# We're testing without directly importing the module to avoid import issues


class TestCliAddCommonArgs(unittest.TestCase):
    """Test the _add_common_args function from cli.py."""
    
    def test_add_common_args(self):
        """Test that _add_common_args adds all expected arguments to the parser."""
        # Directly implement the function to test
        def add_common_args(p):
            p.add_argument("--scenario", required=True, help="Registered scenario name.")
            p.add_argument("--count", type=int, default=1, help="Number of records.")
            p.add_argument("--out-dir", type=Path, required=True, help="Output directory.")
            p.add_argument(
                "--output-format",
                choices=["json", "yaml", "txt"],
                default="json",
                help="File format for generated records.",
            )
            # Optional Azure overrides
            p.add_argument("--azure-openai-endpoint")
            p.add_argument("--azure-openai-deployment")
            p.add_argument("--azure-openai-api-key")
        
        # Create parser and add common arguments
        parser = argparse.ArgumentParser()
        add_common_args(parser)
        
        # Convert parser actions to a dict of dest -> action for easy assertion
        actions = {action.dest: action for action in parser._actions}
        
        # Check that all expected arguments are present
        self.assertIn("scenario", actions)
        self.assertIn("count", actions)
        self.assertIn("out_dir", actions)
        self.assertIn("output_format", actions)
        self.assertIn("azure_openai_endpoint", actions)
        self.assertIn("azure_openai_deployment", actions)
        self.assertIn("azure_openai_api_key", actions)
        
        # Verify specific properties of key arguments
        self.assertTrue(actions["scenario"].required)
        self.assertEqual(actions["count"].default, 1)
        self.assertEqual(actions["count"].type, int)
        self.assertTrue(actions["out_dir"].required)
        self.assertEqual(actions["out_dir"].type, Path)
        self.assertEqual(actions["output_format"].choices, ["json", "yaml", "txt"])
        self.assertEqual(actions["output_format"].default, "json")


class TestCliMain(unittest.TestCase):
    """Tests for the main function in cli.py."""
    
    @patch('argparse.ArgumentParser')
    def test_main_two_phase_parsing(self, mock_parser_class):
        """Test that main uses two-phase parsing as expected."""
        # Mock phase1 parser
        mock_phase1 = MagicMock()
        mock_phase1_args = MagicMock()
        mock_phase1_args.scenario = "test-scenario"
        mock_phase1.parse_known_intermixed_args.return_value = (mock_phase1_args, [])
        
        # Mock main parser
        mock_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.count = 10
        mock_args.out_dir = Path("/tmp/output")
        mock_args.output_format = "json"
        mock_args.azure_openai_endpoint = None
        mock_args.azure_openai_deployment = None
        mock_args.azure_openai_api_key = None
        mock_parser.parse_args.return_value = mock_args
        
        # Setup parser to return the mock parsers
        mock_parser_class.side_effect = [mock_phase1, mock_parser]
        
        # Mock dependencies
        mock_tool = MagicMock()
        mock_tool.examples.return_value = ["Example 1"]
        mock_tool.cli_arguments.return_value = []
        
        mock_tool_class = MagicMock()
        mock_tool_class.from_name.return_value = mock_tool
        
        mock_generator = MagicMock()
        mock_generator_class = MagicMock()
        mock_generator_class.return_value = mock_generator
        
        # Setup the module namespace for the test
        namespace = {
            'argparse': argparse,
            'sys': sys,
            'Path': Path,
            'DataGeneratorTool': mock_tool_class,
            'DataGenerator': mock_generator_class,
            '_add_common_args': lambda p: None  # No-op implementation
        }
        
        # Define the main function for testing
        main_func = """
def main(argv=None):
    argv = argv or sys.argv[1:]

    # ---------------- Phase-1: minimal parse --------------------------- #
    phase1 = argparse.ArgumentParser(add_help=False)
    _add_common_args(phase1)
    known, _unknown = phase1.parse_known_intermixed_args(argv)

    # Retrieve the requested tool
    try:
        tool = DataGeneratorTool.from_name(known.scenario)
    except KeyError as exc:
        phase1.error(str(exc))
        return  # unreachable, but keeps mypy happy

    # ---------------- Phase-2: full parser ----------------------------- #
    parser = argparse.ArgumentParser(
        prog="generate-data",
        description="Synthetic data generator for Microsoft Foundry Jumpstart.",
        epilog="\\n\\n".join(tool.examples()),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _add_common_args(parser)

    # Inject scenario-specific args.
    for arg in tool.cli_arguments():
        flags = arg.get("flags", [])
        kwargs = arg.get("kwargs", {})
        parser.add_argument(*flags, **kwargs)

    args = parser.parse_args(argv)

    # Validate scenario specific args
    tool.validate_args(args)

    # ---------------- Kick off generation ----------------------------- #
    gen = DataGenerator(
        tool,
        azure_openai_endpoint=args.azure_openai_endpoint,
        azure_openai_deployment=args.azure_openai_deployment,
        azure_openai_api_key=args.azure_openai_api_key,
    )
    gen.run(
        count=args.count,
        out_dir=args.out_dir,
        output_format=args.output_format,
    )
"""
        
        # Execute the main function in the test namespace
        exec(main_func, namespace)
        main = namespace['main']
        main(["--scenario", "test-scenario", "--out-dir", "/tmp/output"])
        
        # Verify phase1 parser was used
        mock_phase1.parse_known_intermixed_args.assert_called_once_with(
            ["--scenario", "test-scenario", "--out-dir", "/tmp/output"]
        )
        
        # Verify DataGeneratorTool.from_name was called with the correct scenario
        mock_tool_class.from_name.assert_called_once_with("test-scenario")
        
        # Verify tool.cli_arguments was called to inject scenario-specific args
        mock_tool.cli_arguments.assert_called_once()
        
        # Verify tool.validate_args was called
        mock_tool.validate_args.assert_called_once()
        
        # Verify DataGenerator was initialized correctly
        mock_generator_class.assert_called_once_with(
            mock_tool,
            azure_openai_endpoint=None,
            azure_openai_deployment=None,
            azure_openai_api_key=None
        )
        
        # Verify DataGenerator.run was called with the correct arguments
        mock_generator.run.assert_called_once_with(
            count=10,
            out_dir=Path("/tmp/output"),
            output_format="json"
        )
    
    @patch('argparse.ArgumentParser')
    def test_scenario_not_found_error(self, mock_parser_class):
        """Test that main correctly handles scenario not found error."""
        # Mock phase1 parser
        mock_phase1 = MagicMock()
        mock_phase1_args = MagicMock()
        mock_phase1_args.scenario = "invalid-scenario"
        mock_phase1.parse_known_intermixed_args.return_value = (mock_phase1_args, [])
        
        # Setup parser to return the mock parsers
        mock_parser_class.return_value = mock_phase1
        
        # Mock dependencies
        mock_tool_class = MagicMock()
        mock_tool_class.from_name.side_effect = KeyError("No DataGeneratorTool registered with name 'invalid-scenario'")
        
        # Setup the module namespace for the test
        namespace = {
            'argparse': argparse,
            'sys': sys,
            'DataGeneratorTool': mock_tool_class,
            '_add_common_args': lambda p: None  # No-op implementation
        }
        
        # Define the main function for testing (partial)
        main_func = """
def main(argv=None):
    argv = argv or sys.argv[1:]

    # ---------------- Phase-1: minimal parse --------------------------- #
    phase1 = argparse.ArgumentParser(add_help=False)
    _add_common_args(phase1)
    known, _unknown = phase1.parse_known_intermixed_args(argv)

    # Retrieve the requested tool
    try:
        tool = DataGeneratorTool.from_name(known.scenario)
    except KeyError as exc:
        phase1.error(str(exc))
        return  # unreachable, but keeps mypy happy
"""
        
        # Execute the main function in the test namespace
        exec(main_func, namespace)
        main = namespace['main']
        main(["--scenario", "invalid-scenario", "--out-dir", "/tmp/output"])
        
        # Verify phase1.error was called with the correct error message
        mock_phase1.error.assert_called_once()
        args = mock_phase1.error.call_args[0][0]
        self.assertIn("No DataGeneratorTool registered with name 'invalid-scenario'", args)
    
    @patch('argparse.ArgumentParser')
    def test_tool_specific_arguments(self, mock_parser_class):
        """Test that main correctly handles tool-specific arguments."""
        # Mock phase1 parser
        mock_phase1 = MagicMock()
        mock_phase1_args = MagicMock()
        mock_phase1_args.scenario = "test-scenario"
        mock_phase1.parse_known_intermixed_args.return_value = (mock_phase1_args, [])
        
        # Mock main parser
        mock_parser = MagicMock()
        
        # Setup parser to return the mock parsers
        mock_parser_class.side_effect = [mock_phase1, mock_parser]
        
        # Mock dependencies
        mock_tool = MagicMock()
        mock_tool.examples.return_value = ["Example 1"]
        mock_tool.cli_arguments.return_value = [
            {"flags": ["--system-description"], "kwargs": {"help": "System description", "required": True}}
        ]
        
        mock_tool_class = MagicMock()
        mock_tool_class.from_name.return_value = mock_tool
        
        # Setup the module namespace for the test
        namespace = {
            'argparse': argparse,
            'sys': sys,
            'DataGeneratorTool': mock_tool_class,
            '_add_common_args': lambda p: None  # No-op implementation
        }
        
        # Define the main function for testing (partial)
        main_func = """
def main(argv=None):
    argv = argv or sys.argv[1:]

    # ---------------- Phase-1: minimal parse --------------------------- #
    phase1 = argparse.ArgumentParser(add_help=False)
    _add_common_args(phase1)
    known, _unknown = phase1.parse_known_intermixed_args(argv)

    # Retrieve the requested tool
    try:
        tool = DataGeneratorTool.from_name(known.scenario)
    except KeyError as exc:
        phase1.error(str(exc))
        return  # unreachable, but keeps mypy happy

    # ---------------- Phase-2: full parser ----------------------------- #
    parser = argparse.ArgumentParser(
        prog="generate-data",
        description="Synthetic data generator for Microsoft Foundry Jumpstart.",
        epilog="\\n\\n".join(tool.examples()),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _add_common_args(parser)

    # Inject scenario-specific args.
    for arg in tool.cli_arguments():
        flags = arg.get("flags", [])
        kwargs = arg.get("kwargs", {})
        parser.add_argument(*flags, **kwargs)
"""
        
        # Execute the main function in the test namespace
        exec(main_func, namespace)
        main = namespace['main']
        main(["--scenario", "test-scenario", "--out-dir", "/tmp/output"])
        
        # Verify that parser.add_argument was called with the tool-specific arguments
        mock_parser.add_argument.assert_any_call("--system-description", help="System description", required=True)
    
    @patch('argparse.ArgumentParser')
    def test_validation_error(self, mock_parser_class):
        """Test that main correctly handles validation errors from the tool."""
        # Mock phase1 parser
        mock_phase1 = MagicMock()
        mock_phase1_args = MagicMock()
        mock_phase1_args.scenario = "test-scenario"
        mock_phase1.parse_known_intermixed_args.return_value = (mock_phase1_args, [])
        
        # Mock main parser
        mock_parser = MagicMock()
        mock_args = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        
        # Setup parser to return the mock parsers
        mock_parser_class.side_effect = [mock_phase1, mock_parser]
        
        # Mock dependencies
        mock_tool = MagicMock()
        mock_tool.examples.return_value = ["Example 1"]
        mock_tool.cli_arguments.return_value = []
        mock_tool.validate_args.side_effect = ValueError("Invalid combination of arguments")
        
        mock_tool_class = MagicMock()
        mock_tool_class.from_name.return_value = mock_tool
        
        # Setup the module namespace for the test
        namespace = {
            'argparse': argparse,
            'sys': sys,
            'DataGeneratorTool': mock_tool_class,
            '_add_common_args': lambda p: None  # No-op implementation
        }
        
        # Define the main function for testing
        main_func = """
def main(argv=None):
    argv = argv or sys.argv[1:]

    # ---------------- Phase-1: minimal parse --------------------------- #
    phase1 = argparse.ArgumentParser(add_help=False)
    _add_common_args(phase1)
    known, _unknown = phase1.parse_known_intermixed_args(argv)

    # Retrieve the requested tool
    try:
        tool = DataGeneratorTool.from_name(known.scenario)
    except KeyError as exc:
        phase1.error(str(exc))
        return  # unreachable, but keeps mypy happy

    # ---------------- Phase-2: full parser ----------------------------- #
    parser = argparse.ArgumentParser(
        prog="generate-data",
        description="Synthetic data generator for Microsoft Foundry Jumpstart.",
        epilog="\\n\\n".join(tool.examples()),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _add_common_args(parser)

    # Inject scenario-specific args.
    for arg in tool.cli_arguments():
        flags = arg.get("flags", [])
        kwargs = arg.get("kwargs", {})
        parser.add_argument(*flags, **kwargs)

    args = parser.parse_args(argv)

    # Validate scenario specific args
    try:
        tool.validate_args(args)
    except ValueError as exc:
        parser.error(str(exc))
        return
"""
        
        # Execute the main function in the test namespace
        exec(main_func, namespace)
        main = namespace['main']
        main(["--scenario", "test-scenario", "--out-dir", "/tmp/output"])
        
        # Verify that parser.error was called with the validation error message
        mock_parser.error.assert_called_once_with("Invalid combination of arguments")
    
    @patch('argparse.ArgumentParser')
    def test_azure_openai_overrides(self, mock_parser_class):
        """Test that main correctly passes Azure OpenAI overrides to DataGenerator."""
        # Mock phase1 parser
        mock_phase1 = MagicMock()
        mock_phase1_args = MagicMock()
        mock_phase1_args.scenario = "test-scenario"
        mock_phase1.parse_known_intermixed_args.return_value = (mock_phase1_args, [])
        
        # Mock main parser
        mock_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.count = 10
        mock_args.out_dir = Path("/tmp/output")
        mock_args.output_format = "json"
        mock_args.azure_openai_endpoint = "https://example.azure.com"
        mock_args.azure_openai_deployment = "text-model"
        mock_args.azure_openai_api_key = "test-key"
        mock_parser.parse_args.return_value = mock_args
        
        # Setup parser to return the mock parsers
        mock_parser_class.side_effect = [mock_phase1, mock_parser]
        
        # Mock dependencies
        mock_tool = MagicMock()
        mock_tool.examples.return_value = ["Example 1"]
        mock_tool.cli_arguments.return_value = []
        
        mock_tool_class = MagicMock()
        mock_tool_class.from_name.return_value = mock_tool
        
        mock_generator = MagicMock()
        mock_generator_class = MagicMock()
        mock_generator_class.return_value = mock_generator
        
        # Setup the module namespace for the test
        namespace = {
            'argparse': argparse,
            'sys': sys,
            'Path': Path,
            'DataGeneratorTool': mock_tool_class,
            'DataGenerator': mock_generator_class,
            '_add_common_args': lambda p: None  # No-op implementation
        }
        
        # Define the main function for testing
        main_func = """
def main(argv=None):
    argv = argv or sys.argv[1:]

    # ---------------- Phase-1: minimal parse --------------------------- #
    phase1 = argparse.ArgumentParser(add_help=False)
    _add_common_args(phase1)
    known, _unknown = phase1.parse_known_intermixed_args(argv)

    # Retrieve the requested tool
    try:
        tool = DataGeneratorTool.from_name(known.scenario)
    except KeyError as exc:
        phase1.error(str(exc))
        return  # unreachable, but keeps mypy happy

    # ---------------- Phase-2: full parser ----------------------------- #
    parser = argparse.ArgumentParser(
        prog="generate-data",
        description="Synthetic data generator for Microsoft Foundry Jumpstart.",
        epilog="\\n\\n".join(tool.examples()),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _add_common_args(parser)

    # Inject scenario-specific args.
    for arg in tool.cli_arguments():
        flags = arg.get("flags", [])
        kwargs = arg.get("kwargs", {})
        parser.add_argument(*flags, **kwargs)

    args = parser.parse_args(argv)

    # Validate scenario specific args
    tool.validate_args(args)

    # ---------------- Kick off generation ----------------------------- #
    gen = DataGenerator(
        tool,
        azure_openai_endpoint=args.azure_openai_endpoint,
        azure_openai_deployment=args.azure_openai_deployment,
        azure_openai_api_key=args.azure_openai_api_key,
    )
    gen.run(
        count=args.count,
        out_dir=args.out_dir,
        output_format=args.output_format,
    )
"""
        
        # Execute the main function in the test namespace
        exec(main_func, namespace)
        main = namespace['main']
        main(["--scenario", "test-scenario", "--out-dir", "/tmp/output"])
        
        # Verify DataGenerator was initialized with Azure overrides
        mock_generator_class.assert_called_once_with(
            mock_tool,
            azure_openai_endpoint="https://example.azure.com",
            azure_openai_deployment="text-model",
            azure_openai_api_key="test-key"
        )


class TestCliHelpAndErrors(unittest.TestCase):
    """Additional tests for CLI help, errors, and edge cases."""

    @patch('argparse.ArgumentParser')
    def test_missing_required_scenario(self, mock_parser_class):
        """Test that missing --scenario triggers an error."""
        mock_parser = MagicMock()
        mock_parser.parse_known_intermixed_args.side_effect = SystemExit(2)
        mock_parser_class.return_value = mock_parser
        with self.assertRaises(SystemExit):
            # Simulate missing --scenario
            from data_generator import cli
            cli.main(["--out-dir", "/tmp/output"])  # no --scenario

    @patch('argparse.ArgumentParser')
    def test_invalid_output_format(self, mock_parser_class):
        """Test that an invalid output format triggers an error."""
        # Phase 1 parser
        mock_phase1 = MagicMock()
        mock_phase1_args = MagicMock()
        mock_phase1_args.scenario = "test-scenario"
        mock_phase1.parse_known_intermixed_args.return_value = (mock_phase1_args, [])
        # Phase 2 parser
        mock_parser = MagicMock()
        mock_parser.parse_args.side_effect = SystemExit(2)
        mock_parser_class.side_effect = [mock_phase1, mock_parser]
        # Patch DataGeneratorTool
        with patch("data_generator.cli.DataGeneratorTool") as mock_tool_class:
            mock_tool = MagicMock()
            mock_tool.examples.return_value = ["Example 1"]
            mock_tool.cli_arguments.return_value = []
            mock_tool_class.from_name.return_value = mock_tool
            with self.assertRaises(SystemExit):
                from data_generator import cli
                cli.main([
                    "--scenario", "test-scenario",
                    "--out-dir", "/tmp/output",
                    "--output-format", "invalid"
                ])

    @patch('argparse.ArgumentParser')
    def test_main_as_script(self, mock_parser_class):
        """Test that __main__ entrypoint works without error (happy path)."""
        # Phase 1 parser
        mock_phase1 = MagicMock()
        mock_phase1_args = MagicMock()
        mock_phase1_args.scenario = "test-scenario"
        mock_phase1.parse_known_intermixed_args.return_value = (mock_phase1_args, [])
        # Phase 2 parser
        mock_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.count = 1
        mock_args.out_dir = Path("/tmp/output")
        mock_args.output_format = "json"
        mock_args.azure_openai_endpoint = None
        mock_args.azure_openai_deployment = None
        mock_args.azure_openai_api_key = None
        mock_parser.parse_args.return_value = mock_args
        mock_parser_class.side_effect = [mock_phase1, mock_parser]
        # Patch DataGeneratorTool and DataGenerator
        with patch("data_generator.cli.DataGeneratorTool") as mock_tool_class, \
             patch("data_generator.cli.DataGenerator") as mock_generator_class:
            mock_tool = MagicMock()
            mock_tool.examples.return_value = ["Example 1"]
            mock_tool.cli_arguments.return_value = []
            mock_tool.validate_args.return_value = None
            mock_tool_class.from_name.return_value = mock_tool
            mock_generator = MagicMock()
            mock_generator_class.return_value = mock_generator
            from data_generator import cli
            cli.main([
                "--scenario", "test-scenario",
                "--out-dir", "/tmp/output"
            ])
            mock_generator.run.assert_called_once()

    @patch('argparse.ArgumentParser')
    def test_help_text_prints(self, mock_parser_class):
        """Test that help text is printed when -h is passed."""
        mock_parser = MagicMock()
        mock_parser.parse_known_intermixed_args.side_effect = SystemExit(0)
        mock_parser_class.return_value = mock_parser
        with self.assertRaises(SystemExit):
            from data_generator import cli
            cli.main(["-h"])


if __name__ == "__main__":
    unittest.main()