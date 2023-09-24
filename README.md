# PortlandVoterParticipationParser
The City of Portland distributes voter participation info in PDF format. This makes it a CSV.

## Dependencies
* **pypdfium2**: Install with ```python3 -m pip install pypdfium2```
* **pandas**: Install with ```python3 -m pip install pandas```

## Instructions
1. Put [parser.py](https://github.com/MaineDSA/PortlandVoterParticipationParser/blob/main/parser.py) in a folder with a PDF of the correct format titled "Voter Participation History.pdf".
2. Run the parser with ```python3 parser.py```.
3. Unless there is a problem, you output will be saved as "Voter Participation History.csv".
