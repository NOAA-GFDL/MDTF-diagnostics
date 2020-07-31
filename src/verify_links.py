#!/usr/bin/env python
"""
Check output of the files returned by a run of the MDTF framework and determine
if any PODs failed to generate files, as determined by non-functional html links
in the output webpages.

Based on test_website by Dani Coleman, bundy@ucar.edu
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import os
from src import six
import argparse
import collections
import itertools
from six.moves import html_parser, urllib # py3: html.parser
from src import util

# https://stackoverflow.com/a/41663924
class LinkParser(html_parser.HTMLParser):
    def reset(self):
        super(LinkParser, self).reset()
        self.links = iter([])

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                    self.links = itertools.chain(self.links, [value])


class LinkVerifier(object):
    def __init__(self, root, verbose=False):
        """Setup for search. Form a file:// URL if we're given a local path, and
        organize missing links in a dictionary keyed on POD name.
        """
        self.verbose=verbose
        root_parts = urllib.parse.urlsplit(root)
        path_ = root_parts.path
        if not path_.endswith('index.html'):
            path_ = os.path.join(path_, 'index.html')
        if not root_parts.scheme:
            # given a filesystem path, not a URL
            path_ = os.path.abspath(path_)
            root_parts = root_parts._replace(scheme='file')
        root_parts = root_parts._replace(path=path_)
        self.root = urllib.parse.urlunsplit(root_parts)
        root_parts = root_parts._replace(path=os.path.dirname(path_))
        self.urlbase = urllib.parse.urlunsplit(root_parts)

    @staticmethod
    def gen_links(f, parser):
        """Parse contents of an HTML file f and yield targets of all links.
        """
        #encoding = f.headers.get_content_charset() or 'UTF-8'# py3
        encoding = f.headers.getparam('charset') or 'UTF-8'
        for line in f:
            parser.feed(line.decode(encoding))
            for link in parser.links:
                yield link

    def check_one_url(self, link_source_url, url):
        """Given a url, return 1) None if resource can't be accessed (doesn't exist),
        or 2) a list of all html links appearing in that file (if any).
        """
        try:
            f = urllib.request.urlopen(url)
        except (urllib.error.HTTPError, urllib.error.URLError):
            return None
        if f.info().getsubtype() != 'html':
            return []
        else:
            parser = LinkParser()
            links = [(url, urllib.parse.urljoin(url, l)) for l in self.gen_links(f, parser)]
            f.close()
            return links

    def breadth_first(self, root_url, url_base):
        """Do breadth-first search of all files linked from an initial root_url. 
        Return a list of (link_source, link_target) tuples where the file in 
        link_target couldn't be found.
        """
        missing = []
        queue = [('', root_url)]
        known_urls = set([root_url])
        while queue:
            current_url = queue.pop(0)
            if self.verbose:
                print("\tChecking {}".format(current_url[1][len(url_base) + 1:]), end="")
            new_links = self.check_one_url(*current_url)
            if new_links is None:
                if self.verbose:
                    print('...MISSING!')
                missing.append(current_url)
            else:
                if self.verbose:
                    print('...OK')
                # known_urls so that we don't chase cycles
                # restrict links to those that start with url_base to avoid trying
                # to download all of ncar.ucar.edu
                new_links = [l for l in new_links \
                    if l[1] not in known_urls and l[1].startswith(url_base)]
                queue.extend(new_links)
                known_urls.update([l[1] for l in new_links])
        return missing

    def get_missing_pods(self):
        if self.verbose:
            print("Checking {}\n".format(self.root))
        missing = self.breadth_first(self.root, self.urlbase)
        
        missing_dict = collections.defaultdict(list)
        for tup in missing:
            prefix = os.path.commonprefix(tup)
            dirs = urllib.parse.urlsplit(prefix).path.split('/')
            dirs = [d for d in dirs if d]
            pod = dirs[-1]
            rel_link = tup[1][len(prefix):]
            missing_dict[pod].append(rel_link)
        return missing_dict

# --------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true",
        help="increase output verbosity")
    parser.add_argument("path_or_url", 
        help="URL or filesystem path to the MDTF framework output directory.")
    args = parser.parse_args()
    
    link_verifier = LinkVerifier(args.path_or_url, args.verbose)
    missing_dict = link_verifier.get_missing_pods()

    if missing_dict:
        print("ERROR: the following files are missing:")
        print(util.pretty_print_json(missing_dict))
        exit(1)
    else:
        print("SUCCESS: no missing links found.")
        exit(0)
