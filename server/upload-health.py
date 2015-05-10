#!/usr/bin/env python
#
# Copyright (C) 2013-2015 eNovance SAS <licensing@enovance.com>
#
# Author: Erwan Velu <erwan.velu@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

'''CGI script part of the eDeploy system.

It receives on its file form a file containing a Python dictionnary
with the hardware detected on the remote host. In return, it sends
a Python configuration script corresponding to the matched config.

If nothing matches, nothing is returned. So the system can abort
its configuration.

On the to be configured host, it is usually called like that:

$ curl -i -F name=test -F file=@/hw.lst http://localhost/cgi-bin/upload.py
'''

import ConfigParser
import cgi
import cgitb
import json
import os
import sys
import time

from hardware import matcher

import upload


def main():
    '''CGI entry point.'''

    config = ConfigParser.ConfigParser()
    config.read('/etc/edeploy.conf')

    def config_get(section, name, default):
        'Secured config getter.'
        try:
            return config.get(section, name)
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            return default

    cfg_dir = os.path.normpath(config_get(
        'SERVER',
        'HEALTHDIR',
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     '..',
                     'health'))) + '/'

    # parse hw file given in argument or passed to cgi script
    if len(sys.argv) == 3 and sys.argv[1] == '-f':
        hw_file = open(sys.argv[2])
    else:
        cgitb.enable()

        form = cgi.FieldStorage()

        if 'file' not in form:
            upload.fatal_error('No file passed to the CGI')

        fileitem = form['file']
        hw_file = fileitem.file

    try:
        json_hw_items = json.loads(hw_file.read(-1))
    except Exception, excpt:
        upload.fatal_error("'Invalid hardware file: %s'" % str(excpt))

    def encode(elt):
        'Encode unicode strings as strings else return the object'
        try:
            return elt.encode('ascii', 'ignore')
        except AttributeError:
            return elt

    hw_items = []
    for info in json_hw_items:
        hw_items.append(tuple(map(encode, info)))

    filename_and_macs = matcher.generate_filename_and_macs(hw_items)
    dirname = time.strftime("%Y_%m_%d-%Hh%M", time.localtime())

    if form.getvalue('session'):
        dest_dir = (cfg_dir + os.path.basename(form.getvalue('session')) +
                    '/' + dirname)
    else:
        dest_dir = cfg_dir + '/' + dirname

    try:
        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir)
    except OSError, e:
        upload.fatal_error("Cannot create %s directory (%s)" %
                           (dest_dir, e.errno))

    upload.save_hw(hw_items, filename_and_macs['sysname'], dest_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception, err:
        upload.fatal_error(str(err))
