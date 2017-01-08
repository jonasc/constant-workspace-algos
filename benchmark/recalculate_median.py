#!/usr/bin/env python3.5
"""Calculate median value if not (yet) available."""
from statistics import median

from benchmark.model import Instance, Time


def main():
    """Main function."""
    instances = Instance.select(Instance, Time).join(Time).where(Instance.median_time == 0)

    no_instances = 0
    all_instances = instances.count()

    for instance in instances:
        no_instances += 1
        print('{0}%'.format(no_instances / all_instances * 100))
        if instance.times.count() > 0:
            instance.median_time = median(t.time for t in instance.times)
            instance.save()


if __name__ == '__main__':
    main()
