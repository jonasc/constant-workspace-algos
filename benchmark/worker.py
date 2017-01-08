#!/usr/bin/env python3.5
"""Run benchmark jobs received from the central queue manager."""

import signal
from multiprocessing.managers import BaseManager
from statistics import median, StatisticsError
from threading import Event
from threading import Thread

from benchmark import model, config as remote_config
from geometry import PolygonPoint


class QueueManager(BaseManager):
    """Dummy queue manager."""

    pass


class ManagerThread(Thread):
    """Class to manage input from user in a different thread."""

    def __init__(self, *args, **kwargs):
        """Instantiate a new thread."""
        super(ManagerThread, self).__init__(*args, **kwargs)
        self._quit_event = Event()
        self._unpause_event = Event()
        self._unpause_event.set()

    def wait_until_unpaused(self):
        """If paused, wait until the user allows continuation."""
        self._unpause_event.wait()

    def should_quit(self):
        """Return whether the users wants the application to end."""
        return self._quit_event.is_set()

    def run(self):
        """In a loop ask for one of the three options a user can give."""
        while True:
            action = input('[p]ause, [q]uit, [c]ontinue: ').lower()
            if action == 'p':
                print('Pausing this client after computation finishes.')
                self._unpause_event.clear()
            elif action == 'c':
                print('Continuing this client.')
                self._unpause_event.set()
            elif action == 'q':
                print('Shutting down this client after computation finishes.')
                self._quit_event.set()
                self._unpause_event.set()
                return


def timeout(*_, **__):
    """Raise a timeout error."""
    raise TimeoutError()


def compute(polygon, polygon_id, s_id, t_id, s, t, algorithm_list, run_timeout=3600, max_time=5, min_runs=5,
            max_runs=20):
    """Compute the benchmark for one start/end pair in one polygon with all known algorithms."""
    from socket import gethostname
    from datetime import datetime
    from gsp import makestep_shortest_path, delaunay_shortest_path, lee_preparata_shortest_path, \
        trapezoid_shortest_path
    import gc
    import tracemalloc
    import sys
    import traceback
    from time import process_time as timer

    m_run = model.Run.create(polygon_id=polygon_id,
                             host=model.Host.create_or_get(name=gethostname())[0],
                             start=datetime.now(), end=datetime.now(),
                             s=model.PolygonPoint.get(id=s_id), t=model.PolygonPoint.get(id=t_id),
                             version=model.Version.get())
    logging.debug('Created run "%s"', m_run)

    for algorithm, sp in dict(delaunay=delaunay_shortest_path, makestep=makestep_shortest_path,
                              trapezoid=trapezoid_shortest_path, lee_preparata=lee_preparata_shortest_path).items():
        if algorithm not in algorithm_list:
            continue

        m_algorithm, _ = model.Algorithm.create_or_get(name=algorithm)
        logging.info('Running algorithm "%s"', m_algorithm)
        gc.collect()
        tracemalloc.start()
        try:
            signal.alarm(run_timeout)
            path = list(sp(polygon, s, t))
            signal.alarm(0)
        except BaseException:
            traceback.print_exc(file=sys.stderr)
            continue
        else:
            memory = tracemalloc.get_traced_memory()

            gc.collect()
            tracemalloc.stop()

            m_instance = model.Instance.create(run=m_run, algorithm=m_algorithm, memory=memory[1] - memory[0],
                                               path_length=len(path))
            logging.debug('Saved instance "%s"', m_instance)

            logging.debug('Creating resulting path: "%s"', path)
            for i, point in enumerate(path):
                try:
                    m_point = model.Point.get(x=point.x, y=point.y)
                except model.Point.DoesNotExist:
                    for tmp_polygon_point in m_run.polygon.polygon_points:
                        if tmp_polygon_point.point.as_geometry() == point:
                            m_polygon_point = tmp_polygon_point
                            break
                else:
                    m_polygon_point = model.PolygonPoint.get(point=m_point, polygon_id=polygon_id,
                                                             is_vertex=isinstance(point, PolygonPoint))
                model.PathPoint.create(instance=m_instance, index=i, polygon_point=m_polygon_point)

            for property, value in sp.properties.items():
                m_property, _ = model.PropertyName.create_or_get(name=property)
                if isinstance(value, int):
                    model.IntegerProperty.create(instance=m_instance, name=m_property, value=value)

        total_time = 0
        runs = 0

        times = []

        while runs < min_runs or max_time > total_time and runs < max_runs:
            try:
                signal.alarm(run_timeout)
                gc.disable()
                start = timer()
                list(sp(polygon, s, t))
                time = timer() - start
                gc.enable()
                signal.alarm(0)
            except BaseException:
                traceback.print_exc(file=sys.stderr)
                break
            else:
                times.append(time)
                total_time += time
                runs += 1

        if len(times) > 0:
            with model.db.atomic():
                model.Time.insert_many(dict(instance=m_instance, time=t) for t in times).execute()

            m_instance.median_time = median(times)
            m_instance.save()

    m_run.end = datetime.now()
    m_run.save()

    return (polygon_id, s_id, t_id)


if __name__ == '__main__':
    import logging
    import multiprocessing

    signal.signal(signal.SIGALRM, timeout)

    multiprocessing.log_to_stderr(logging.DEBUG)

    logging.basicConfig(level=logging.DEBUG)

    QueueManager.register('get_job_queue')
    QueueManager.register('get_result_queue')
    m = QueueManager(address=(remote_config.host, remote_config.port),
                     authkey=remote_config.authkey)
    m.connect()

    job_queue = m.get_job_queue()
    result_queue = m.get_result_queue()

    jobs = 0

    thread = ManagerThread()
    thread.start()

    while not thread.should_quit():
        thread.wait_until_unpaused()
        if thread.should_quit():
            continue

        jobs += 1
        print('Waiting for new job', jobs, flush=True)
        try:
            args = job_queue.get()
        except Exception as e:
            result_queue.put(e)
            print('Exception thrown: {0}'.format(e))
        else:
            print('Got job:', args, flush=True)
            print('Current job is job', jobs, flush=True)
            try:
                result_queue.put(compute(*args))
                print('Computed job', jobs, flush=True)
            except Exception as e:
                print('Error computing job:', e, flush=True)
                try:
                    result_queue.put(e)
                except Exception as e:
                    print('Error putting error into queue:', e, flush=True)
