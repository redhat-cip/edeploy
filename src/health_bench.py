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

    def initialize(self):
        return

    def clean(self):
        return

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
        HL.check_mce_status(self.message.hw)
        HP.send_hm_message(self.socket, self.message)

    def completed(self, module):
        self.message.message = HM.MODULE
        self.message.module = module
        self.message.action = HM.COMPLETED
        HL.check_mce_status(self.message.hw)
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
        HL.run_sysbench_cpu(self.message.hw, self.message.running_time,
                self.message.cpu_instances)
        self.completed()

    def initialize(self):
        Health_Bench.initialize(self, HM.CPU)

    def clean(self):
        Health_Bench.clean(self, HM.CPU)

    def starting(self):
        Health_Bench.starting(self, HM.CPU)

    def stop(self):
        self.logger.info("Stopping CPU Bench")

    def notcompleted(self):
        Health_Bench.notcompleted(self, HM.CPU)

    def completed(self):
        Health_Bench.completed(self, HM.CPU)


class Health_MEMORY(Health_Bench):

    def start(self):
        self.logger.info("Starting Memory Bench for %d seconds with blocksize=%s" %
                         (self.message.running_time, self.message.block_size))
        self.starting()
        HL.run_sysbench_memory(self.message)
        self.completed()

    def initialize(self):
        Health_Bench.initialize(self, HM.MEMORY)

    def clean(self):
        Health_Bench.clean(self, HM.MEMORY)

    def starting(self):
        Health_Bench.starting(self, HM.MEMORY)

    def stop(self):
        self.logger.info("Stopping Memory Bench")

    def notcompleted(self):
        Health_Bench.notcompleted(self, HM.MEMORY)

    def completed(self):
        Health_Bench.completed(self, HM.MEMORY)


class Health_NETWORK(Health_Bench):

    def initialize(self):
        self.logger.info("Starting init for %s Network Bench " %
                         (self.message.network_test))
        HL.start_netservers(self.message)
        self.completed()

    def clean(self):
        self.logger.info("Cleaning for %s Network Bench " %
                         (self.message.network_test))
        HL.stop_netservers(self.message)
        self.completed()

    def start(self):
        self.logger.info("Starting Network Bench (%s mode) for %d seconds with blocksize=%s" %
                         (self.message.network_test, self.message.running_time, self.message.block_size))
        self.starting()
        HL.run_network_bench(self.message)
        self.completed()

    def starting(self):
        Health_Bench.starting(self, HM.NETWORK)

    def stop(self):
        self.logger.info("Stopping Network Bench")

    def notcompleted(self):
        Health_Bench.notcompleted(self, HM.NETWORK)

    def completed(self):
        Health_Bench.completed(self, HM.NETWORK)


class Health_STORAGE(Health_Bench):

    def start(self):
        self.logger.info("Starting Storage Bench for %d seconds with blocksize=%s" %
                         (self.message.running_time, self.message.block_size))
        self.starting()
        HL.run_fio_job(self.message)
        self.completed()

    def initialize(self):
        Health_Bench.initialize(self, HM.STORAGE)

    def clean(self):
        Health_Bench.clean(self, HM.STORAGE)

    def starting(self):
        Health_Bench.starting(self, HM.STORAGE)

    def stop(self):
        self.logger.info("Stopping Storage Bench")

    def notcompleted(self):
        Health_Bench.notcompleted(self, HM.STORAGE)

    def completed(self):
        Health_Bench.completed(self, HM.STORAGE)
