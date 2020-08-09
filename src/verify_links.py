#!/usr/bin/env python
"""
Check output of the files returned by a run of the MDTF framework and determine
if any PODs failed to generate files, as determined by non-functional html links
in the output webpages.

Based on test_website by Dani Coleman, bundy@ucar.edu
"""
import sys
# do version check before importing other stuff
if sys.version_info[0] != 3 or sys.version_info[1] < 6:
    print(("ERROR: MDTF currently only supports python >= 3.6.*. Please check "
    "which version is on your $PATH (e.g. with `which python`.)"))
    print("Attempted to run with following python version:\n{}".format(sys.version))
    exit(1)
# passed; continue with imports
import os
import argparse
import collections
import itertools
from html.parser import HTMLParser
import urllib.parse
import urllib.request
import urllib.error
from src import util

class LinkParser(HTMLParser):
    """Custom subclass of :py:class:`~html.parser.HTMLParser` which constructs 
    an iterable over each <a> tag.
    
    Adapted from `<https://stackoverflow.com/a/41663924>`__.
    """
    def reset(self):
        super(LinkParser, self).reset()
        self.links = iter([])

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            for name, value in attrs:
                if name.lower() == 'href':
                    self.links = itertools.chain(self.links, [value])


class LinkVerifier(object):
    def __init__(self, root, verbose=False):
        """Initialize search for broken links.
        
        Args:
            root (str): Either a URL or path on the local filesystem. Location 
                of the top-level html file to begin the search from.
            verbose (bool, default False): Set to True to print each file 
                examined.
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
        """Generator which parses the contents of an HTML file f and yields 
        targets of all the links it contains.

        Adapted from `<https://stackoverflow.com/a/41663924>`__.

        Args:
            f: :py:mod:`urllib.respose` object of the form returned by 
                :py:func:`~urllib.request.urlopen`: either 
                :py:class:`~http.client.HTTPResponse` for http or https, or 
                :py:class:`urllib.response.addinfourl` for files.
            parser: instance of :class:`LinkParser`.

        Yields:
            Contents of the `href` attribute of each `a` tag of f, as extracted 
                by :class:`LinkParser`.
        """
        encoding = f.headers.get_content_charset() or 'UTF-8'
        for line in f:
            parser.feed(line.decode(encoding))
            yield from parser.links

    def check_one_url(self, link_source_url, url):
        """Get list of URLs linked to from the current URL (if any).

        Args:
            link_source_url (str): unused.
            url (str): URL to examine.

        Returns: 
            Either 

                #. None if url can't be opened, 
                #. the empty list if url is not an html document, or 
                #. a list of links contained in url, expressed as 
                    (`url`, `target_url`) tuples.
        """
        try:
            f = urllib.request.urlopen(url)
        except urllib.error.URLError as e:
            if hasattr(e, 'reason'):
                print('Failed to reach a server.')
                print('Reason: ', e.reason)
            elif hasattr(e, 'code'):
                print('The server couldn\'t fulfill the request.')
                print('Error code: ', e.code)
            return None
        if f.info().get_content_subtype() != 'html':
            return []
        else:
            parser = LinkParser()
            links = [
                (url, urllib.parse.urljoin(url, link)) \
                    for link in self.gen_links(f, parser)
            ]
            f.close()
            return links

    def breadth_first(self, root_url, url_base):
        """Breadth-first search of all files linked from an initial root_url. 

        The search correctly handles cycles (ie, A.html links to B.html and 
        B.html links to A.html) and only examines files in subdirectories of 
        root_url's directory, so that links to external sites are ignored, 
        rather than trying to trace the link structure of the whole internet.

        Args:
            root_url (str): URL of an html file to start the search at.
            url_base (str): Directory containing the file in root_url.

        Returns:
            list of (link_source, link_target) tuples where the file in 
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
                # restrict links to those that start with url_base
                new_links = [l for l in new_links \
                    if l[1] not in known_urls and l[1].startswith(url_base)]
                queue.extend(new_links)
                # update known_urls so that we don't chase cycles
                known_urls.update([l[1] for l in new_links])
        return missing

    def get_missing_pods(self):
        """Perform search for missing linked files and collect them by POD.

        This is the only user-facing method of :class:`LinkVerifier` once it's
        been initialized.

        Returns:
            dict, with keys given by the short names of PODs with missing files
                and values given by a list of the files that POD is missing. 
                Missing files are listed by their path relative to the POD's 
                output directory.
        """
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
    # Wrap input/output if we're called as a standalone script
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
