"""Tests for voter participation PDF extraction."""

import textwrap

import pytest

from src.voter_participation_parser import (
    PDFConfig,
    VoterRecord,
    extract_voters_from_page,
    parse_voter_lines,
)


class TestVoterRecord:
    """Tests for VoterRecord dataclass."""

    def test_voter_record_creation(self) -> None:
        """Test creating a VoterRecord instance."""
        record = VoterRecord(
            ward_precinct="1-2",
            voter_id="12345",
            party="DEM",
            name="John Doe",
            history="2020-11-03 2022-11-08",
            address="123 Main St",
            status="ACTIVE",
            ballot_type="Regular",
        )
        assert record.ward_precinct == "1-2"
        assert record.voter_id == "12345"
        assert record.party == "DEM"

    def test_voter_record_immutable(self) -> None:
        """Test that VoterRecord is immutable (frozen)."""
        record = VoterRecord("1-2", "12345", "DEM", "John Doe", "history", "123 Main St", "ACTIVE", "Regular")
        with pytest.raises(AttributeError):
            record.voter_id = "54321"  # type: ignore[misc]


class TestParseVoterLines:
    """Tests for parse_voter_lines function."""

    def test_parse_valid_voter_lines(self) -> None:
        """Test parsing valid voter data."""
        lines = [
            "1-2 12345 John Doe 123 Main St ACTIVE",
            "2020-11-03 2022-11-08",
            "DEM Regular Ballot",
        ]
        record = parse_voter_lines(lines)
        assert record.ward_precinct == "1-2"
        assert record.voter_id == "12345"
        assert record.name == "John Doe"
        assert record.address == "123 Main St"
        assert record.status == "ACTIVE"
        assert record.history == "2020-11-03 2022-11-08"
        assert record.party == "DEM"
        assert record.ballot_type == "Regular Ballot"

    def test_parse_voter_with_multi_word_name(self) -> None:
        """Test parsing voter with multiple name parts."""
        lines = [
            "3-4 67890 Mary Jane Smith 456 Oak Ave INACTIVE",
            "2018-11-06",
            "REP Absentee Ballot",
        ]
        record = parse_voter_lines(lines)
        assert record.name == "Mary Jane Smith"
        assert record.address == "456 Oak Ave"

    def test_parse_invalid_format_raises_error(self) -> None:
        """Test that invalid format raises ValueError."""
        lines = [
            "invalid format",
            "2020-11-03",
            "DEM Regular",
        ]
        with pytest.raises(ValueError, match="Could not parse voter line"):
            parse_voter_lines(lines)

    def test_parse_insufficient_lines_raises_error(self) -> None:
        """Test that insufficient lines raises error."""
        lines = [
            "1-2 12345 John Doe 123 Main St ACTIVE",
            "2020-11-03",
        ]
        with pytest.raises(IndexError, match="list index out of range"):
            parse_voter_lines(lines)


class TestExtractVotersFromPage:
    """Tests for extract_voters_from_page function."""

    def test_extract_single_voter(self) -> None:
        """Test extracting a single voter from page text."""
        page_text = (
            textwrap.dedent("""
        Header Line 1
        Header Line 2
        Header Line 3
        Header Line 4
        Header Line 5
        Header Line 6
        1-2 12345 John Doe 123 Main St ACTIVE
        2020-11-03 2022-11-08
        DEM Regular Ballot
        Page 1 of 10
        """)
            .lstrip("\n")
            .rstrip()
        )

        voters = extract_voters_from_page(page_text)
        assert len(voters) == 1
        assert voters[0].voter_id == "12345"
        assert voters[0].name == "John Doe"

    def test_extract_multiple_voters(self) -> None:
        """Test extracting multiple voters from page text."""
        page_text = (
            textwrap.dedent("""
        Header Line 1
        Header Line 2
        Header Line 3
        Header Line 4
        Header Line 5
        Header Line 6
        1-2 12345 John Doe 123 Main St ACTIVE
        2020-11-03 2022-11-08
        DEM Regular Ballot
        3-4 67890 Jane Smith 456 Oak Ave INACTIVE
        2018-11-06
        REP Absentee Ballot
        Page 2 of 10
        """)
            .lstrip("\n")
            .rstrip()
        )

        voters = extract_voters_from_page(page_text)
        assert len(voters) == 2
        assert voters[0].voter_id == "12345"
        assert voters[1].voter_id == "67890"

    def test_extract_empty_page(self) -> None:
        """Test extracting from page with only headers/footers."""
        page_text = (
            textwrap.dedent("""
        Header Line 1
        Header Line 2
        Header Line 3
        Header Line 4
        Header Line 5
        Header Line 6
        Page 1 of 10
        """)
            .lstrip("\n")
            .rstrip()
        )

        voters = extract_voters_from_page(page_text)
        assert len(voters) == 0


class TestPDFConfig:
    """Tests for PDFConfig constants."""

    def test_config_values(self) -> None:
        """Test that config values are set correctly."""
        assert PDFConfig.LINES_PER_VOTER == 3
        assert PDFConfig.HEADER_LINES == 6
        assert PDFConfig.FOOTER_LINES == 1
        assert not PDFConfig.TEST_MODE
