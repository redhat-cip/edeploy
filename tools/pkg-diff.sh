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
PKG_LIST=

IFS=$'\n'
for list in $OLD_LIST $NEW_LIST;do
      for pkg in `cat $list`; do
          PKG_NAME=$(echo $pkg | awk '{print $1}')
          PKG_VERSION=$(echo $pkg | awk '{print $2}')
          PKG_LIST="${PKG_LIST}\n${list} ${PKG_NAME} ${PKG_VERSION}"
      done
done

echo -e ${PKG_LIST} > all_pkg
old_package_names=$(grep $OLD_LIST all_pkg | awk '{print $2}')
new_package_names=$(grep $NEW_LIST all_pkg | awk '{print $2}')

new_pkg() {
  for pkg in $new_package_names; do
      if ! echo $old_package_names | grep -w "\<$pkg\>"; then
          echo "$pkg"
      fi
  done
}

deleted_pkg() {
  for pkg in $old_package_names; do
      if ! echo $new_package_names | grep -w "\<$pkg\>"; then
          echo "$pkg"
      fi
  done
}

version_pkg() {
  for pkg in $new_package_names; do
      old_version=$(grep $pkg $OLD_LIST | awk '{print $2}')
      new_version=$(grep $pkg $NEW_LIST | awk '{print $2}')
      if [ -n $old_version ] && [ "$old_version" != "$new_version" ]; then
          echo "old: $pkg $old_version"
          echo "new: $pkg $new_version"
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
rm all_pkg
