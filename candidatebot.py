#!/usr/bin/python

import getpass
import requests
import sys

import candidate

username = "candidatebot"
#baseurl = "http://test.wikipedia.org/w/"
baseurl = "http://cso.noidea.dog/w/"
yaml_file = "candidates.yaml"

# TODO: Set a user agent.

def get_login_cookies(username, password):
  """Return login cookies.

  Args:
    username: (str)
    password: (stra
  Returns:
    (requests.cookies.RequestsCookieJar): delicious cookies
  """
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
  except ValueError, e:
    print "Couldn't parse JSON from login token:", e
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

def does_page_exist(page_to_query, login_cookies):
  """Checks whether a page already exists.
  
  Args:
    page_to_query: (string) What to look up.
    login_cookies: (requests.cookies.RequestsCookieJar) Cookies from when we
      authenticated with the wiki.
  Returns:
    (bool) whether the page exists.
  """
  params = '?format=json&action=query&titles=%s&prop=info&inprop=url' % page_to_query
  req = requests.get(baseurl + 'api.php' + params)
  if not req.ok:
    print "Got status code %s from %s: %s"% (req.status_code, req.url, req.reason)

  try:
    pages = req.json()['query']['pages']
    for k in pages: # though there should only be one
      if k != "-1":  # we have a live page!
        print "%s already has a page at %s" % (page_to_query, pages[k]['fullurl'])
        return True
  except ValueError, e:
    print "Couldn't parse JSON:", e


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
  if does_page_exist(page_to_edit, login_cookies):
    return True

  params = '?format=json&action=query&meta=tokens&continue='
  req = requests.get(baseurl + 'api.php' + params, cookies=login_cookies)

  if req.status_code != 200:
    print "Got status code %s from %s: %s"% (req.status_code, req.url, req.reason)
    return False

  try:
    edit_token = req.json()['query']['tokens']['csrftoken']
  except ValueError, e:
    print "Couldn't parse edit token from JSON:", e
    return False

  edit_cookie = login_cookies.copy()
  edit_cookie.update(req.cookies)

  print "Creating wikipedia page for %s" % page_to_edit
  payload = { 'action': 'edit', 'assert': 'user', 'format': 'json', 'utf8': '',
              'text': content_to_write, 'summary': 'candidatebot did this',
              'title': page_to_edit, 'token': edit_token, 'createonly': True }
  req = requests.post(baseurl + 'api.php', data=payload, cookies=edit_cookie)

  if not req.ok:
    print "Got status code %s from %s: %s"% (req.status_code, req.url, req.reason)
    return False
  return True


def main():
  password = getpass.getpass("Password for wikipedia account %s: " % username)
  login_cookies = get_login_cookies(username, password)
  if not login_cookies:
    sys.exit(1)

  for person in candidate.new_from_yaml(yaml_file):
    ok = edit_page(person.name(), person.wikipedia_content(), login_cookies)
    
    if ok:
      print "That seemed to go ok."
    else:
      print "There were errors."

main()
