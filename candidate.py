"""Information about a candidate, including what fields are valid for
Wikipedia's Officeholder onebox.
"""

import re
import string
import us
import yaml

from bs4 import BeautifulSoup
from lxml import etree


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

def normalize_location(state, district):
  """Translate districts and state abbreviations into a district and state.

  Depending on the data source, the state name might be part of the district
  arg or abbreviated in the state arg. Calls are expected to look like:
    normalize_location("", "Alabama 1") or
    normalize_location("CA", "3") or
    normalize_location("FL", "")

  Args:
    state: (str) a state name or abbreviation or the empty string
    district: (str) a string like "Alabama 1" or "14" or the empty string.
  returns:
    (str, str): a state and ordinal district, e.g., ("Alabama", "1st")
  """
  number = ""
  suffix = ""
  unverified_state = state

  # District first
  match = re.search(r"^(\d+)$", district)
  if match is not None:
    # The district is just a number
    number = match.group(1).lstrip('0') or "0"
  else:
    # Let's see if it's a state and a number
    district_re = r"^(.*)\W+(\d+|at-large)$"
    match = re.search(district_re, district)
    if match is not None:
      unverified_state = match.group(1)
      number = match.group(2)

  if number:
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

  normalized_district = number + suffix

  # Check it's a valid state.
  normalized_state = ""
  full = us.states.lookup(unicode(unverified_state))
  if full:
    normalized_state = full.name
  # https://github.com/unitedstates/python-us/issues/13. We can't guarantee that
  # everyone will have jellyfish 0.5.3 or greater, so... hackorama.
  elif unverified_state == "Utah":
    normalized_state = "Utah"

  return (normalized_state, normalized_district)

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

def parse_candidates_column(candidates, citations):
  """Munges the 'candidates' column of a wikipedia table.

    Args:
      candidates: (str) A bunch of html including candidate names, page links
                  and citation references.
      citations: {(str): (str), ...}
    Returns:
      (str, str): Candidate name, citation
  """
  other_parties = ["Green", "Independent", "Libertarian", "NPP", "PDP", "PIP",
                   "PPT", "R", "Reform", "Republican", "No Party Preference"]
  lines = candidates.text.split("\n")

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
    reference = line.split(")")[1].strip()

    # Extract the citation. This is a bit involved.
    # 1. We pull the reference number out from after the candidate name. It
    # looks like:  [63]
    # 2. We get the A record that matches that reference. It looks like:
    #   <a href="#cite_note-68">[63]</a> The two numbers probably won't match,
    # btw.
    # 3. Strip the pound sign off the cite-note and look it up in the list
    # of citations we created above. That gives us a name, like "Candidate
    # Does A Thing, Says Newspaper!" and a url. We save them both for now,
    # and combine them in a reference-ish way when we create the wiki page.
    refs = candidates.findAll("a")
    citation = None
    for ref in refs:
      if ref.text == reference:  # That's that '[63]' mentioned above.
        href = ref.get('href')   # e.g., #cite_note-68
        match = re.match("^#(.*)$", href)  # strip the leading '#'
        if match is not None:
          note = match.group(1)
          if note in citations:
            citation = citations[note]
        break
    return name, citation


def new_from_wikipedia_page(filename, office):
  """Read a wikipedia Elections page and parse a list of candidates.

    Args:
      filename: (str) a file with one or more candidates
      office: (str) the name of the office to display (house|senate|governor)
    Yields:
      (Candidate): candidates.
  """
  offices = ['house', 'senate', 'governor']
  if office not in offices:
    print "Warning: unexpected office, %s. Should be one of %s" % (office, offices)

  html = open(filename, 'r').read()
  # We don't care about these. 'first_elected' is when the incumbent was
  # elected, so is misleading.
  skip_fields = ["pvi", "candidates", "first_elected"]
  soup = BeautifulSoup(html, 'html.parser')
  citations = {}
  for ref_lists in soup.findAll("ol", {"class": "references"}):
    for ref in ref_lists.findAll("li"):
      name = ref.get('id')
      citation = ref.find("a", {"class": "external text"})
      citations[name] = citation

  tables = soup.findAll("table", {"class": "wikitable sortable"})

  for table in tables:  # each state/territory
    header_fields = []
    for row in table.findAll("tr"):  # each district
      headers = row.findAll("th")    # district name
      columns = row.findAll("td")    # election information
      extracted = {}
      # Look for a top of table header with a "Candidates" column. Set headers
      # and move on.
      if len(columns) == 0:  # it's a top of table header:
        header_fields = [x.text.replace("\n", " ").replace(" ", "_").lower() for x in headers]
        if "candidates" not in header_fields:
          header_fields = []
        continue

      # Don't do anything unless there are headers from a previous row.
      if len(header_fields) == 0:
        continue

      if (len(columns) + len(headers)) != len(header_fields):
        print "unexpected number of columns in %s: %s vs %s" % (row, len(columns), len(header_fields))
        continue

      # This is fragile: we assume headers come first.
      extracted[header_fields[0]] = headers[0]
      for i in range(0, len(columns)):
        extracted[header_fields[i+1]] = columns[i]  # includes markup

      try:
        candidates = extracted["candidates"]
      except KeyError:
        print "No candidates column found! Headers are ", [x for x in extracted.keys()]
        continue
      if candidates is None:
        print "Error: Unexpectedly empty candidates column for [%s]." % row
        continue

      name, citation = parse_candidates_column(candidates, citations)
      if not name:
        continue

      data = {}
      data["name"] = name
      data["office"] = office
      data["party"] = "Democratic"

      for k in extracted:
        if k not in data and k not in skip_fields:
          data[k] = extracted[k].text
      if citation:
        data["reference_name"] = citation.text
        data["reference_url"] = citation.get('href')
      else:
        print "No citation for %s" % name
      try:
        candidate = make_candidate(data)
      except CandidateException, ex:
        print "Skipping %s candidate %s: %s" % (office, name, ex)
        continue
      yield candidate


class CandidateException(Exception):
  """Failed to create a candidate for some reasonable reason."""
  pass

def make_candidate(noisy_data):
  """Turn a dictionary of potentially noisy candidate data into a Candidate.

  Args:
    data: ({str:str, ...}) A dictionary of candidate data, indexed by type
  Returns:
    (Candidate): a populated Candidate object
  Raises:
    CandidateException: missing name, office, district or state
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

  if "district" in data:
    district = data["district"]
  else:
    district = ""
  if "state" in data:
    state = data["state"]
  else:
    state = ""

  state, district = normalize_location(state, district)

  if not state:
    raise CandidateException("missing expected field: state. Had %s" % data.keys())
  else:
    data['state'] = state

  if not district:
    if office == "house":
      raise CandidateException("missing expected field: district")
  else:
    data["district"] = district

  return Candidate(name, data)

class Candidate(object):
  """Name and a bunch of key/value pairs for a single candidate."""
  def __init__(self, name, data):
    self._name = name
    self._data = data

  @staticmethod
  def ordered_fields():
    """Return an ordered list of the interesting fields."""
    return [
      "name",
      "office",
      "state",
      "district",
      "incumbent",
      "representative",
      "reference_name",
      "reference_url",
    ]

  def wikipedia_content(self):
    """Create a wikipedia-formatted string of candidate information."""
    infostr = "{{Infobox Officeholder\n"
    for k in self._data:
      infostr += "| %s = %s\n" % (k, self._data[k])

    infostr += ("\n}}\n'''%s''' is a 2016 Democratic candidate seeking "
                "election to the %s. %s" % (
               self.name(), self.office_and_district(), self.reference()))
    infostr += ("\n\n"
                "== Biography ==\n"
                "TODO: Replace this text with some biographical information."
                "<ref>TODO: Add a URL in here that confirms the bio.</ref>"
                "\n\n"
                "==  Political positions ==\n"
                "TODO: Replace this text with some information about the "
                "candidate's political positions"
                "<ref>TODO: Add a URL in here that confirms them.</ref>"
                "\n\n"
                "== External links ==\n"
                "* [ADD_URL_HERE / %s for %s]") % (self.name(), self.office())

    infostr += "\n\n{{US-politician-stub}}\n\n"

    infostr += ("==References==\n{{reflist}}")

    try:
      state = self._data["state"]
      infostr += ("\n[[Category:%s Democrats]] "
                  "\n[[Category:%s Politicians]]\n" % (state, state))
    except KeyError:
      pass

    return infostr

  def as_list(self):
    """Return information in an ordered list for CSVification."""
    info = []
    for field in self.ordered_fields():
      try:
        info.append(self._data[field].encode('utf-8'))
      except KeyError:
        info.append("")
    return info

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
    elif office == "governor":
      return "Governor of %s" % self._data["state"]
    else:
      return office

  def office(self):
    """Return the office the candidate is running for."""
    try:
      office = self._data["office"]
      if office == "house":
        return "Congress"
      if office == "senate":
        return "Senate"
      return office
    except KeyError:
      return "Office"

  def data(self):
    """Return all of the candidate's data. For testing."""
    return self._data

  def reference(self):
    """Return wikipedia reference."""
    try:
      name = self._data["reference_name"]
      url = self._data["reference_url"]
      # reference names are already enclosed in double quotes.
      return '<ref name=%s>%s</ref>' % (name, url)
    except KeyError:
      return ""
