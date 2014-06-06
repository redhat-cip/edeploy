class Health_Message():
    protocol_version = 0
    
    INVALID = 0
    NONE = 1 << 0
    DISCONNECTED = 1 << 1

    STOP = 1 << 1
    START = 1 << 2
    COMPLETED = 1 << 3
    NOTCOMPLETED = 1 << 4

    CONNECT = 1 << 1
    DISCONNECT = 1 << 2 
    ACK = 1 << 3
    NACK = 1 << 4
    MODULE = 1 << 5
    
    CPU = 1 << 1
    STORAGE = 1 << 2
    MEMORY = 1 << 3
    NETWORK = 1 << 4

    message_string = {NONE: 'NONE', CONNECT: 'CONNECT', DISCONNECT: 'DISCONNECT', ACK: 'ACK', NACK: 'NACK', MODULE: 'MODULE'}
    module_string = {NONE: 'NONE', CPU: 'CPU', STORAGE:'STORAGE', MEMORY:'MEMORY', NETWORK:'NETWORK'}
    action_string = {NONE: 'NONE', STOP: 'STOP', START: 'START', COMPLETED: 'COMPLETED', NOTCOMPLETED: 'NOTCOMPLETED'}
    message = NONE
    action = NONE 
    module = NONE

    need_ack = False
    hw = []

    running_time = 0
    cpu_instances = 0


    def get_message_list(self):
        return [self.NONE, self.CONNECT, self.DISCONNECT, self.ACK, self.NACK, self.MODULE]


    def get_action_list(self):
        return [self.NONE, self.STOP, self.START, self.COMPLETED, self.NOTCOMPLETED]


    def get_module_list(self):
        return [self.NONE, self.CPU, self.STORAGE, self.MEMORY, self.NETWORK]


    def is_valid(self):
        for msg in self.get_message_list():
            if self.message & msg == msg:
                return True
        return False


    def __init__ (self, message = NONE, module = NONE, action = NONE):
        self.message = message
        self.module = module
        self.action = action


    def get_message_type(self):
        return self.message_string[self.message]

    def get_action_type(self):
        return self.action_string[self.action]

    def get_module_type(self):
        return self.module_string[self.module]
