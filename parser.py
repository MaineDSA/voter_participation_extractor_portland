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
	ward = re.findall('^(\d+\-\d+) ', lines[0])[0]
	voterid = re.findall(f'{re.escape(ward)} (.+?) ', lines[0])[0]
	party = re.findall(f'^([A-Z]+) [A-Z]+$', lines[2])[0]
	votername = re.findall(f'{re.escape(voterid)} (.+?) \d', lines[0])[0]
	history = lines[1]
	address = re.findall(f'{re.escape(votername)} (.+?) [A-Z]+$', lines[0])[0]
	status = re.findall(f'{re.escape(address)} ([A-Z]+)$', lines[0])[0]
	ballot = re.findall(f'{re.escape(party)} ([A-Z]+)$', lines[2])[0]
	output.append([ward, voterid, party, votername, history, address, status, ballot])

# Iterate through voters.
def voters(pagetext:str):
	lines = pagetext.splitlines()
	pagenumber = int(re.findall('Page (\d+) of', lines[len(lines)-1])[0])
	print(f'Found {int((len(lines)-HEADERLINES-FOOTERLINES)/LINESPERVOTER)} voters on page {pagenumber}')
	for n in range(HEADERLINES,len(lines)-(FOOTERLINES+1), LINESPERVOTER):
		print(f'Iterating over voter {int((n-HEADERLINES)/3)+1}')
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

if TESTMODE:
	print(df)

df.to_csv(r'./Voter Participation History.csv', encoding='utf-8', index=False)
