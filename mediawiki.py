#!/usr/bin/python2.7

"""Methods for interacting with a mediawiki instance, like wikipedia."""

import requests
import time

# Rate-limit aggressively. Can be increased if using against a test wiki. Should
# stay cautious when used for wikipedia.
EDIT_PAGES_PER_SECOND = 0.1
QUERY_PAGES_PER_SECOND = 1

# TODO: Set a user agent.

def rate_limited(max_per_second):
  """Rate limiting decorator-with-args.
  Args:
    max_per_second: (float) How many times per second to do the thing.
  Returns:
    (func): A decorator
  """
  interval = 1.0 / float(max_per_second)

  def decorator(func):
    """A rate-limiting decorator.
    Args:
      func: (func) The thing to wrap.
    Returns:
      (func): The rate-limting function to apply to the thing to wrap.
    """
    last_called = [0.0]

    def rate_limited_function(*args, **kwargs):
      """The actual rate limiting logic."""
      elapsed = time.time() - last_called[0]
      wait = interval - elapsed
      if wait > 0:
        time.sleep(wait)
      ret = func(*args, **kwargs)
      last_called[0] = time.time()
      return ret
    return rate_limited_function
  return decorator


class WikiException(Exception):
  """Failed to log in to mediawiki."""
  pass


class Wiki(object):
  """Login credentials and methods for interacting with a mediawiki isntance."""

  def __init__(self, url, username, password, draft_prefix="Draft:"):
    """Log in to the wiki.

    Args:
      url: (str) url of the wiki
      username: login for the wiki
      password: password for the wiki
      draft_prefix: (str) How draft pages are named.
    """
    self.url = url
    self.login_cookies = self.get_login_cookies(username, password)
    self.draft_prefix = draft_prefix

  def get_login_cookies(self, username, password):
    """Return login cookies.
    Args:
      username: (str)
      password: (str)
    Returns:
      (requests.cookies.RequestsCookieJar): delicious cookies
    Raises:
     WikiException: login failed.
    """
    if not username or not password:
      raise WikiException("Empty username or password")

    payload = {'action': 'query', 'format': 'json', 'utf8': '',
               'meta': 'tokens', 'type': 'login'}
    req1 = requests.post(self.url + 'api.php', data=payload)

    if not req1.ok:
      raise WikiException("query: Got status code %s from %s: %s"% (
          req1.status_code, req1.url, req1.reason))

    try:
      login_token = req1.json()['query']['tokens']['logintoken']
    except ValueError, ex:
      raise WikiException("Couldn't parse JSON from login token:", ex)

    payload = {'action': 'login', 'format': 'json', 'utf8': '',
               'lgname': username, 'lgpassword': password,
               'lgtoken': login_token}

    # TODO: It returns a 200 even for a wrong password. Waaaat?
    req2 = requests.post(self.url + 'api.php', data=payload,
                         cookies=req1.cookies)

    if not req2.ok:
      raise WikiException("login: Got status code %s from %s: %s"% (
          req2.status_code, req2.url, req2.reason))

    if len(req2.cookies) == 0:
      raise WikiException("Didn't get any login cookies.")

    return req2.cookies

  @rate_limited(QUERY_PAGES_PER_SECOND)
  def does_page_exist(self, page_to_query):
    """Checks whether a page already exists.
    Args:
      page_to_query: (string) What to look up.
    Returns:
      (str) the page url if it exists; None otherwise.
    Raises:
      WikiException: Bad data from the wiki.
    """
    params = ('?format=json&action=query&titles=%s&prop=info&inprop=url' %
              page_to_query)
    req = requests.get(self.url + 'api.php' + params)
    if not req.ok:
      raise WikiException("Got status code %s from %s: %s"% (
                          req.status_code, req.url, req.reason))

    try:
      pages = req.json()['query']['pages']
      for k in pages: # though there should only be one
        if k != "-1":  # we have a live page!
          return pages[k]['fullurl']
    except ValueError, ex:
      raise WikiException("Couldn't parse JSON:", ex)


  def does_draft_exist(self, page_to_query):
    """Checks whether a draft page exists.
    Args:
      page_to_query: (string) What to look up. The page name will be prepended
                     with |self.draft_prefix|.
    Returns:
      (str) the page url if it exists; None otherwise.
    """
    draft_to_query = "%s%s" % (self.draft_prefix, page_to_query)
    return self.does_page_exist(draft_to_query)


  @rate_limited(EDIT_PAGES_PER_SECOND)
  def create_page(self, person, create_draft=False):
    """Create a page if it doesn't exist. If it already exists, just silently
       does nothing.
     Args:
      person: (candidate.Candidate) data about one candidate
      create_draft: (bool) Whether to create a draft page using the
                    |self.draft_prefix| variable.
     Returns:
      (str) Url of page, whether newly created or already existing.
    Raises:
      WikiException: Couldn't create the page. The page already existing does
        not raise an exception.
    """
    if create_draft:
      page_to_edit = "%s%s" % (self.draft_prefix, person.name())
    else:
      page_to_edit = person.name()

    params = '?format=json&action=query&meta=tokens&continue='
    req = requests.get(self.url + 'api.php' + params,
                       cookies=self.login_cookies)

    if req.status_code != 200:
      raise WikiException("Got status code %s from %s: %s"% (
          req.status_code, req.url, req.reason))

    try:
      edit_token = req.json()['query']['tokens']['csrftoken']
    except ValueError, ex:
      raise WikiException("Couldn't parse edit token from JSON:", ex)

    edit_cookie = self.login_cookies.copy()
    edit_cookie.update(req.cookies)

    content_to_write = person.wikipedia_content()

    payload = {'action': 'edit', 'assert': 'user', 'format': 'json', 'utf8': '',
               'text': content_to_write, 'summary': 'candidatebot did this',
               'title': page_to_edit, 'token': edit_token, 'createonly': True}
    req = requests.post(self.url + 'api.php', data=payload, cookies=edit_cookie)

    if not req.ok:
      raise WikiException("Got status code %s from %s: %s"% (
              req.status_code, req.url, req.reason))

    # I can't find this information anywhere except in the text /o\
    if req.text.find('"result":"Failure"') > -1:
      raise WikiException("Saw error in creation response: %s" % req.text)

    created_page = self.does_page_exist(page_to_edit)
    if not created_page:
      raise WikiException("Wiki page wasn't created at %s, but there were no "
                          "errors. " % page_to_edit)

    # Add to the list of stubs we've created.
    link = "[[%s]]<br>" % page_to_edit
    list_page = "%s%s" % (self.draft_prefix, "CandidatebotListOfPages")

    payload = {'action': 'edit', 'assert': 'user', 'format': 'json',
               'utf8': '', 'appendtext': link,
               'summary': 'candidatebot did this', 'title': list_page,
               'token': edit_token}
    req = requests.post(self.url + 'api.php', data=payload,
                        cookies=edit_cookie)

    return created_page
