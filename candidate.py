"""Information about a candidate, including what fields are valid for
Wikipedia's Officeholder onebox.
"""

import yaml

def check_field(field):
  """Checks if a field is valid.

  Args:
    field: (string) A field name.
  Returns:
    (bool) Whether that's in the list of valid fields.
  """
  valid_fields = [
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
    "website",
    "footnotes ",
  ]

  return field in valid_fields


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

class Candidate(object):
  """Name and a bunch of key/value pairs for a single candidate."""
  def __init__(self, name, stuff):
    self._name = name
    self._data = stuff

  def wikipedia_content(self):
    """Create a wikipedia-formatted string of candidate information."""
    infostr = "{{Infobox Officeholder\n"
    for k in self._data:
      if not check_field(k):
        print "%s: %s is not a valid field. Skipping." % (self._name, k)
        continue
      infostr += "| %s = %s\n" % (k, self._data[k])

    infostr += "\n}}"

    return infostr

  def name(self):
    """Return the candidate's name."""
    return self._name

