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

Link = collections.namedtuple('Link', ['origin', 'target'])
Link.__doc__ = """
Class representing individual links, to simplify bookkeeping.

Attributes:
    origin (str): URL of the document containing the link.
    target (str): URL referred to by the link.
"""

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
        if not root_parts.scheme:
            # given a filesystem path, not a URL
            path_ = os.path.abspath(root_parts.path)
            root_parts = root_parts._replace(path=path_)
            root_parts = root_parts._replace(scheme='file')
        self.root = urllib.parse.urlunsplit(root_parts)

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

    def check_one_url(self, link):
        """Get list of URLs linked to from the current URL (if any).

        Args:
            link (:obj:`Link`): Instance of :class:`Link`. Only the URL in
                link.target is examined.

        Returns: 
            Either 

                #. None if link.target can't be opened, 
                #. the empty list if link.target is not an html document, or 
                #. a list of links contained in link.target, expressed as 
                    :class:`Link` objects.
        """
        if hasattr(link, 'target'):
            url = link.target
        else:
            return None
        try:
            f = urllib.request.urlopen(url)
        except urllib.error.HTTPError as e:
            print('Error code: ', e.code)
            return None
        except urllib.error.URLError as e:
            print('\nFailed to find file or connect to server.')
            print('Reason: ', e.reason)
            return None
        if f.info().get_content_subtype() != 'html':
            return []
        else:
            parser = LinkParser()
            links = [
                Link(origin=url, target=urllib.parse.urljoin(url, link_out)) \
                    for link_out in self.gen_links(f, parser)
            ]
            f.close()
            return links

    def breadth_first(self, root_url):
        """Breadth-first search of all files linked from an initial root_url. 

        The search correctly handles cycles (ie, A.html links to B.html and 
        B.html links to A.html) and only examines files in subdirectories of 
        root_url's directory, so that links to external sites are ignored, 
        rather than trying to trace the link structure of the whole internet.

        Args:
            root_url (str): URL of an html file to start the search at.

        Returns:
            list of (link_source, link_target) tuples where the file in 
                link_target couldn't be found.
        """
        missing = []
        known_urls = set([root_url])
        root_parts = urllib.parse.urlsplit(root_url)
        root_parts = root_parts._replace(path=os.path.dirname(root_parts.path))
        # root_parent = URL to directory containing file referred to in root_url
        root_parent = urllib.parse.urlunsplit(root_parts)

        queue = [Link(origin=None, target=root_url)]
        if self.verbose:
            print("Checking {}:".format(root_url))
        while queue:
            current_link = queue.pop(0)
            if self.verbose:
                print("\tChecking {}".format(
                    current_link.target[len(root_parent) + 1:]
                ), end="")
            new_links = self.check_one_url(current_link)
            if new_links is None:
                if self.verbose:
                    print('...MISSING!')
                missing.append(current_link)
            else:
                if self.verbose:
                    print('...OK')
                # restrict links to those that start with root_parent
                new_links = [
                    lnk for lnk in new_links if lnk.target not in known_urls \
                        and lnk.target.startswith(root_parent)
                ]
                queue.extend(new_links)
                # update known_urls so that we don't chase cycles
                known_urls.update([lnk.target for lnk in new_links])
        return missing

    def group_relative_links(self, missing):
        """Format paths to missing linked files as relative paths, grouped by 
        POD.

        Args:
            missing (list): List of :class:`Link` objects found by 
                :meth:`breadth_first`, whose targets correspond to missing files.

        Returns:
            dict, with keys given by the short names of PODs with missing files
                and values given by a list of the files that POD is missing. 
                Missing files are listed by their path relative to the POD's 
                output directory.
        """
        missing_dict = collections.defaultdict(list)
        for link in missing:
            prefix = os.path.commonprefix([link.origin, link.target])
            dirs = urllib.parse.urlsplit(prefix).path.split('/')
            dirs = [d for d in dirs if d]
            pod = dirs[-1]
            rel_link = link.target[len(prefix):]
            missing_dict[pod].append(rel_link)
        return missing_dict

    def verify_pod_links(self, pod_name):
        """Perform search for missing linked files that were supposed to have 
        been output by pod_name.

        Args:
            pod_name: Name of the POD to check for missing files.

        Returns:
            A list of the files that POD is missing. Missing files are listed by
                their path relative to the POD's output directory.
        """
        root_parts = urllib.parse.urlsplit(self.root)
        if not root_parts.path.endswith('.html'):
            path_ = os.path.join(root_parts.path, pod_name+'.html')
            root_parts = root_parts._replace(path=path_)
        root_url = urllib.parse.urlunsplit(root_parts)

        missing = self.breadth_first(root_url)
        missing_dict = self.group_relative_links(missing)
        return missing_dict.get(pod_name, [])

    def verify_all_links(self):
        """Perform search for any missing linked files from a run of the MDTF
        framework and collect them by POD.

        Returns:
            dict, with keys given by the short names of PODs with missing files
                and values given by a list of the files that POD is missing. 
                Missing files are listed by their path relative to the POD's 
                output directory.
        """
        root_parts = urllib.parse.urlsplit(self.root)
        if not root_parts.path.endswith('.html'):
            path_ = os.path.join(root_parts.path, 'index.html')
            root_parts = root_parts._replace(path=path_)
        root_url = urllib.parse.urlunsplit(root_parts)

        missing = self.breadth_first(root_url)
        return self.group_relative_links(missing)

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
    missing_dict = link_verifier.verify_all_links()

    if missing_dict:
        print("ERROR: the following files are missing:")
        print(util.pretty_print_json(missing_dict))
        exit(1)
    else:
        print("SUCCESS: no missing links found.")
        exit(0)
