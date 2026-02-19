from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from src.voter_participation_parser import (
    VoterRecord,
    extract_voters_from_page,
    parse_voter_lines,
    save_voters_to_csv,
)


@pytest.fixture
def sample_voter() -> VoterRecord:
    """Provide a standard VoterRecord for testing."""
    return VoterRecord(
        ward_precinct="1-2", voter_id="12345", party="DEM", name="John Doe", history="2020-11-03", address="123 Main St", status="ACTIVE", ballot_type="Regular"
    )


@pytest.fixture
def mock_page_text() -> Callable[[int], str]:
    """Generate mock PDF page text with variable voter counts."""

    def _generate(num_voters: int = 1) -> str:
        header = "\n".join([f"Header Line {i}" for i in range(1, 7)])
        voter_block = "1-2 12345 John Doe 123 Main St ACTIVE\n2020-11-03\nDEM Regular Ballot"
        body = "\n".join([voter_block] * num_voters)
        footer = "Page 1 of 1"
        return f"{header}\n{body}\n{footer}" if num_voters > 0 else f"{header}\n{footer}"

    return _generate


class TestVoterRecord:
    """Test structure of VoterRecord object."""

    def test_voter_record_properties(self, sample_voter: VoterRecord) -> None:
        assert sample_voter.voter_id == "12345"

    def test_voter_record_immutable(self, sample_voter: VoterRecord) -> None:
        with pytest.raises(AttributeError):
            sample_voter.voter_id = "54321"  # type: ignore[misc]


class TestParseVoterLines:
    """Test behavior of parsing voter information from string components."""

    @pytest.mark.parametrize(
        ("line_0", "line_2", "expected_attr", "expected_val"),
        [
            # Name Variations
            ("1-1 888 St. John III 44 Ash ACTIVE", "DEM Reg", "name", "St. John III"),
            ('8-9 777 Robert "Bob" W 33 Willow ACTIVE', "DEM Reg", "name", 'Robert "Bob" W'),
            ("6-7 666 José María Fernández 222 Spruce INACTIVE", "DEM Reg", "name", "José María Fernández"),
            # Address Variations
            ("1-2 123 J Doe 456 Oak Ave Apt 2B ACTIVE", "REP Abs", "address", "456 Oak Ave Apt 2B"),
            ("7-8 222 M Lee 321 Elm Dr #305 ACTIVE", "REP Abs", "address", "321 Elm Dr #305"),
            # Party/Ballot Variations
            ("1-1 111 B Jones 10 Main ACTIVE", "IND Early Voting", "party", "IND"),
            ("1-1 111 B Jones 10 Main ACTIVE", "IND Early Voting", "ballot_type", "Early Voting"),
        ],
    )
    def test_parsing_logic(self, line_0: str, line_2: str, expected_attr: str, expected_val: str) -> None:
        """Consolidates name, address, party, and ballot testing into a single parameterized test."""
        lines = [line_0, "2020-11-01", line_2]
        record = parse_voter_lines(lines)
        assert getattr(record, expected_attr) == expected_val


class TestExtractVotersFromPage:
    """Test behavior of extracting voter information from an entire page."""

    @pytest.mark.parametrize("voter_count", [0, 1, 5])
    def test_extract_voters_count(self, voter_count: int, mock_page_text: Callable[[int], str]) -> None:
        """Verifies extraction works for empty, single, and multiple records per page."""
        text = mock_page_text(voter_count)
        voters = extract_voters_from_page(text)
        assert len(voters) == voter_count


class TestSaveVotersToCSV:
    """Test behavior of saving voter information into CSV file."""

    def test_save_voters_logic(self, tmp_path: Path, sample_voter: VoterRecord) -> None:
        """Verifies file creation logic, including the 'no file for empty list' requirement."""
        output_file = tmp_path / "test.csv"

        save_voters_to_csv([], output_file)
        assert not output_file.exists()

        save_voters_to_csv([sample_voter], output_file)
        assert output_file.exists()

        df = pd.read_csv(output_file)
        assert len(df) == 1
        assert df.iloc[0]["Voter Name"] == "John Doe"
        assert df.iloc[0]["Ward/Precinct"] == "1-2"
