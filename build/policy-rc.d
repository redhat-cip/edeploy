#!/bin/bash
#
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Frederic Lepied <frederic.lepied@enovance.com>
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

# Purpose: prevent services to start or do whatever at installation time.

script="$1"
actions="$2"
level="$3"

# try to detect that we are called from a package scriptlet
if [ -n "$PPID" ]; then
    PPPID=$(ps -p $PPID -o ppid|head -2|tail -1|sed -e 's/^\s*//' -e 's/\s*$//')
    #cat /proc/$PPPID/cmdline|tr '\000' '\n' 1>&2
    set -- $(cat /proc/$PPPID/cmdline|tr '\000' '\n')
    if [ "$2" = -e ]; then
	SCRIPT="$3"
    else
	SCRIPT="$2"
    fi
    case "$SCRIPT" in
	*.postinst|*.preinst|*.postrm|*.prerm)
	    echo "policy-rc.d: scriptlet detected: preventing action $actions on $script" 1>&2
	    exit 101
	    ;;
	*)
	    echo "policy-rc.d: called outside of a scriptlet: action $actions on $script authorized" 1>&2
	    ;;
    esac
elif [ "$actions" != rotate ]; then
    exit 101
fi
