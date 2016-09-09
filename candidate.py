"""Information about a candidate, including what fields are valid for
Wikipedia's Officeholder onebox.
"""

import yaml
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
    Candidates
"""
  tree = etree.iterparse(filename)

  for _, elem in tree:
    if not elem.getchildren():
      continue
    data = {}
    for datum in elem.getchildren():
      data[datum.tag] = datum.text

    candidate = make_candidate(data)
    if candidate:
      yield candidate


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
    party = data["party"]
    office = data["office"]
  except KeyError:
    return None

  # Reduce the noise from this very, very noisy dataset.
  if party and party.lower() != "dem":
    return None
  if office and office.lower() == "president":
    return None

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

    infostr += "\n}}"

    return infostr

  def name(self):
    """Return the candidate's name."""
    return self._name

  def office(self):
    """Return the candidate's office."""
    try:
      return self._data["office"]
    except KeyError:
      return ""

  def data(self):
    """Return all of the candidate's data. For testing."""
    return self._data
