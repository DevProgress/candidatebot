#!/usr/bin/python
"""Tests for candidate.py. Run them with py.test."""

import re
import unittest

import candidate

# pylint: disable=too-many-public-methods
class TestCandidate(unittest.TestCase):
  """Tests for candidate.py."""

  def test_normalize_name(self):
    """Test translating names from various formats to Firstname Lastname."""
    cases = {
      "CATFACE, ALEX": "Alex Catface",
      "BANANA, MABEL JR.": "Mabel Banana Jr",
      "SLEEPERSOFA, LUCY DR": "Lucy Sleepersofa",
      "BEAR, P III": "P Bear III",
      "Some Ok Name": "Some Ok Name",
    }
    for k in cases:
      self.assertEqual(candidate.normalize_name(k), cases[k])

  def test_validity(self):
    """Test checking fields for validity.

    This is a kind of pointless test, but let's exercise the code.
    """
    cases = {
      "office": True,
      "icecream_flavor": False,
    }
    for k in cases:
      self.assertEqual(candidate.check_field(k), cases[k])

  def test_candidate_creation(self):
    """Test candidate creation from a dictionary."""
    valid_cases = [
      # Create a candidate
      ({"can_nam": "Some Person", "office": "senate", "party": "DEM",
        "can_off_sta": "NM"},
       {"name": "Some Person", "office": "senate", "party": "DEM", "state": "New Mexico"}
      ),
      # Differently formatted name
      ({"can_nam": "PERSON, SOME", "office": "senate", "party": "DEM",
        "can_off_sta": "NM"},
       {"name": "Some Person", "office": "senate", "party": "DEM", "state": "New Mexico"}
      ),
      # House candidate with a district
      ({"can_nam": "Some Person", "party": "Democratic", "office": "house", "district": "West Virginia 2"},
       {"name": "Some Person", "party": "Democratic", "office": "house", "state": "West Virginia", "district": "2nd"},
      ),
      # Invalid fields are retained (though not used).
      ({"can_nam": "PERSON, SOME", "office": "senate", "party": "DEM", "state": "AL",
        "icecream_flavor": "banana"},
       {"name": "Some Person", "office": "senate", "party": "DEM", "state": "Alabama",
       "icecream_flavor": "banana",}
      ),
     ]

    # Invalid cases raise a CandidateException
    invalid_cases = [
      # No specified office
      ({"can_nam": "Some Person", "party": "DEM", "can_off_sta": "NM"},
      None,
      ),
      # House candidate without a district
      ({"can_nam": "Some Person", "party": "DEM", "can_off_sta": "NM", "office": "house"},
      None,
      ),
    ]
    for k in valid_cases:
      got = candidate.make_candidate(k[0])
      self.assertEqual(k[1], got.data())

    for k in invalid_cases:
      try:
        self.assertFalse(candidate.make_candidate(k[0]))
        self.fail()
      except candidate.CandidateException:
        pass

  def test_district(self):
    """Test district munging."""
    cases = [
      ["California 1", "California", "1st"],
      ["New York 2", "New York", "2nd"],
      ["New Mexico 3", "New Mexico", "3rd"],
      ["Florida 18", "Florida", "18th"],
      ["Wyoming at-large", "Wyoming", "at-large"],
    ]
    for k in cases:
      got = candidate.normalize_district(k[0])
      expected = (k[1], k[2])
      self.assertEqual(got, expected)

  def test_state(self):
    """Test state translation."""
    cases = [
      ("CA", "California"),
      ("NM", "New Mexico"),
      (None, None),
      ("South Carolina", "South Carolina"),
      ("XX", "XX"),
    ]
    for k in cases:
      self.assertEqual(candidate.normalize_state(k[0]), k[1])


  def test_content(self):
    """Test wikipedia output."""
    data = {"can_nam": "Some Person", "office": "house", "party": "DEM",
            "can_off_sta": "NM", "can_off_dis": "New Mexico 7"}

    got = candidate.make_candidate(data).wikipedia_content()
    # fields could come out in any order, so we can't do a full match;
    # we just check that something plausible came out.
    expected_re = re.compile(
        "^{{Infobox Officeholder\n.*| name = Some Person\n.*}}$")
    match = expected_re.search(got)

    self.assertTrue(match)


  def test_wikipedia_html(self):
    """Test parsing wikipedia html.
    """

    filename = "test_house.html"
    got = []
    for person in candidate.new_from_wikipedia_page(filename):
      got.append(person.data())

    expected_data1 = {
      "name": u"Pageless One",
      "state": u"Alabama",
      "district": u"2nd",
      "incumbent": u"Name Two",
      "reference": u"[63]",
      "office": "house",
      "party": "Democratic",
    }
    expected_data2 = {
      "name": u"Pageless Two",
      "state": u"Alaska",
      "district": u"at-large",
      "incumbent": u"Name Five",
      "reference": u"[71]",
      "office": "house",
      "party": "Democratic",
    }
    expected = [
      expected_data1,
      expected_data2,
   ]
    self.assertEqual(got, expected)


if __name__ == 'main__':
  unittest.main()
