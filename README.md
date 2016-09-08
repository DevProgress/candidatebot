# candidatebot

This project will help get basic candidate information that is programmatically retrieved and/or crowdsourced, added to wikipedia, and potentially other prominent sites online.

# What it does
It reads a yaml file with a bunch of information about a candidate, and makes a
wikipedia page for them if they don't already have one.

It uses the existing Officeholder infobox:
https://en.wikipedia.org/wiki/Template:Infobox_officeholder

# Prerequisites
A couple of python modules:

```
pip install pyyaml
pip install requests
```

# If I run this will I write to wikipedia?
Nope, it's set up to point at my local wiki, http://cso.noidea.dog/w/. Also, you need a password.

# What does the page look like?
Pretty rubbish so far, thanks for asking.

http://cso.noidea.dog/w/index.php/Person_Four
http://cso.noidea.dog/w/index.php/Some_Person

