#!/usr/bin/python

import getpass
import requests
import sys

import candidate

username = "candidatebot"
#baseurl = "http://test.wikipedia.org/w/"
baseurl = "http://cso.noidea.dog/w/"

# TODO: Set a user agent.

def get_login_cookies(username, password):
  if not username or not password:
    print "Empty username or password"
    return None

  payload = { 'action': 'query', 'format': 'json', 'utf8': '',
              'meta': 'tokens', 'type': 'login' }
  req1 = requests.post(baseurl + 'api.php', data=payload)
  
  if not req1.ok:
    print "query: Got status code %s from %s: %s"% (req1.status_code, req1.url, req1.reason)
    return None

  try:
    login_token = req1.json()['query']['tokens']['logintoken']
  except ValueError:
    print "Couldn't parse JSON from login token."
    return None

  payload = { 'action': 'login',  'format': 'json', 'utf8': '',
              'lgname': username, 'lgpassword': password, 'lgtoken': login_token }

  # TODO: It returns a 200 even for a wrong password. Waaaat?
  req2 = requests.post(baseurl + 'api.php', data=payload, cookies=req1.cookies)

  if not req2.ok:
    print "login: Got status code %s from %s: %s"% (req2.status_code, req2.url, req2.reason)
    return None

  if len(req2.cookies) == 0:
    print "Didn't get any login cookies."
    return None

  return req2.cookies

# TODO: Be smarter about reporting that pages already exist.
def edit_page(page_to_edit, content_to_write, login_cookies):
  """Create a page if it doesn't exist. If it already exists, just silently
     does nothing.

   Args:
    page_to_edit: (str) Usually the candidate's name.
    content_to_write: (str) What to write to the new page, in wikipedia format.
    login_cookies: (requests.cookies.RequestsCookieJar) Cookies from when we
      authenticated with the wiki.

   Returns:
    (bool) Did this work without errors?
  """
  params = '?format=json&action=query&meta=tokens&continue='
  req = requests.get(baseurl + 'api.php' + params, cookies=login_cookies)

  if req.status_code != 200:
    print "Got status code %s from %s: %s"% (req.status_code, req.url, req.reason)
    return False

  try:
    edit_token = req.json()['query']['tokens']['csrftoken']
  except ValueError:
    print "Couldn't parse edit token from JSON."
    return False

  edit_cookie = login_cookies.copy()
  edit_cookie.update(req.cookies)

  payload = { 'action': 'edit', 'assert': 'user', 'format': 'json', 'utf8': '',
              'text': content_to_write, 'summary': 'candidatebot did this',
              'title': page_to_edit, 'token': edit_token, 'createonly': True }
  req = requests.post(baseurl + 'api.php', data=payload, cookies=edit_cookie)

  if req.status_code != 200:
    print "Got status code %s from %s: %s"% (req.status_code, req.url, req.reason)
    return False
  return True


def main():
  password = getpass.getpass("Password for wikipedia account %s: " % username)
  login_cookies = get_login_cookies(username, password)
  if not login_cookies:
    sys.exit(1)

  for person in candidate.NewFromYaml("candidates.yaml"):
    print "Looking for a Wikipedia page for", person.Name()

    ok = edit_page(person.Name(), person.Info(), login_cookies)
    
    if ok:
      print "That seemed to go ok."
    else:
      print "There were errors."

main()
