"""
Travel Booking Prompt Builder
=============================

Scenario-specific implementation of :class:`data_generator.tool.DataGeneratorTool`
that creates realistic (but fully fictional) travel booking records.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Any

import yaml

from ..tool import DataGeneratorTool

_logger = logging.getLogger(__name__)


class TravelBookingTool(DataGeneratorTool):
    """Generate synthetic travel booking records in YAML, JSON or plain-text."""

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "travel-booking"
    toolName: str = "TravelBooking"

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(
        self, *, trip_type: str | None = None, region: str | None = None
    ) -> None:
        """Instantiate the tool, optionally overriding trip_type and region."""
        super().__init__()
        self.trip_type = trip_type or "flight+hotel"
        self.region = region or "global"

    def cli_arguments(self) -> list[dict[str, Any]]:
        """Argparse specification consumed by the top-level CLI wrapper."""
        return [
            {
                "flags": ["--trip-type"],
                "kwargs": {
                    "choices": ["flight", "hotel", "flight+hotel"],
                    "default": "flight+hotel",
                    "help": "Type of travel booking to generate",
                },
            },
            {
                "flags": ["--region"],
                "kwargs": {
                    "default": "global",
                    "help": "Geographic region for the booking",
                },
            },
        ]

    def validate_args(self, ns: argparse.Namespace) -> None:
        """Validate and normalize arguments after CLI parsing."""
        # Normalize and store trip_type
        trip_type = getattr(ns, "trip_type", None) or "flight+hotel"
        if trip_type not in ["flight", "hotel", "flight+hotel"]:
            trip_type = "flight+hotel"
        self.trip_type = trip_type

        # Store region
        self.region = getattr(ns, "region", None) or "global"

    def examples(self) -> list[str]:
        """Representative usage snippets for `--help` output."""
        return [
            "python -m generate_data "
            "--scenario travel-booking "
            "--count 30 "
            "--trip-type flight+hotel "
            "--region Europe "
            "--output-format json"
        ]

    # ------------------------------------------------------------------ #
    # Output formats                                                     #
    # ------------------------------------------------------------------ #
    def supported_output_formats(self) -> list[str]:  # noqa: D401
        """Return the list of output formats this tool can generate."""
        return ["yaml", "json", "text"]

    # ------------------------------------------------------------------ #
    # Prompt construction                                                #
    # ------------------------------------------------------------------ #
    _BOOKING_STATUS: list[str] = ["confirmed", "pending", "canceled"]
    _AIRLINES: list[str] = [
        "Delta Air Lines",
        "American Airlines", 
        "United Airlines",
        "British Airways",
        "Lufthansa",
        "Air France",
        "Emirates",
        "Singapore Airlines"
    ]
    _HOTEL_CHAINS: list[str] = [
        "Marriott Hotels",
        "Hilton Hotels",
        "InterContinental",
        "Holiday Inn",
        "Sheraton",
        "Hyatt Hotels",
        "Best Western",
        "Radisson"
    ]

    def _random_attributes(self) -> tuple[str, str, str]:
        """Randomly choose booking status, airline, and hotel chain."""
        return (
            random.choice(self._BOOKING_STATUS),
            random.choice(self._AIRLINES),
            random.choice(self._HOTEL_CHAINS),
        )

    def _prompt_common(self, *, unique_id: str | None = None) -> str:
        """Return the invariant part of the prompt shared across formats."""
        booking_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        return (
            f"Booking ID (immutable): {booking_id}\n"
            f"Created At: {created_at}\n"
            f"Trip Type: {self.trip_type}\n"
            f"Region: {self.region}\n"
            "Use ISO-8601 timestamps and do NOT invent real PII.\n"
            "Use plausible but fictional airport codes, hotel names, and pricing.\n\n"
        )

    def build_prompt(
        self, output_format: str, *, unique_id: str | None = None
    ) -> str:  # noqa: D401
        """
        Construct the full system-prompt string for the requested *output_format*.
        All variable data (booking_id, timestamps, etc.) are pre-baked so the 
        kernel only receives the `index` placeholder supplied by the engine.
        """
        base = (
            "You are a helpful travel booking system generating REALISTIC BUT ENTIRELY "
            "FICTIONAL travel booking records for demonstrations.\n\n"
            "## BOOKING REQUIREMENTS\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
            "## INSTRUCTIONS\n\n"
            "Generate realistic booking data with plausible airport codes "
            "(IATA format), hotel chains, flight numbers, times, and prices. "
            "All traveler information should be clearly fictional. Use realistic "
            "but fake email addresses (e.g., @example.com domain). Prices should "
            "be in USD unless region implies otherwise.\n"
        )

        if output_format == "yaml":
            return base + self._yaml_skeleton()
        if output_format == "json":
            return base + self._json_skeleton()
        # Plain text is the default (handle both "text" and "txt")
        return base + self._text_skeleton()

    # ------------------------------------------------------------------ #
    # Static prompt fragments                                            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _yaml_skeleton() -> str:
        """YAML response schema instructing the LLM on the exact shape."""
        return (
            "Return VALID YAML ONLY (no markdown fences).\n\n"
            "booking_id: (echo above)\n"
            "created_at: (echo above)\n"
            "trip_type: flight|hotel|flight+hotel\n"
            "region: (echo above)\n"
            "traveler:\n"
            "  name: Fictional Name\n"
            "  email: fake@example.com\n"
            "itinerary:\n"
            "  flights:\n"
            "    - from: IATA_CODE\n"
            "      to: IATA_CODE\n"
            "      depart: ISO_8601_DATETIME\n"
            "      arrive: ISO_8601_DATETIME\n"
            "      airline: airline_name\n"
            "      flight_number: flight_code\n"
            "      fare:\n"
            "        amount: decimal\n"
            "        currency: USD\n"
            "  hotels:\n"
            "    - name: hotel_name\n"
            "      check_in: ISO_8601_DATE\n"
            "      check_out: ISO_8601_DATE\n"
            "      city: city_name\n"
            "      nightly_rate:\n"
            "        amount: decimal\n"
            "        currency: USD\n"
            "total_cost:\n"
            "  amount: decimal\n"
            "  currency: USD\n"
            "status: confirmed|pending|canceled\n"
            "customer_feedback:\n"
            "  rating: 1-5\n"
            "  comments: text (optional)\n"
        )

    @staticmethod
    def _json_skeleton() -> str:
        """JSON response schema instructing the LLM on the exact shape."""
        return (
            "Return VALID JSON ONLY (no markdown fences).\n\n"
            "{\n"
            '  "booking_id": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "trip_type": "flight|hotel|flight+hotel",\n'
            '  "region": "(echo above)",\n'
            '  "traveler": {\n'
            '    "name": "Fictional Name",\n'
            '    "email": "fake@example.com"\n'
            '  },\n'
            '  "itinerary": {\n'
            '    "flights": [{\n'
            '      "from": "IATA_CODE",\n'
            '      "to": "IATA_CODE",\n'
            '      "depart": "ISO_8601_DATETIME",\n'
            '      "arrive": "ISO_8601_DATETIME",\n'
            '      "airline": "airline_name",\n'
            '      "flight_number": "flight_code",\n'
            '      "fare": {\n'
            '        "amount": "decimal",\n'
            '        "currency": "USD"\n'
            '      }\n'
            '    }],\n'
            '    "hotels": [{\n'
            '      "name": "hotel_name",\n'
            '      "check_in": "ISO_8601_DATE",\n'
            '      "check_out": "ISO_8601_DATE",\n'
            '      "city": "city_name",\n'
            '      "nightly_rate": {\n'
            '        "amount": "decimal",\n'
            '        "currency": "USD"\n'
            '      }\n'
            '    }]\n'
            '  },\n'
            '  "total_cost": {\n'
            '    "amount": "decimal",\n'
            '    "currency": "USD"\n'
            '  },\n'
            '  "status": "confirmed|pending|canceled",\n'
            '  "customer_feedback": {\n'
            '    "rating": "1-5",\n'
            '    "comments": "text (optional)"\n'
            '  }\n'
            "}\n"
        )

    @staticmethod
    def _text_skeleton() -> str:
        """Plain-text layout for tools that prefer unstructured output."""
        return (
            "Return plain text WITHOUT any YAML/JSON formatting markers.\n\n"
            "Booking ID: (echo above)\n"
            "Created At: (echo above)\n"
            "Trip Type: flight|hotel|flight+hotel\n"
            "Region: (echo above)\n\n"
            "TRAVELER INFORMATION:\n"
            "Name: Fictional Name\n"
            "Email: fake@example.com\n\n"
            "FLIGHT DETAILS: (if applicable)\n"
            "From: IATA_CODE To: IATA_CODE\n"
            "Departure: ISO_8601_DATETIME\n"
            "Arrival: ISO_8601_DATETIME\n"
            "Airline: airline_name Flight: flight_code\n"
            "Fare: $amount USD\n\n"
            "HOTEL DETAILS: (if applicable)\n"
            "Hotel: hotel_name\n"
            "Check-in: ISO_8601_DATE\n"
            "Check-out: ISO_8601_DATE\n"
            "City: city_name\n"
            "Nightly Rate: $amount USD\n\n"
            "BOOKING SUMMARY:\n"
            "Total Cost: $amount USD\n"
            "Status: confirmed|pending|canceled\n"
            "Customer Rating: 1-5\n"
            "Comments: text (optional)\n"
        )

    # ------------------------------------------------------------------ #
    # Post-processing                                                    #
    # ------------------------------------------------------------------ #
    def post_process(self, raw: str, output_format: str) -> Any:  # noqa: ANN401
        """Deserialize based on output_format; fallback to raw string on failure."""
        fmt = output_format.lower()
        if fmt == "json" and raw.lstrip().startswith("{"):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                _logger.warning(
                    "Failed to parse JSON; returning raw string.", exc_info=True
                )
                return raw
        if fmt == "yaml" and ":" in raw and "\n" in raw:  # naive YAML sniff
            try:
                return yaml.safe_load(raw)
            except yaml.YAMLError:
                _logger.warning(
                    "Failed to parse YAML; returning raw string.", exc_info=True
                )
                return raw
        # plain-text or unrecognized format (handle both "text" and "txt")
        return raw

    # ------------------------------------------------------------------ #
    # Misc.                                                              #
    # ------------------------------------------------------------------ #
    def get_system_description(self) -> str:
        """Return a description of the travel booking system."""
        return f"Travel bookings ({self.trip_type}) in {self.region}"
