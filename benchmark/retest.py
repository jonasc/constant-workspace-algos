#!/usr/bin/env python3.5
"""Retest runs with strangely high memory consumption."""
import gc
import signal
import sys
import traceback
import tracemalloc

from benchmark.model import Algorithm, Instance, Point, PolygonPoint, Run
from geometry.polygons import polygon_from_database
from gsp import delaunay_shortest_path, lee_preparata_shortest_path, makestep_shortest_path, trapezoid_shortest_path

algorithms = dict(delaunay=delaunay_shortest_path, makestep=makestep_shortest_path, trapezoid=trapezoid_shortest_path,
                  lee_preparata=lee_preparata_shortest_path)


def timeout(*_, **__):
    """Raise a timeout error."""
    raise TimeoutError()


def main():
    """Main function."""
    signal.signal(signal.SIGALRM, timeout)

    # logging.basicConfig(level=logging.DEBUG)

    # polygons = Polygon.select(Polygon.id).join(PolygonType).where(PolygonType.name == 'pathological_01')

    high_runs = (Instance
                 .select(Instance, Algorithm, Run)
                 .join(Algorithm)
                 .switch(Instance)
                 .join(Run)
                 .where(Instance.memory > 10000)
                 .order_by(Run.polygon, -Instance.memory, Instance.id))

    polygon_id = None
    polygon = None

    for instance in high_runs:
        if polygon is None or polygon_id != instance.run.polygon_id:
            polygon_id = instance.run.polygon_id
            polygon = polygon_from_database(polygon_id, triangulated=True)
            print('\n##### New polygon {id:4d} #####'.format(id=polygon_id))

        print('Run {run:8d}, memory {memory:8d}, algorithm {algorithm}.'.format(run=instance.run.id,
                                                                                memory=instance.memory,
                                                                                algorithm=instance.algorithm.name))

        s_and_t = (PolygonPoint.select(PolygonPoint, Point).join(Point)
                   .where(PolygonPoint.id << (instance.run.s_id, instance.run.t_id)))

        s, t = None, None
        for p in s_and_t:
            if p.id == instance.run.s_id:
                s = p.point.as_geometry()
            if p.id == instance.run.t_id:
                t = p.point.as_geometry()

        if s is None or t is None:
            print(s, t)
            print(list(s_and_t))
            print(instance.run)
            sys.exit(10)

        gc.collect()
        tracemalloc.start()
        try:
            signal.alarm(3600)
            path = list(algorithms[instance.algorithm.name](polygon, s, t))
            signal.alarm(0)
        except KeyboardInterrupt:
            return
        except BaseException:
            traceback.print_exc(file=sys.stderr)
            continue
        else:
            memory = tracemalloc.get_traced_memory()
            memory = memory[1] - memory[0]
            print(' ' * 10 + 'new memory {memory:8d}'.format(memory=memory))
            del path

            gc.collect()
            tracemalloc.stop()

            if memory < instance.memory:
                instance.memory = memory
                instance.save()

                print('>' * 6 + ' UPDATED!')


if __name__ == '__main__':
    main()
