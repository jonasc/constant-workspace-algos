#!/usr/bin/env python3.5
"""Runs a distributed queue manager."""
import logging
import multiprocessing
import queue
from multiprocessing.managers import BaseManager


class QueueManager(BaseManager):
    """Dummy queue manager."""

    pass


if __name__ == '__main__':

    multiprocessing.log_to_stderr(logging.DEBUG)

    job_queue = queue.Queue()
    result_queue = queue.Queue()

    print('Setting up manager.', flush=True)

    QueueManager.register('get_job_queue', callable=lambda: job_queue)
    QueueManager.register('get_result_queue', callable=lambda: result_queue)
    m = QueueManager(address=('', 50000), authkey=b'abracadabra')
    print('Everything ist set up.', flush=True)
    s = m.get_server()
    print('Serving forever.', flush=True)
    s.serve_forever()
