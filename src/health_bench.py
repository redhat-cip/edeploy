from health_messages import Health_Message as HM
import health_protocol as HP
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

    def completed(self):
        return

    def none(self):
        return

    def __init__ (self, msg, socket, logger):
        logger.info("INIT BENCH")
        self.message = msg
        self.socket = socket
        self.logger = logger

class Health_CPU(Health_Bench):

    def start(self):
        self.logger.info("Starting CPU Bench for %d seconds" % self.message.running_time)
        time.sleep(self.message.running_time)
        self.completed()
        return


    def stop(self):
        logger.info("Stopping CPU Bench")
        return


    def completed(self):
        HP.send_hm_message(self.socket, HM(HM.MODULE, HM.CPU, HM.COMPLETED))
        return

