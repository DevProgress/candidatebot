#!/usr/bin/python2.7

"""This script reads a list of candidates from various data sources and makes
sure that they each have a wikipedia page, creating it if necessary"""

import csv
import getpass
import sys

import candidate
import credentials
import mediawiki

#BASEURL = "https://test.wikipedia.org/w/"
#BASEURL = "https://en.wikipedia.org/w/"
BASEURL = "http://cso.noidea.dog/w/"
# Prepend all created pages with this
DRAFT_PREFIX = "User:Candidatebot/sandbox/"
YAML_FILE = "candidates.yaml"
XML_FILE = "CandidateSummaryAction.xml"
HOUSE_FILE = "house.html"
GOVERNOR_FILE = "governor.html"
# Limit what this does during testing.
MAX_PAGES_TO_CREATE = 0



def main():
  """Gets a bunch of candidate information and tries to create pages for it."""

  if not credentials.USERNAME:
    print ("Please specify a user name in the variable USERNAME in a "
           "credentials.py file in the root directory")
    sys.exit(1)
  if not credentials.PASS:
    password = getpass.getpass("Password for wikipedia account %s: "
                               % credentials.USERNAME)
  else:
    password = credentials.PASS

  try:
    wiki = mediawiki.Wiki(BASEURL, credentials.USERNAME, password,
                          draft_prefix=DRAFT_PREFIX)
  except mediawiki.WikiException, ex:
    print "Error: %s" % ex
    sys.exit(1)

  created = 0


  csvfile = open('candidates.csv', 'wb')
  writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
  writer.writerow(candidate.Candidate.ordered_fields())

  files = [ # (HOUSE_FILE, "house"),
            (GOVERNOR_FILE, "governor")]

  print "Creating no more than %s wiki pages." % MAX_PAGES_TO_CREATE
  for filename, office in files:
    print "### %s" % filename
    #for person in candidate.new_from_fec_xml(XML_FILE):
    #for person in candidate.new_from_yaml(YAML_FILE):
    for person in candidate.new_from_wikipedia_page(filename, office):
      writer.writerow(person.as_list())
      if created == MAX_PAGES_TO_CREATE:
        continue
      # Check if a live page exists.
      existing_page = wiki.does_page_exist(person.name())
      if existing_page:
        print "Page already exists at %s" % existing_page
        continue
      # Check for an existing draft page.
      existing_draft = wiki.does_draft_exist(person.name())
      if existing_draft:
        print "Draft already exists at %s" % existing_draft
        continue
      print "Creating wikipedia page for %s (for %s)" % (
        person.name(), person.office_and_district())
      new_page = wiki.create_page(person, create_draft=True)
      if new_page:
        print "Created %s" % new_page
        created += 1
      else:
        print "Failed to create a page for %s" % person.name()
      continue

main()
