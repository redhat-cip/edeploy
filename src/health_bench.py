from health_messages import Health_Message as HM
import health_protocol as HP
import health_libs as HL
import logging
import time

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

    def __init__ (self, msg, socket, logger):
        logger.info("INIT BENCH")
        self.message = msg
        self.socket = socket
        self.logger = logger

class Health_CPU(Health_Bench):

    def start(self):
        self.logger.info("Starting CPU Bench for %d seconds" % self.message.running_time)
        HL.run_sysbench(self.message.hw, self.message.running_time, self.message.cpu_instances)
        self.completed()

    def stop(self):
        logger.info("Stopping CPU Bench")

    def notcompleted(self):
        Health_Bench.notcompleted(self, HM.CPU)

    def completed(self):
        Health_Bench.completed(self, HM.CPU)

