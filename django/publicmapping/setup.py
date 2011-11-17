#!/usr/bin/python
"""
Set up District Builder.

This management command will examine the main configuration file for 
correctness, import geographic levels, create spatial views, create 
geoserver layers, and construct a default plan.

This file is part of The Public Mapping Project
https://github.com/PublicMapping/

License:
    Copyright 2010 Micah Altman, Michael McDonald

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

Author: 
    Andrew Jennings, David Zwarg
"""

from decimal import Decimal
from optparse import OptionParser, OptionGroup
from os.path import exists
from lxml.etree import parse, XMLSchema
from xml.dom import minidom
import traceback, os, sys, random
from redistricting.config import StoredConfig

def main():
    """
    Main method to start the setup of District Builder.
    """
    usage = "usage: %prog [options] SCHEMA CONFIG"
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest="database",
            help="Generate the database schema", default=False,
            action='store_true')
    parser.add_option('-g', '--geolevel', dest="geolevels",
            help="Import the geography from the Nth GeoLevel.", 
            action="append", type="int")
    parser.add_option('-V', '--views', dest="views",
            help="Create database views based on all geographies.",
            action='store_true', default=False)
    parser.add_option('-G', '--geoserver', dest="geoserver",
            help="Create spatial data layers in Geoserver.",
            default=False, action='store_true')
    parser.add_option('-t', '--templates', dest="templates",
            help="Create the system-wide templates.",
            default=False, action='store_true')
    parser.add_option('-n', '--nesting', dest="nesting",
            help="Enforce nested geometries.",
            action='append', type="int")
    parser.add_option('-s', '--static', dest="static",
            help="Collect the static javascript and css files.",
            action='store_true', default=False),
    parser.add_option('-b', '--bard', dest="bard",
            help="Create a BARD map based on the imported spatial data.", 
            default=False, action='store_true'),
    parser.add_option('-B', '--bardtemplates', dest="bard_templates",
            help="Create the BARD reporting templates.",
            action='store_true', default=False),
    parser.add_option('-v', '--verbosity', dest="verbosity",
            help="Verbosity level; 0=minimal output, 1=normal output, 2=all output",
            default=1, type="int")
    parser.add_option('-f', '--force', dest="force",
            help="Force changes if config differs from database",
            default=False, action='store_true')


    (options, args) = parser.parse_args()

    allops = (not options.database) and (not options.geolevels) and (not options.views) and (not options.geoserver) and (not options.templates) and (not options.nesting) and (not options.bard) and (not options.static) and (not options.bard_templates)

    verbose = options.verbosity

    if len(args) != 2:
        if verbose > 0:
            print """
ERROR:

    This script requires a configuration file and a schema. Please check
    the command line arguments and try again.
"""
        sys.exit(1)

    try:
        config = StoredConfig(args[1], schema=args[0])
    except Exception, e:
        if verbose > 0:
            print e[1]
        sys.exit(1)

    (is_valid, msgs,) = config.validate()

    if not is_valid:
        if verbose > 0:
            print "Configuration could not be validated."

        if verbose > 1:
            for msg in msgs:
                print msg
        sys.exit(1)

    if verbose > 0:
        print "Validated config."

    merge_status = config.merge_settings('settings.py')
    if merge_status[0]:
        if verbose > 0:
            print "Generated django settings for publicmapping."
    else:
        if verbose > 0:
            for msg in merge_status[1]:
                print msg
        sys.exit(1)

    merge_status = config.merge_settings('reporting_settings.py')
    if merge_status[0]:
        if verbose > 0:
            print "Generated django settings for reporting."
    else:
        if verbose > 0:
            for msg in merge_status[1]:
                print msg
        sys.exit(1)

    os.environ['DJANGO_SETTINGS_MODULE'] = 'publicmapping.settings'
    
    sys.path += ['.', '..']

    from django.core import management

    if allops or options.database:
        management.call_command('syncdb', verbosity=verbose, interactive=False)

    if allops:
        geolevels = []
        views = True
        geoserver = True
        templates = True
        nesting = []
        static = True
        bard = True
        bard_templates = True
    else:
        geolevels = options.geolevels
        views = options.views
        geoserver = options.geoserver
        templates = options.templates
        nesting = options.nesting
        static = options.static
        bard = options.bard
        bard_templates = options.bard_templates

    management.call_command('setup', config=args[1], verbosity=verbose, geolevels=geolevels, views=views, geoserver=geoserver, templates=templates, nesting=nesting, static=static, bard=bard, bard_templates=bard_templates, force=options.force)
    
    # Success! Exit-code 0
    sys.exit(0)

if __name__ == "__main__":
    main()
