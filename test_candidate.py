#!/usr/bin/python
"""Tests for candidate.py. Run them with py.test."""

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
    cases = [
      # Create a candidate
      ({"can_nam": "Some Person", "office": "house", "party": "DEM",
        "can_off_sta": "NM"},
       {"name": "Some Person", "office": "house", "party": "DEM", "state": "NM"}
      ),
      # Same person, not a dem.
      ({"can_nam": "Some Person", "office": "house", "party": "ind",
        "can_off_sta": "NM"},
      None,
      ),
      # Same person, running for president so ignore them,
      ({"can_nam": "Some Person", "office": "house", "party": "ind",
        "can_off_sta": "NM"},
      None,
      ),
      # Same person, with no specified office
      ({"can_nam": "Some Person", "party": "DEM", "can_off_sta": "NM"},
      None,
      ),
      ]
    for k in cases:
      got = candidate.make_candidate(k[0])
      if got:
        self.assertEqual(k[1], got.data())
      else:
        self.assertEqual(k[1], None)


if __name__ == 'main__':
  unittest.main()
