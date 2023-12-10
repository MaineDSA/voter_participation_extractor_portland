[![Pylint](https://github.com/MaineDSA/PortlandVoterParticipationParser/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/MaineDSA/PortlandVoterParticipationParser/actions/workflows/pylint.yml)

# PortlandVoterParticipationParser
The City of Portland distributes voter participation info in PDF format. This makes it a CSV.

## Prerequisites

To run this code, you'll need to have Python 3.9, 3.10, 3.11, or 3.12 installed on your machine. You'll also need to install the required packages by running the following command from inside the project folder:

```shell
python3 -m pip install -r requirements.txt
```

## Usage

1. Clone the repository and navigate to the project folder.
2. Add the city-provided PDF of voter participation data to the folder as a file titled "Voter Participation History.pdf".
2. Open a terminal and run the following command to extract data:

```shell
python3 -m voter_participation_parser
```

3. Unless there is a problem, you output will be saved as "Voter Participation History.csv".
