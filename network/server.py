# -*- coding: utf-8 -*-

import threading
import xmlrpc

from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn

from helpers import log
import config as cfg
import core
from ai.action import Action


class EnhancedServer(SimpleXMLRPCServer, ThreadingMixIn):
    """ Enhanced XML-RPC Server with some extended/overloaded functions.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quit = None
        self.thread = None

    def serve_forever(self, poll_interval=0.5):
        self.quit = False
        self.encoding = 'utf-8'

        while not self.quit:
            self.handle_request()

        log('Server closed')

    def terminate(self):
        self.quit = True

    def start(self):
        log('Starting server')
        self.thread = threading.Thread(target=self.serve_forever)
        self.thread.start()
        log('Done')

    def __del__(self):
        self.terminate()

    @staticmethod
    def is_server_already_running():
        client = xmlrpc.client.Server(cfg.SERVER_URL, allow_none=True, encoding='utf-8')
        result = False
        try:
            result = client.alive()
        finally:
            return result


class Functions:
    """ Class with XML exported functions.
    """
    @staticmethod
    def alive():
        """ Returns True if the server is alive.
        """
        return True

    @staticmethod
    def close():
        """ Closes the server
        """
        core.BOARD.server.terminate()
        return False

    @staticmethod
    def do_action(action: Action):
        if core.BOARD.current_player.is_network_player:
            core.BOARD.do_action(action)

            if not core.BOARD.finished:
                core.BOARD.next_player()

            return True

        return False  # Not allowed
