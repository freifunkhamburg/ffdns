Freifunk DNS repository
=======================

This repository is supposed to make the management of DNS in the ICVPN easier. It consists of two parts:

Data
----
In the data directory, there are files containing information how to resolve the TLDs and other domains (think RDNS) of various Freifunk communities and other networks (like DN42 for example). Please send pull requests to insert/update your own data!

Each community/network has a file of its own in a format as simple as
```
domain=ffhh
domain=112.10.in-addr.arpa
domain=d.0.d.f.2.b.b.2.1.5.d.f.ip6.arpa
server=fd51:2bb2:fd0d::101
server=fd51:2bb2:fd0d::e01
server=10.112.1.1
server=10.112.14.1
```
As you can see, there are lines starting with `domain=` which define domains "owned" by this community, and lines starting with `server=` defining the servers of this community that are able to resolve the domains.

The format is intended to retype as few data as possbile.

Generation script
-----------------
The Python script genconfig.py can generate configs for different DNS resolvers from the above data format. It currently supports bind9 (types `static-stub` and `forward`) and dnsmasq.

It is capable of excluding some files from the data directory, so that you can exclude your own community (because you probably are the master for your own domains) and recursively resolve all others. You may also filter out IPv4 or IPv6 servers if you are operating a single-stack network.

The complete help message reads:
```
Usage: genconfig.py [options]

Options:
  -h, --help            show this help message and exit
  -f FMT, --format=FMT  Create config in format FMT. Possible values: bind,
                        dnsmasq, bind-forward. Default: dnsmasq
  -s DIR, --sourcedir=DIR
                        Use files in DIR as input files. Default: data/
  -x FILES, --exclude=FILES
                        Exclude the comma-separated list of FILES in the
                        sourcedir from the generation
  --filter=FILTER       Only include certain servers. Possible choices: v4, v6
```
