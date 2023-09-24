import pypdfium2 as pdfium
import pandas as pd
import re

output = []
TESTMODE = False
LINESPERVOTER = 3
HEADERLINES = 6
FOOTERLINES = 1

# Extract data from group
def voter(lines:list):
	ward, voterid, votername, address, status = re.findall('^(\d+\-\d+) (\d+) (.*?) (\d.*?) ([A-Z]+)$', lines[0])[0]
	history = lines[1]
	party, ballot = re.findall('^([A-Z]+) ([A-Z]+)$', lines[2])[0]
	output.append([ward, voterid, party, votername, history, address, status, ballot])

# Iterate through voters.
def voters(pagetext:str):
    lines = pagetext.splitlines()
    pagenumber = int(re.findall('Page (\d+) of', lines[-1])[0])
    num_voters = (len(lines) - HEADERLINES - FOOTERLINES) // LINESPERVOTER
    print(f'Found {num_voters} voters on page {pagenumber}')
    for n in range(HEADERLINES, len(lines) - (FOOTERLINES + 1), LINESPERVOTER):
        print(f'Iterating over voter {((n - HEADERLINES) // 3) + 1}')
        voter([lines[n], lines[n+1], lines[n+2]])

# Read PDF into pages and iterate over them as text strings.
def read_voters_pages():
	pdf = pdfium.PdfDocument("./Voter Participation History.pdf")
	print(f'Found {int(len(pdf))} pages in PDF')
	for n in range(1,len(pdf)): # skip title page
		voters(pdf[n].get_textpage().get_text_range())
		if TESTMODE:
			break

read_voters_pages()
df = pd.DataFrame(
		data=output,
		columns=[
			'Ward/Precinct',
			'Voter Record #',
			'Party',
			'Voter Name',
			'History',
			'Residence Address',
			'Status',
			'Ballot Type'
			]
		)
df = df.set_index(['Voter Record #'])
df.to_csv(r'./Voter Participation History.csv', encoding='utf-8', index=False)
