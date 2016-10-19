# candidatebot

# Status
On hold. Wikipedia doesn't consider candidates for election to be automatically notable, and human-generated pages for candidates have been reverted; bot-created pages have low chance of survival. We could set up our own wiki, but the information is already available at Ballotopedia, Politics1, ActBlue, etc. This could be a data source for other projects; if a use case arises, we should repurpose this code to do whatever is needed.

# What it does
It reads data sources with information about candidates for election, saves them as CSV and optionally creates mediawiki (e.g., Wikipedia) stub pages for them using the https://en.wikipedia.org/wiki/Template:Infobox_officeholder infobox template.

It can currently read yaml, the xml data dump from http://www.fec.gov/data/CandidateSummary.do and some wikipedia pages, e.g., 
https://en.wikipedia.org/wiki/United_States_House_of_Representatives_elections,_2016


# Prerequisites

If you are running on a mac, make sure you have xcode command-line tools installed. You can install them using the command 'xcode-select --install'

A few python modules:

```
pip install pyyaml
pip install requests
pip install lxml
pip install beautifulsoup4
pip install us
```

and for testing, you need `python-pytest`. (http://doc.pytest.org)
Run `py.test` in the same directory as the tests to run them.


# If I run this will I write to wikipedia?
Nope, it's set up to point at a local wiki, http://cso.noidea.dog/w/. Create an account there, and add a file, credentials.py that looks like
USERNAME=youruser
PASS=yourpass


# What does the page look like?

http://cso.noidea.dog/w/index.php/User:Candidatebot/sandbox/Test_Page

We want to autogenerate as much information as possible, but humans will have to fill in the TODOs.
