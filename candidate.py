"""Information about a candidate, including what fields are valid for
Wikipedia's Officeholder onebox.
"""

import re
import us
import yaml

from bs4 import BeautifulSoup
from lxml import etree


def check_field(field):
  """Checks if a field is valid.

  Args:
    field: (string) A field name.
  Returns:
    (bool) Whether that's in the list of valid fields.
  """
  valid_fields = [  # this is not complete
    "honorific-prefix",
    "name",
    "honorific-suffix",
    "image",
    "alt",
    "state_assembly",
    "district",
    "term_start",
    "term_end",
    "predecessor",
    "successor",
    "speaker",
    "term_start2",
    "term_end2",
    "predecessor2",
    "successor2",
    "birth_date",
    "birth_place",
    "death_date",
    "death_place",
    "nationality",
    "office",
    "spouse",
    "party",
    "relations",
    "children",
    "residence",
    "alma_mater",
    "occupation",
    "profession",
    "religion",
    "signature",
    "signature_alt",
    "state",
    "website",
    "footnotes ",
  ]

  return field in valid_fields


def normalize_field(field):
  """Translate a name from the fec xml file to what wikipedia calls it.

  Args:
    field: (string) A tag from the fec.gov file, e.g., can_par_aff
  Returns:
    (string): A field name on wikipedia, e.g., party
  """
  translation = {
    "can_nam": "name",
    "can_off": "office",   # office sought, e.g., President, House, Senate
    "can_off_sta": "state",   # office state
    "can_off_dis": "district",   # office district
    "can_par_aff": "party", #party affiliation
  }
  try:
    translated = translation[field]
  except KeyError:
    return field
  return translated

def normalize_office(field):
  """Translate office names from the fec xml file to human readable.

  Args:
    field: (string) A tag from the fec.gov file, e.g., can_par_aff
  Returns:
    (string): An office, e.g., "house"
  """
  offices = {"P": "president", "H": "house", "S": "senate"}
  try:
    translated = offices[field]
  except KeyError:
    return field
  return translated


def normalize_name(name):
  """Translates a name to wikipedia's format.

  Args:
    name: (string) A name in "SURNAME, FIRSTNAME" all-uppercase format.
  Returns:
    (string): A name in "Firstname Surname" format.
  """
  if not name:
    return ""
  punctuations = [".", ","]
  for punctuation in punctuations:
    if name.endswith(punctuation):
      name = name[:-1]

  honorifics = ["mr", "mrs", "dr", "md"]
  for honorific in honorifics:
    if name.lower().endswith(honorific):
      name = name[:-len(honorific)].strip()

  suffixes = [  # ordered list so we test iii before ii. So lazy.
    ("iii", "III"),
    ("ii", "II"),
    ("iv", "IV"),
    ("jr", "Jr"),
    ("sr", "Sr"),
    ("esq", "Esq")
  ]
  to_be_added = []
  for suffix in suffixes:
    if name.lower().endswith(suffix[0]):
      to_be_added.append(suffix[1])
      name = name[:-len(suffix[0])].strip()

  parts = name.split(",")
  new = " ".join(parts[1:])
  new += " %s" % parts[0]

  normalized = new.strip().lower().title()
  for suffix in to_be_added:
    normalized += " %s" % suffix
  return normalized

def normalize_district(district):
  """Translate a district into an ordinal and state.
  Args:
    district: (str) a string like "Alabama 1" or "14"
  returns:
    (str, str): a state and ordinal district, e.g., ("Alabama", "1st")
  """
  if not district:
    return (None, None)
  state = None
  match = re.search(r"^(\d+)$", district)
  if match is not None:
    # The district is just a number
    number = match.group(1).lstrip('0') or "0"
  else:
    # Let's see if it's a state and a number
    district_re = r"^(.*)\W+(\d+|at-large)$"
    match = re.search(district_re, district)
    number = ""
    state = ""
    if match is not None:
      state = match.group(1)
      number = match.group(2)
    else:
      print "Error: [%s] didn't match [%s]" % (district_re, district)
      return (None, None)

  if number == "at-large":
    suffix = ""
  elif re.match("^1.$", number):
    suffix = "th"
  elif number[-1] == "1":
    suffix = "st"
  elif number[-1] == "2":
    suffix = "nd"
  elif number[-1] == "3":
    suffix = "rd"
  else:
    suffix = "th"
  return (state, number + suffix)

def normalize_state(state):
  """Translate a two letter state name into a full state name
  Args:
    state: (str) a string like "CA" or "California"
  returns:
    (str): a state name like "California"
  """
  if not state:
    return None
  if len(state) != 2:
    return state
  full = us.states.lookup(state)
  if full:
    return full.name
  return state

def new_from_yaml(filename):
  """ Read a yaml file, yield Candidates.

  Args:
    filename (string): a file with one or more candidates
  Yields:
    Candidates
  """
  with open(filename) as stream:
    try:
      contents = yaml.load(stream)
    except yaml.YAMLError as ex:
      print ex

  for element in contents:
    if not element["name"]:
      print "No name. Skipping."
      continue

    candidate = Candidate(element["name"], element)

    yield candidate


def new_from_fec_xml(filename):
  """Read an XML file downloaded from fec.gov, yield Candidates.

  http://www.fec.gov/data/CandidateSummary.do has a list of candidates.

  Args:
    filename (string): a file with one or more candidates
  Yields:
    (Candidate): candidates.
"""
  tree = etree.iterparse(filename)

  for _, elem in tree:
    if not elem.getchildren():
      continue
    data = {}
    for datum in elem.getchildren():
      data[datum.tag] = datum.text

    try:
      party = data["can_par_aff"]
      office = data["can_off"]
    except KeyError:
      continue
    # Reduce the noise from this very, very noisy dataset.
    if party != "DEM":
      continue
    if office == "P":
      continue

    try:
      candidate = make_candidate(data)
    except CandidateException, ex:
      print "Didn't create a candidate: %s" % ex
      continue
    yield candidate


def new_from_wikipedia_page(filename):
  """Read wikipedia's House Elections page and parse a list of candidates.

    File downloaded from
    https://en.wikipedia.org/wiki/United_States_House_of_Representatives_elections,_2016

    Args:
      filename (string): a file with one or more candidates
    Yields:
      (Candidate): candidates.
  """

  html = open(filename, 'r').read()

  other_parties = ["Green", "Independent", "Libertarian", "NPP", "PDP", "PIP",
                   "PPT", "R", "Reform", "Republican", "No Party Preference"]
  soup = BeautifulSoup(html, 'html.parser')
  tables = soup.findAll("table", {"class": "wikitable sortable"})

  for table in tables:  # each state/territory
    for row in table.findAll("tr"):  # each district
      headers = row.findAll("th")    # district name
      columns = row.findAll("td")    # election information
      if len(headers) != 1 or len(columns) != 6:
        # Not a table in the format we expect. That's fine; there'll be other
        # stuff on the page.
        continue
      district = headers[0].text
      incumbent = columns[1].text
      candidates = columns[5]
      if candidates is None:
        print "Error: Unexpectedly empty candidates column for [%s]." % row
        continue
      lines = candidates.text.split("\n")
      tags = candidates.findAll()

      page = ""
      reference = ""
      for line in lines:
        # Skip empty lines.
        if len(line) == 0:
          continue
        # Skip non-democrats, though warn if we can't see a party; this will
        # help catch things in formats we don't expect.
        if not "(Democrat" in line or "(D)" in line:
          found = False
          for party in other_parties:
            if "(%s)" % party in line:
              found = True
              break
          if not found:
            print "Warning: [%s] has an unknown party." % line
          continue

        # Ok, we have a democratic candidate. Pull out the name and the
        # wikipedia reference, then look for an <a href" link to an existing
        # wikipedia page. The line will look like
        # Firstname Lastname (Democrat)[reference]
        name = line.split("(")[0].strip()
        #TODO: Parse the references and collect this url. We could also get
        # this from the <sup> tag.
        reference = line.split(")")[1].strip()
        for i in range(0, len(tags)):
          if tags[i].name == 'a' and tags[i].text == name:
            page = tags[i]
        if page:  # The candidate already has a page. We're not needed here.
          continue
        else:
          data = {}
          data["name"] = name
          data["district"] = district
          data["incumbent"] = incumbent
          data["reference"] = reference
          data["party"] = "Democratic"
          data["office"] = "house"
          try:
            candidate = make_candidate(data)
          except CandidateException, ex:
            print "Skipping %s: %s" % (name, ex)
            continue
          yield candidate


class CandidateException(Exception):
  """Failed to create a candidate for some reasonable reason."""
  pass

def make_candidate(noisy_data):
  """Turn a dictionary of potentially noisy candidate data into a Candidate.

  Only returns candidates who match a bunch of rules:
    * has a name
    * is listed as a democrat
    * is running for a specific office
    * isn't running for president

  Args:
    data: ({str:str, ...}) A dictionary of candidate data, indexed by type
  Returns:
    (Candidate): a populated Candidate object
  """
  data = {}

  for tag in noisy_data:
    translated = normalize_field(tag)
    text = noisy_data[tag]

    if translated == "office":
      text = normalize_office(text)
    data[translated] = text

  try:
    name = normalize_name(data["name"])
    data["name"] = name
    office = data["office"]
  except KeyError, ex:
    raise CandidateException("missing expected fields: %s" % ex)


  if office == "house":
    try:
      district = data["district"]
    except KeyError:
      raise CandidateException("missing expected field: district")

    state, ordinal = normalize_district(district)
    if state:
      data['state'] = state

    if ordinal:
      data['district'] = ordinal
    else:
      raise CandidateException("couldn't parse district: %s")

  try:
    state = normalize_state(data["state"])
    data["state"] = state
  except KeyError:
    raise CandidateException("missing expected field: state")

  return Candidate(name, data)


class Candidate(object):
  """Name and a bunch of key/value pairs for a single candidate."""
  def __init__(self, name, data):
    self._name = name
    self._data = data

  def wikipedia_content(self):
    """Create a wikipedia-formatted string of candidate information."""
    infostr = "{{Infobox Officeholder\n"
    for k in self._data:
      if not check_field(k):
        # silently skip fields we don't know how to deal with.
        continue
      infostr += "| %s = %s\n" % (k, self._data[k])

    infostr += ("\n}}\n'''%s''' is a 2016 Democratic candidate seeking "
                "election to the %s.\n {{US-politician-stub}}" % (
                self.name(), self.office_and_district()))

    reference = self.reference()
    if reference:
      infostr += "<ref>%s</ref>" % reference

    return infostr

  def name(self):
    """Return the candidate's name."""
    return self._name

  def office_and_district(self):
    """Return the candidate's office."""
    office = self._data["office"]
    if office == "house":
      try:
        district = self._data["district"]
        state = self._data["state"]
      except KeyError:
        return "the US House of Representatives"
      if district == "at-large":
        return ("the US House of Representatives to represent the %s at-large "
                "district" % state)
      else:
        return ("the US House of Representatives to represent the %s district "
                "of %s" % (district, state))
    elif office == "senate":
      try:
        state = self._data["state"]
      except KeyError:
        return "the US Senate"
      return "the US Senate for %s" % state
    else:
      return office

  def data(self):
    """Return all of the candidate's data. For testing."""
    return self._data

  def reference(self):
    """Return wikipedia reference."""
    try:
      return self._data["reference"]
    except KeyError:
      return None
