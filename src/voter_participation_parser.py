"""Extract voter participation info from a City of Portland-provided PDF into a CSV format."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pypdfium2 as pdfium

logging.basicConfig(level=logging.INFO, format="%(levelname)s : voter_participation_extractor_portland:%(name)s : %(message)s")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VoterRecord:
    """Structured voter record data."""

    ward_precinct: str
    voter_id: str
    party: str
    name: str
    history: str
    address: str
    status: str
    ballot_type: str


class PDFConfig:
    """PDF parsing configuration."""

    LINES_PER_VOTER = 3
    HEADER_LINES = 6
    FOOTER_LINES = 1
    TEST_MODE = False


def parse_voter_lines(lines: list[str]) -> VoterRecord:
    """
    Parse three lines of voter data into a structured record.

    Args:
    lines: List of three strings containing voter info

    Returns:
    VoterRecord with parsed data

    Raises:
    ValueError: If lines don't match expected format

    """
    try:
        match = re.search(r"^(\d+-\d+) (\d+) (.*?) (\d.*?) ([A-Z]+)$", lines[0])
        if not match:
            msg = f"Could not parse voter line: {lines[0]}"
            raise ValueError(msg)

        ward, voter_id, name, address, status = match.groups()
        history = lines[1]
        party, ballot = lines[2].split(" ", maxsplit=1)

        return VoterRecord(ward, voter_id, party, name, history, address, status, ballot)
    except (IndexError, ValueError) as e:
        logger.error("Error parsing voter lines: %s", e)
        raise


def extract_voters_from_page(page_text: str) -> list[VoterRecord]:
    """
    Extract all voter records from a single page.

    Args:
    page_text: Raw text content of the PDF page

    Returns:
    List of VoterRecord objects

    """
    lines = page_text.splitlines()

    # Extract and log page number
    page_number = int(page_match.group(1)) if (page_match := re.search(r"Page (\d+) of", lines[-1])) else "unknown"

    # Calculate number of voters on page
    content_lines = len(lines) - PDFConfig.HEADER_LINES - PDFConfig.FOOTER_LINES
    num_voters = content_lines // PDFConfig.LINES_PER_VOTER
    logger.info("Page %s contains %s voters", page_number, num_voters)

    # Extract voter records
    voters = []
    start_idx = PDFConfig.HEADER_LINES
    end_idx = len(lines) - PDFConfig.FOOTER_LINES

    for i in range(start_idx, end_idx, PDFConfig.LINES_PER_VOTER):
        voter_num = ((i - PDFConfig.HEADER_LINES) // PDFConfig.LINES_PER_VOTER) + 1
        logger.debug("Processing voter %s", voter_num)

        voter_lines = lines[i : i + PDFConfig.LINES_PER_VOTER]
        if len(voter_lines) == PDFConfig.LINES_PER_VOTER:
            voters.append(parse_voter_lines(voter_lines))

    return voters


def read_pdf_voters(pdf_path: Path) -> list[VoterRecord]:
    """
    Read all voter records from the PDF file.

    Args:
    pdf_path: Path to the PDF file

    Returns:
    List of all VoterRecord objects from the PDF

    """
    all_voters = []

    with pdfium.PdfDocument(pdf_path) as pdf:
        logger.info("Processing PDF with %s pages", len(pdf))

        # Skip title page (page 0)
        pages_to_process = range(1, 2 if PDFConfig.TEST_MODE else len(pdf))

        for page_num in pages_to_process:
            page_text = pdf[page_num].get_textpage().get_text_range()
            all_voters.extend(extract_voters_from_page(page_text))

    return all_voters


def save_voters_to_csv(voters: list[VoterRecord], output_path: Path) -> None:
    """
    Save voter records to a CSV file.

    Args:
    voters: List of VoterRecord objects
    output_path: Path for the output CSV file

    """
    if not voters:
        logger.warning("No voter records found. Skipping CSV creation.")
        return

    df = pd.DataFrame([vars(v) for v in voters])

    # Rename columns for clarity
    df.columns = [
        "Ward/Precinct",
        "Voter Record #",
        "Party",
        "Voter Name",
        "History",
        "Residence Address",
        "Status",
        "Ballot Type",
    ]

    df.to_csv(output_path, encoding="utf-8", index=False)
    logger.info("Saved %s voter records to %s", len(voters), output_path)


def main() -> None:
    """Extract voter participation info from PDF and save to CSV."""
    pdf_path = Path("./Voter Participation History.pdf")
    csv_path = Path("./Voter Participation History.csv")

    voters = read_pdf_voters(pdf_path)
    save_voters_to_csv(voters, csv_path)


if __name__ == "__main__":
    main()
