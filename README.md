# candidatebot

This project will help get basic candidate information that is programmatically retrieved and/or crowdsourced, added to wikipedia, and potentially other prominent sites online.

# What it does
It reads data sources with information about candidates for election, and
checks whether they have wikipedia pages. If not, it makes draft pages for
them with placeholder information. It adds all created pages to a list so
volunteers can fill in the gaps before sending the page for review.

It can currently read yaml, the xml data dump from http://www.fec.gov/data/CandidateSummary.do and https://en.wikipedia.org/wiki/United_States_House_of_Representatives_elections,_2016

It uses the existing Officeholder infobox:
https://en.wikipedia.org/wiki/Template:Infobox_officeholder

# Prerequisites

If you are running on a mac, make sure you have xcode command-line tools installed. You can install them using the command 'xcode-select --install'

A couple of python modules:

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
