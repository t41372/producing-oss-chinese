#!/usr/bin/env python3

import sys
import os

#######################################################
candidate_xsldirs = (
    # Fedora
    '/usr/share/sgml/docbook/xsl-stylesheets',
    # Cygwin
    '/usr/share/docbook-xsl',
    # Debian
    '/usr/share/xml/docbook/stylesheet/nwalsh',
    # SUSE
    '/usr/share/xml/docbook/stylesheet/nwalsh/current',
    # FreeBSD
    '/usr/local/share/xsl/docbook',
    # Ubuntu (docbook-xsl-ns package)
    '/usr/share/xml/docbook/stylesheet/docbook-xsl-ns'
    # Please add your OS's location here if not listed!
    )
#######################################################

tools_bin_dir = os.path.dirname(sys.argv[0])
xsl_dir = os.path.join(tools_bin_dir, '..', 'xsl')

if os.path.exists(xsl_dir):
    sys.stderr.write("XSL directory '%s' already exists\n" % xsl_dir)
    sys.exit(0)

for candidate in candidate_xsldirs:
    if os.path.exists(os.path.join(candidate, 'html', 'docbook.xsl')):
        os.symlink(candidate, xsl_dir)
        print("Found and linked %s" % candidate)
        break
else:
    sys.stderr.write('ERROR: Failed to find a DocBook XSL directory\n')
    sys.exit(1)
