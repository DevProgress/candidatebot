# candidatebot

This project will help get basic candidate information that is programmatically retrieved and/or crowdsourced, added to wikipedia, and potentially other prominent sites online.

# What it does
It reads a data source with a bunch of information about a candidate, and makes a
wikipedia page for them if they don't already have one. It can currently read yaml
and the xml data dump from http://www.fec.gov/data/CandidateSummary.do

It uses the existing Officeholder infobox:
https://en.wikipedia.org/wiki/Template:Infobox_officeholder

# Prerequisites
A couple of python modules:

```
pip install pyyaml
pip install requests
```

and for testing, you need `python-pytest`. (http://doc.pytest.org)
Run `py.test` in the same directory as the tests to run them.


# If I run this will I write to wikipedia?
Nope, it's set up to point at my local wiki, http://cso.noidea.dog/w/. Also, you need a password.

# Is it ok to create pages automatically on wikipedia?
With prior approval. See https://en.wikipedia.org/wiki/Wikipedia:Bot_policy#Mass_page_creation
We haven't requested approval yet.

# What does the page look like?
Pretty rubbish so far, thanks for asking.

http://cso.noidea.dog/w/index.php/Person_Four
http://cso.noidea.dog/w/index.php/Some_Person

