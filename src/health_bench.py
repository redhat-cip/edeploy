#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

from health_messages import Health_Message as HM
import health_protocol as HP
import health_libs as HL
import logging


class Health_Bench():
    logger = logging.getLogger(__name__)
    message = HM()
    socket = 0

    def start(self):
        return

    def stop(self):
        return

    def none(self):
        return

    def notcompleted(self, module):
        self.message.message = HM.MODULE
        self.message.module = module
        self.message.action = HM.NOTCOMPLETED
        HP.send_hm_message(self.socket, self.message)

    def completed(self, module):
        self.message.message = HM.MODULE
        self.message.module = module
        self.message.action = HM.COMPLETED
        HP.send_hm_message(self.socket, self.message)

    def starting(self, module):
        self.message.message = HM.MODULE
        self.message.module = module
        self.message.action = HM.STARTING
        HP.send_hm_message(self.socket, self.message)

    def __init__(self, msg, socket, logger):
        logger.info("INIT BENCH")
        self.message = msg
        self.socket = socket
        self.logger = logger


class Health_CPU(Health_Bench):

    def start(self):
        self.logger.info("Starting CPU Bench for %d seconds" %
                         self.message.running_time)
        self.starting()
        HL.run_sysbench(self.message.hw, self.message.running_time,
                        self.message.cpu_instances)
        self.completed()

    def starting(self):
        Health_Bench.starting(self, HM.CPU)

    def stop(self):
        self.logger.info("Stopping CPU Bench")

    def notcompleted(self):
        Health_Bench.notcompleted(self, HM.CPU)

    def completed(self):
        Health_Bench.completed(self, HM.CPU)
