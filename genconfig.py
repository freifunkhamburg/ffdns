#!/usr/bin/env python

import os
from textwrap import dedent
from optparse import OptionParser
from socket import AF_INET, AF_INET6, inet_pton

class Formatter(object):
    """
    Abstract class to define the interface for formatters.
    """

    def __init__(self):
        """
        Initialize formatter, maybe generate a preamble for the config
        """
        self.config = []
        self.add_comment(dedent(
            """
            This file is automatically generated by the ffdns generator.
            Don't edit it manually! Instead, send pull requests to
            https://github.com/freifunkhamburg/ffdns
            and re-generate it using the genconfig.py there!
            """
        ))

    def add_comment(self, comment):
        """
        Add a comment to the config. Default is prefixed with #
        """
        self.config.append("# " + "\n# ".join(comment.split("\n")))

    def add_data(self, domains, servers):
        """
        Add config directives so that every domain in domains is forwarded to
        every server in servers.
        """
        raise NotImplementedError()

    def finalize(self):
        """
        Finalize configuration and return it
        """
        return "\n".join(self.config)

class DnsmasqFormatter(Formatter):
    "Formatter for dnsmasq"
    def add_data(self, domains, servers):
        for domain in domains:
            for server in servers:
                self.config.append("server=/%s/%s" % (domain, server))

class BindFormatter(Formatter):
    "Formatter for bind9 (>=9.8) using type static-stub"
    def add_data(self, domains, servers):
        for domain in domains:
            self.config.append(dedent("""
                zone "%s" {
                    type static-stub;
                    server-addresses { %s; };
                };
            """ % (domain, "; ".join(servers))).lstrip())

class BindForwardFormatter(Formatter):
    "Formatter for bind9 using type forward"
    def add_data(self, domains, servers):
        for domain in domains:
            self.config.append(dedent("""
                zone "%s" {
                    type forward;
                    forwarders { %s; };
                    forward only;
                };
            """ % (domain, "; ".join(servers))).lstrip())

def create_config(srcdir, fmtclass, exclude=None, filters=[]):
    """
    Generates a configuration using all files in srcdir (non-recursively)
    except those in the iterable exclude.

    The files are read in lexicographic order to produce deterministic results.

    Every option=value pair in the files is passed through all callables in the
    iterable filters. Only if none return False, it is assumed valid.
    """
    COMMENT_CHAR = "#"
    OPTION_CHAR = "="
    formatter = fmtclass()
    for fname in sorted(list(set(os.listdir(srcdir)) - set(exclude))):
        fpath = os.path.join(srcdir, fname)
        if os.path.isfile(fpath):
            domains = []
            servers = []

            with open(fpath) as f:
                formatter.add_comment("\n%s\n" % fname)
                for line in f:
                    if COMMENT_CHAR in line:
                        line, comment = line.split(COMMENT_CHAR, 1)
                        comment = comment.strip()
                        if comment:
                            formatter.add_comment(comment)
                    if OPTION_CHAR in line:
                        option, value = line.split(OPTION_CHAR, 1)
                        option = option.strip()
                        value = value.strip()
                        if not all(filt(option, value) for filt in filters):
                            continue
                        if option == "server":
                            servers.append(value)
                        elif option == "domain":
                            domains.append(value)
                        else:
                            raise RuntimeError("Unknown option '%s' in file '%s'" % (option, fpath))
                    elif line.strip():
                        raise RuntimeError("Unrecognized line '%s' in file '%s'" % (line, fpath))

            if not domains:
                formatter.add_comment("No valid domains found")
            elif not servers:
                formatter.add_comment("No valid servers found")
            else:
                formatter.add_data(domains, servers)

    print(formatter.finalize())

if __name__ == "__main__":
    def try_inet_pton(af, ip):
        try:
            inet_pton(af, ip)
            return True
        except:
            return False

    formatters = {
        "dnsmasq": DnsmasqFormatter,
        "bind": BindFormatter,
        "bind-forward": BindForwardFormatter,
    }
    filters = {
        "v4": lambda option, value: option != "server" or try_inet_pton(AF_INET, value),
        "v6": lambda option, value: option != "server" or try_inet_pton(AF_INET6, value),
    }
    parser = OptionParser()
    parser.add_option("-f", "--format", dest="fmt",
        help="Create config in format FMT. Possible values: %s. Default: dnsmasq" % ", ".join(formatters.keys()), metavar="FMT",
        choices=list(formatters.keys()),
        default="dnsmasq")
    parser.add_option("-s", "--sourcedir", dest="src",
        help="Use files in DIR as input files. Default: data/", metavar="DIR",
        default="data")
    parser.add_option("-x", "--exclude", dest="exclude",
        help="Exclude the comma-separated list of FILES in the sourcedir from the generation", metavar="FILES",
        default="")
    parser.add_option("--filter", dest="filter",
        help="Only include certain servers. Possible choices: %s" % ", ".join(filters.keys()),
        choices=list(filters.keys()))

    (options, args) = parser.parse_args()

    create_config(options.src, formatters[options.fmt], options.exclude.split(","), [filters[options.filter]] if options.filter else [])
