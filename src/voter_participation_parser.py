"""Extract voter participation info from a City of Portland-provided PDF into a CSV format."""

import logging
import re

import pandas as pd
import pypdfium2 as pdfium

TESTMODE = False
LINESPERVOTER = 3
HEADERLINES = 6
FOOTERLINES = 1

logger = logging.getLogger(__name__)


def voter(lines: list) -> list:
    """Extract voter data from pdf data group."""
    ward, voterid, votername, address, status = re.findall(r"^(\d+-\d+) (\d+) (.*?) (\d.*?) ([A-Z]+)$", lines[0])[0]
    history = lines[1]
    party, ballot = lines[2].split(" ")
    return [ward, voterid, party, votername, history, address, status, ballot]


def voters(pagetext: str) -> list:
    """Iterate through voters from provided page."""
    page = []
    lines = pagetext.splitlines()
    pagenumber = int(re.findall(r"Page (\d+) of", lines[-1])[0])
    num_voters = (len(lines) - HEADERLINES - FOOTERLINES) // LINESPERVOTER
    logger.info("Found %s voters on page %s", num_voters, pagenumber)
    for n in range(HEADERLINES, len(lines) - (FOOTERLINES + 1), LINESPERVOTER):
        logger.info("Iterating over voter %s", ((n - HEADERLINES) // 3) + 1)
        page.append(voter(lines[n : n + LINESPERVOTER]))
    return page


def read_voters_pages() -> list:
    """Read PDF into pages and iterate over them as text strings."""
    all_voters = []
    pdf = pdfium.PdfDocument("./Voter Participation History.pdf")
    logger.info("Found %s pages in PDF", len(pdf))
    for n in range(1, len(pdf)):  # skip title page
        all_voters.extend(voters(pdf[n].get_textpage().get_text_range()))
        if TESTMODE:
            break
    return all_voters


def main() -> None:
    """Extract voter participation info from a City of Portland-provided PDF into a CSV format."""
    df = pd.DataFrame(
        data=read_voters_pages(),
        columns=[
            "Ward/Precinct",
            "Voter Record #",
            "Party",
            "Voter Name",
            "History",
            "Residence Address",
            "Status",
            "Ballot Type",
        ],
    )
    df.set_index(["Voter Record #"], inplace=True)
    df.to_csv(r"./Voter Participation History.csv", encoding="utf-8", index=False)


if __name__ == "__main__":
    main()
