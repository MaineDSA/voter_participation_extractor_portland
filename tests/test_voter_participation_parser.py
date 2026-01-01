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

    @pytest.mark.parametrize(
        ("voter_line", "expected_name"),
        [
            ("3-4 67890 Mary Jane Smith 456 Oak Ave INACTIVE", "Mary Jane Smith"),
            ("1-2 12345 John Doe 123 Main St ACTIVE", "John Doe"),
            ("5-6 11111 Bob 789 Pine St ACTIVE", "Bob"),
            ("7-8 22222 Maria Garcia Lopez 321 Elm Dr ACTIVE", "Maria Garcia Lopez"),
            ("9-10 33333 Jean-Pierre O'Connor 555 Maple Ln INACTIVE", "Jean-Pierre O'Connor"),
            ("2-3 44444 Dr. Sarah Johnson PhD 999 Cedar Rd ACTIVE", "Dr. Sarah Johnson PhD"),
            ("4-5 55555 Mary-Ann Smith-Jones 111 Birch Ct ACTIVE", "Mary-Ann Smith-Jones"),
            ("6-7 66666 José María Fernández 222 Spruce Way INACTIVE", "José María Fernández"),
            ('8-9 77777 Robert "Bob" Williams 333 Willow St ACTIVE', 'Robert "Bob" Williams'),
            ("1-1 88888 St. John van der Berg III 444 Ash Ave ACTIVE", "St. John van der Berg III"),
        ],
    )
    def test_parse_various_name_formats(self, voter_line: str, expected_name: str) -> None:
        """Test parsing voters with various name formats."""
        lines = [
            voter_line,
            "2020-11-03 2022-11-08",
            "DEM Regular Ballot",
        ]
        record = parse_voter_lines(lines)
        assert record.name == expected_name

    @pytest.mark.parametrize(
        ("voter_line", "expected_address"),
        [
            ("1-2 12345 John Doe 123 Main St ACTIVE", "123 Main St"),
            ("3-4 67890 Jane Smith 456 Oak Ave Apt 2B INACTIVE", "456 Oak Ave Apt 2B"),
            ("5-6 11111 Bob Jones 789 Pine St Unit 10 ACTIVE", "789 Pine St Unit 10"),
            ("7-8 22222 Mary Lee 321 Elm Dr #305 ACTIVE", "321 Elm Dr #305"),
            ("9-10 33333 Tom Brown 555 Maple Ln Bldg C INACTIVE", "555 Maple Ln Bldg C"),
            ("2-3 44444 Sarah Davis 999 Cedar Rd Suite 100 ACTIVE", "999 Cedar Rd Suite 100"),
        ],
    )
    def test_parse_various_address_formats(self, voter_line: str, expected_address: str) -> None:
        """Test parsing voters with various address formats."""
        lines = [
            voter_line,
            "2020-11-03",
            "REP Absentee Ballot",
        ]
        record = parse_voter_lines(lines)
        assert record.address == expected_address

    @pytest.mark.parametrize(
        ("party_ballot_line", "expected_party", "expected_ballot"),
        [
            ("DEM Regular Ballot", "DEM", "Regular Ballot"),
            ("REP Absentee Ballot", "REP", "Absentee Ballot"),
            ("IND Early Voting", "IND", "Early Voting"),
            ("GRN Mail-In Ballot", "GRN", "Mail-In Ballot"),
            ("LIB Provisional", "LIB", "Provisional"),
            ("UNA Regular", "UNA", "Regular"),
        ],
    )
    def test_parse_various_party_ballot_combinations(self, party_ballot_line: str, expected_party: str, expected_ballot: str) -> None:
        """Test parsing various party and ballot type combinations."""
        lines = [
            "1-2 12345 John Doe 123 Main St ACTIVE",
            "2020-11-03",
            party_ballot_line,
        ]
        record = parse_voter_lines(lines)
        assert record.party == expected_party
        assert record.ballot_type == expected_ballot

    @pytest.mark.parametrize(
        "history_line",
        [
            "2020-11-03 2022-11-08",
            "2018-11-06",
            "2016-11-08 2018-11-06 2020-11-03 2022-11-08",
            "2022-11-08 2024-11-05",
            "",
        ],
    )
    def test_parse_various_voting_histories(self, history_line: str) -> None:
        """Test parsing various voting history formats."""
        lines = [
            "1-2 12345 John Doe 123 Main St ACTIVE",
            history_line,
            "DEM Regular Ballot",
        ]
        record = parse_voter_lines(lines)
        assert record.history == history_line

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
