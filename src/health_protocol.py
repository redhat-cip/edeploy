import logging
import pickle
import socket
import struct
import zlib
import time
from health_messages import Health_Message as HM
logger = 0
hdlr = 0
formatter = 0

def start_log(filename, level=logging.INFO):
    global logger
    global hdlr
    global formatter
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler(filename)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(level)
    logger.info('Starting logger')


def send_hm_message(sock, data, need_ack=False):
    global logger
    data.need_ack = need_ack
    logger.debug("Sent %s/%s/%s to %s (need_ack=%r)" % (data.get_message_type(), data.get_module_type(), data.get_action_type(), sock.getpeername(), data.need_ack))
    to_be_sent = zlib.compress(pickle.dumps(data))
    sock.sendall(struct.pack('!I', len(to_be_sent)))
    sock.sendall(to_be_sent)
    if data.need_ack is True:
        msg = HM()
        while True:
            logger.debug("Waiting for ACK")
            try:
                msg = recv_hm_message(sock)
            except Exception as e:
                logger.error("Broken socket, exiting")
                break;

            if (msg.message == HM.ACK):
                logger.debug("Got ACK, exiting")
                break;
            if (msg.message == HM.NACK):
                logger.error("Received NACK from %s on message %s" % (sock.getpeername(), (data.get_message_type())))
                break;


def recv_hm_message(sock):
    global logger
    try:
        lengthbuf = recvall(sock, 4)
    except socket.error as (errno, v):
        if errno == 9:
            return HM(HM.DISCONNECTED)
        logger.error(v)
        return HM(HM.INVALID)

    try:
        length = struct.unpack('!I', lengthbuf)
    except Exception as e:
        logger.error("Received incomplete message")
        return HM(HM.INVALID)

    msg = pickle.loads(zlib.decompress(recvall(sock, int(length[0]))))
    if msg.is_valid() is False:
        logger.error("Message %d is not part of the valid message_list" % msg.message)
        if (msg.need_ack is True) and (msg.message != HM.DISCONNECT):
            send_hm_message(sock, HM(HM.NACK), False)
        msg.message = HM.INVALID
    else:
        logger.debug("Received %s/%s/%s from %s (need_ack=%r)" % (msg.get_message_type(), msg.get_module_type(), msg.get_action_type(), sock.getpeername(), msg.need_ack))
        if (msg.need_ack is True) and (msg.message != HM.DISCONNECT):
            send_hm_message(sock, HM(HM.ACK), False)
    return msg


def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf
