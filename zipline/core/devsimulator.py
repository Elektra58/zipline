"""
Simulator hosts all the components necessary to execute a simulation.
See :py:method""
"""

import threading
from zipline.core.simulatorref import SimulatorBase

class AddressAllocator(object):
    """
    Produces a iterator of 10000 sockets to allocate as needed.
    Emulates the API of Qexec's socket allocator.
    """

    def __init__(self, ns):
        self.idx = 0
        self.sockets = [
            'tcp://127.0.0.1:%s' % (10000 + n)
            for n in xrange(ns)
        ]

    def lease(self, n):
        sockets = self.sockets[self.idx:self.idx+n]
        self.idx += n
        return sockets

    def reaquire(self, *conn):
        pass


class Simulator(SimulatorBase):

    zmq_flavor = 'thread'

    def __init__(self, addresses):
        # TODO: rethink this
        SimulatorBase.__init__(self, addresses)
        self.subthreads = []
        self.running = False

    @property
    def get_id(self):
        return 'Simple Simulator'

    def launch_controller(self):
        thread = threading.Thread(
            target=self.controller.run,
        )
        thread.start()

        self.subthreads.append(thread)
        return thread

    def simulate(self):
        thread = threading.Thread(target=self.run)
        thread.start()

        self.subthreads.append(thread)
        self.running = True

        return thread

    def did_clean_shutdown(self):
        return not any([t.isAlive() for t in self.subthreads])

    def shutdown(self):
        """
        Destroy all tracked components.
        """

        if not self.running:
            return


        for component in self.components.itervalues():
            component.shutdown()

        for thread in self.subthreads:
            if thread.is_alive():
                thread._Thread__stop()

        #self.controller.shutdown()

        self.running = False

        assert self.did_clean_shutdown()

    def launch_component(self, component):
        thread = threading.Thread(target=component.run)
        thread.start()

        self.subthreads.append(thread)
        return thread