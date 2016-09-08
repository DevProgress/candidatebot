import yaml

def CheckField(field):
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


def NewFromYaml(filename):
  """ Read a yaml file, yield Candidates.

  Args: 
    filename (string): a file with one or more candidates
  Yields:
    Candidates
  """
  candidates = []
  with open(filename) as stream:
    try:
      contents = yaml.load(stream)
    except yaml.YAMLError as e:
      print e

  for element in contents:
    if not element["name"]:
      print "No name. Skipping."
      continue

    candidate = Candidate(element["name"], element)

    yield candidate

 
""" Sample template usage:
  {{Infobox Officeholder
  | honorific-prefix = Honorable
  | name = Candidate McCandidate
  | honorific-suffix =
  | image = 
  | alt = Some person
  | state_assembly = California <!--more often use state_house -->
  | district = [[California's 46th Assembly district|46th]]
  | term_start = 2002
  | term_end =
  | predecessor = [[Poopy]]
  | successor = 
  | speaker = 66th
  | term_start2 = 2002
  | term_end2 =
  | predecessor2 = [[Herb Wesson]]
  | successor2 = Termed out (2008)
  | birth_date = December 22, 1966
  | birth_place = [[San Diego]], California, U.S.
  | death_date =
  | death_place =
  | nationality = American
  | spouse = Maria Robles
  | party = [[Democratic Party (United States)|Democratic]]
  | relations =
  | children =
  | residence =
  | alma_mater =
  | occupation =
  | profession = Politician
  | religion = Catholic
  | signature =
  | signature_alt =
  | website =
  | footnotes =
  }}
"""  


"""Name and a bunch of key/value pairs for a single candidate."""
class Candidate:
  def __init__(self, name, stuff):
    self._name = name
    self._data = stuff

  def Info(self):
    """Create a wikipedia-formatted string of candidate information."""
    infostr = "{{Infobox Officeholder\n"
    for k in self._data:
      if not CheckField(k):
        print("%s: %s is not a valid field. Skipping." % (self._name, k))
        continue
      infostr += "| %s = %s\n" % (k, self._data[k])

    infostr += "\n}}"

    return infostr

  def Name(self):
    return self._name

