#!/bin/bash
#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Author: Emilien Macchi <emilien.macchi@enovance.com>
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
#
# Compare two list of packages and show the differences.
# Expected syntax of file:
# <package_name> <version>-<release>
#
# Use:
# diff-pkg old.packages new.packages
#
# To generate the list of packages:
# * Red Hat / CentOS: rpm -qa --queryformat '%{NAME} %{VERSION}-%{RELEASE}'
# * Debian / Ubuntu: dpkg -l | grep '^ii' | awk '{print $2 "\t" $3}'
#

if [ ! $# -eq 2 ]; then
  echo "Usage: $0 old.packages new.packages" 1>&2
  exit 1
fi

OLD_LIST=$1
NEW_LIST=$2

IFS=$'\n'

new_pkg() {
  for pkg in `cat $NEW_LIST | awk '{print $1}'`; do
      grep -qw "\<$pkg\>" $OLD_LIST || echo "$pkg" | awk '{print $1}'
  done
}

deleted_pkg() {
  for pkg in `cat $OLD_LIST | awk '{print $1}'`; do
      grep -qw "\<$pkg\>" $NEW_LIST || echo "$pkg" | awk '{print $1}'
  done
}

version_pkg() {
  printf '%-35s %25s %25s\n' "Package name" "Previous version" "Newer version"
  printf '%-35s %-25s %-25s\n' "-------------------------" "-------------------------" "-------------------------"
  for pkg in `cat $NEW_LIST | awk '{print $1}'`; do
      old_version=$(grep -w "^\<$pkg\> .*" $OLD_LIST 2>&1 | awk '{print $2}')
      new_version=$(grep -w "^\<$pkg\> .*" $NEW_LIST 2>&1 | awk '{print $2}')
      # If the package was not existing in previous relase
      # Let's add a N/A as the previous version, and show the new one in new_version
      if [ -z "$old_version" ]; then
         old_version="N/A"
      fi

      if [ "$old_version" != "$new_version" ]; then
          printf '%-35s %25s %25s\n' "$pkg" "$old_version" "$new_version"
      fi
  done
}

echo "### New Packages ###"
new_pkg
echo
echo "### Deleted Packages ###"
deleted_pkg
echo
echo "### Version changes ###"
version_pkg

# cleanup
unset IFS
