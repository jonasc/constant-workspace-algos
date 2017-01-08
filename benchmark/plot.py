#!/usr/bin/env python3.5
"""Plot results from benchmark runs."""
import argparse
import json
import logging
import os.path
import re
import sys
from datetime import date
from numbers import Number

import numpy as np
from matplotlib import pyplot as plt
from numpy.linalg import LinAlgError
from peewee import DoesNotExist, SQL, fn
from scipy.optimize import curve_fit

from benchmark.executer import config
from benchmark.model import Algorithm, Instance, IntegerProperty, Polygon, PolygonType, PropertyName, Run, Time, Version


def logarithmic(x, a, b, c):
    """Calculate a*log(b*x)+c."""
    return a * np.log(b * x) + c


def square_root(x, a, b):
    """Calculate a*sqrt(x)+b."""
    return a * np.sqrt(x) + b


def const(x, a):
    """Return constant a."""
    # The following is a fix so that we return as many values as x contains
    return a + x - x


def linear(x, a, b):
    """Calculate a*x+b."""
    return a * x + b


def squared(x, a, b, c):
    """Calculate a*x²+b*x+c."""
    return a * x * x + b * x + c


def cubed(x, a, b, c, d):
    """Calculate a*x³+b*x²+c*x+d."""
    return a * x * x * x + b * x * x + c * x + d


violin_plot_parts = ('cmeans', 'cmedians', 'cmins', 'cmaxes', 'cbars')
plot_colors = dict(delaunay='red', makestep='green', trapezoid='blue', lee_preparata='orange')
units = {
    'i.jarvis_marches': '# of jarvis marches',
    'i.iterations': '# of iterations of the main loop',
    'time': 'time in seconds',
    'memory': 'memory in bytes',
    'memory-time': 'memory×time in byteseconds',
    'size': '# of vertices',
}

fitting = {
    'time': {
        'x': dict(func=linear, draw_style=(0, (4, 2)),
                  algorithms=('lee_preparata',),
                  label='${a:.5f}\cdot x+{b:.5f}$',
                  plot='{a:.12f}*x+{b:.12f}'),
        'x²': dict(func=squared, draw_style=(0, (8, 4)),
                   algorithms=('makestep', 'trapezoid', 'delaunay',),
                   label='${a:.6f}\cdot x^2+{b:.5f}\cdot x+{c:.5f}$',
                   dump_algorithms=('makestep', 'trapezoid',),
                   plot='{a:.12f}*x^2+{b:.12f}*x+{c:.12f}'),
        'x³': dict(func=cubed, draw_style=(0, (12, 6)),
                   algorithms=('makestep', 'trapezoid', 'delaunay',),
                   label='${a:.7f}\cdot x^3+{b:.6f}\cdot x^2+{c:.5f}\cdot x+{d:.5f}$',
                   dump_algorithms=('delaunay',),
                   plot='{a:.12f}*x^3+{b:.12f}*x^2+{c:.12f}*x+{d:.12f}')
    },
    'memory': {
        'c': dict(func=const, draw_style=(0, (4, 2)),
                  algorithms=('makestep', 'trapezoid', 'delaunay',),
                  label='${a:.3f}$',
                  plot='{a:.12f}'),
        'x': dict(func=linear, draw_style=(0, (4, 2)),
                  algorithms=('lee_preparata',),
                  label='${a:.3f}\cdot x+{b:.3f}$',
                  plot='{a:.12f}*x+{b:.12f}'),
        'log(x)': dict(func=logarithmic, draw_style=(0, (12, 6)),
                       algorithms=('makestep', 'trapezoid', 'delaunay',),
                       label='${a:.1f}\cdot\log({b:.1f}\cdot x)+{c:.1f}$',
                       dump_algorithms=(),
                       plot='{a:.12f}*log({b:.12f}*x)+{c:.12f}'),
        # 'sqrt(x)': dict(func=square_root, draw_style=(0, (6, 3)),
        #                 algorithms=('makestep', 'trapezoid', 'delaunay', 'lee_preparata'),
        #                 label='${a:.1f}\cdot\sqrt{{x}}+{b:.1f}$')
    },
    'memory-time': {
        'x': dict(func=linear, draw_style=(0, (4, 2)),
                  algorithms=('lee_preparata',),
                  label='${a:.5f}\cdot x+{b:.5f}$',
                  plot='{a:.12f}*x+{b:.12f}'),
        'x²': dict(func=squared, draw_style=(0, (8, 4)),
                   algorithms=('makestep', 'trapezoid', 'delaunay', 'lee_preparata',),
                   label='${a:.6f}\cdot x^2+{b:.5f}\cdot x+{c:.5f}$',
                   plot='{a:.12f}*x^2+{b:.12f}*x+{c:.12f}'),
        'x³': dict(func=cubed, draw_style=(0, (12, 6)),
                   algorithms=('makestep', 'trapezoid', 'delaunay',),
                   label='${a:.7f}\cdot x^3+{b:.6f}\cdot x^2+{c:.5f}\cdot x+{d:.5f}$',
                   plot='{a:.12f}*x^3+{b:.12f}*x^2+{c:.12f}*x+{d:.12f}')
    },
    'i.ignores': {
        'x': dict(func=linear, draw_style=(0, (4, 2)),
                  algorithms=('trapezoid',),
                  label='${a:.5f}\cdot x+{b:.5f}$',
                  plot='{a:.12f}*x+{b:.12f}'),
        'x²': dict(func=squared, draw_style=(0, (8, 4)),
                   algorithms=('trapezoid',),
                   label='${a:.6f}\cdot x^2+{b:.5f}\cdot x+{c:.5f}$',
                   plot='{a:.12f}*x^2+{b:.12f}*x+{c:.12f}'),
    }
}


def fit(x_values, y_values, algorithm, type, file, plottype='medianplot'):
    """Fit the data to some predefined functions, depending on algorithm and type."""
    if type not in fitting:
        logging.info('Cannot fit type "%s".', type)
        return

    for name, options in fitting[type].items():
        if algorithm not in options['algorithms']:
            continue

        try:
            popt, pcov = curve_fit(options['func'], x_values, y_values, absolute_sigma=True)
        except TypeError:
            continue

        params = dict(zip('abcdefghijklmnopqrstuvwxyz', popt))
        logging.debug('Plotting %s for %s:', name, algorithm)
        logging.debug('\t' + str(x_values))
        logging.debug('\t' + str(options['func'](np.array(x_values), **params)))
        plt.gca().plot(x_values, options['func'](np.array(x_values), **params), color=plot_colors[algorithm],
                       linestyle=options['draw_style'], linewidth=1.5,
                       label=algorithm[:1] + 'fitted: ' + options['label'].format(**params))
        if file:
            if 'dump_algorithms' in options and algorithm not in options['dump_algorithms']:
                continue
            function = options['plot'].format(**params)
            file.write('\\addplot[{type},{algorithm},domain=0:{upper}] {{{function}}};\n'.format(
                type=plottype, algorithm=algorithm.replace('_', ''), upper=max(x_values), function=function))


def get_y_values(y, y_low, y_high, algorithm, version_constraint, with_ignored, type_):
    """Build a database (sub-)query to fetch y-values in a generic manner."""
    logging.info('Building up y-values.')
    y_values = None
    if '.' in y:
        parts = y.split('.')
        if len(parts) != 2:
            logging.critical('I do not know how to interpret y-values "%s".', y)
            return 1

        property_class = None
        if parts[0] == 'i':
            property_class = IntegerProperty

        if property_class is None:
            logging.critical('Prefix "%s" is unknown.', parts[0])
            return 1

        try:
            property = PropertyName.get(PropertyName.name == parts[1])
        except DoesNotExist:
            logging.critical('Property "%s" is unknown.', parts[1])
            return 1

        y_values = (property_class
                    .select(Instance.run, Instance.algorithm,
                            property_class.value.alias('y'))
                    .join(Instance)
                    .join(Run)
                    .where(Instance.algorithm == algorithm, property_class.name == property, version_constraint)
                    )

        if y_low is not None:
            y_values = y_values.where(property_class.value >= y_low)
        if y_high is not None:
            y_values = y_values.where(property_class.value <= y_high)

        y_values = (y_values
                    .order_by()
                    .alias('y_values')
                    )
    elif y == 'time':
        y_values = (Instance
                    .select(Instance.run, Instance.algorithm, Instance.median_time.alias('y'))
                    .join(Run)
                    .where(Instance.algorithm == algorithm, version_constraint)
                    )

        if y_low is not None:
            y_values = y_values.where(Time.time >= y_low)
        if y_high is not None:
            y_values = y_values.where(Time.time <= y_high)

        y_values = (y_values
                    .order_by()
                    .alias('y_values')
                    )
    elif y == 'memory':
        y_values = (Instance
                    .select(Instance.run, Instance.algorithm, Instance.memory.alias('y'))
                    .join(Run)
                    .where(Instance.algorithm == algorithm, version_constraint)
                    )

        if y_low is not None:
            y_values = y_values.where(Instance.memory >= y_low)
        if y_high is not None:
            y_values = y_values.where(Instance.memory <= y_high)

        y_values = (y_values
                    .order_by()
                    .alias('y_values')
                    )
    elif y == 'memory-time':
        y_values = (Instance
                    .select(Instance.run, Instance.algorithm, (Instance.memory * Instance.median_time).alias('y'))
                    .join(Run)
                    .where(Instance.algorithm == algorithm, version_constraint)
                    )

        if y_low is not None:
            y_values = y_values.having(SQL('y') >= y_low)
        if y_high is not None:
            y_values = y_values.having(SQL('y') <= y_high)

        y_values = (y_values
                    .order_by()
                    .alias('y_values')
                    )
    elif y == 'path':
        y_values = (Instance
                    .select(Instance.run, Instance.algorithm, Instance.path_length.alias('y'))
                    .join(Run)
                    .where(Instance.algorithm == algorithm, version_constraint)
                    )

        if y_low is not None:
            y_values = y_values.where(Instance.path_length >= y_low)
        if y_high is not None:
            y_values = y_values.where(Instance.path_length <= y_high)

        y_values = (y_values
                    .order_by()
                    .alias('y_values')
                    )

    return y_values


def get_x_values(x, x_low, x_high, algorithm, version_constraint, with_ignored, m_type, y_values):
    """Build a database (sub-)query to fetch x-values in a generic manner."""
    logging.info('Building up x-values.')
    x_values = None
    if x == 'size':
        x_values = (Run
                    .select(Run.id, fn.Avg(Polygon.size).alias('x'), y_values.c.y, y_values.c.algorithm_id)
                    .join(Polygon)
                    .where(Polygon.type == m_type, version_constraint)
                    .order_by()
                    .alias('t1')
                    )

        if x_low is not None:
            x_values = x_values.where(Polygon.size >= x_low)
        if x_high is not None:
            x_values = x_values.where(Polygon.size <= x_high)
    elif x == 'path':
        x_values = (Run
                    .select(Run.id, fn.Avg(Instance.path_length).alias('x'), y_values.c.y, y_values.c.algorithm_id)
                    .join(Polygon)
                    .switch(Run)
                    .join(Instance)
                    .where(Polygon.type == m_type, version_constraint)
                    .order_by()
                    .alias('t1')
                    )

        if x_low is not None:
            x_values = x_values.where(Instance.path_length >= x_low)
        if x_high is not None:
            x_values = x_values.where(Instance.path_length <= x_high)
    elif '.' in x:
        parts = x.split('.')
        if len(parts) != 2:
            logging.critical('I do not know how to interpret x-values "%s".', x)
            return 1

        property_class = None
        if parts[0] == 'i':
            property_class = IntegerProperty

        if property_class is None:
            logging.critical('Prefix "%s" is unknown.', parts[0])
            return 1

        try:
            property = PropertyName.get(PropertyName.name == parts[1])
        except DoesNotExist:
            logging.critical('Property "%s" is unknown.', parts[1])
            return 1

        x_values = (Run
                    .select(Run.id, fn.Avg(property_class.value).alias('x'), y_values.c.y, y_values.c.algorithm_id)
                    .join(Instance)
                    .join(property_class)
                    .switch(Run)
                    .join(Polygon)
                    .where(Instance.algorithm == algorithm, property_class.name == property,
                           Polygon.type == m_type, version_constraint)
                    .order_by()
                    .alias('t1')
                    )

        if x_low is not None:
            x_values = x_values.where(property_class.value >= x_low)
        if x_high is not None:
            x_values = x_values.where(property_class.value <= x_high)

    return x_values


def database_source(x, y, x_low, x_high, y_low, y_high, algorithm, version_constraint, with_ignored, m_type):
    """Load data for algorithm from database."""
    y_values = get_y_values(y, y_low, y_high, algorithm, version_constraint, with_ignored, m_type)

    if y_values is None:
        logging.critical('No y-values retrieved.')
        sys.exit(1)

    logging.debug('This is y_values: %s', y_values)

    x_values = get_x_values(x, x_low, x_high, algorithm, version_constraint, with_ignored, m_type, y_values)

    if x_values is None:
        logging.critical('No x-values retrieved.')
        sys.exit(1)

    logging.debug('This is x_values: %s', x_values)

    logging.info('Joining both queries.')
    data = (x_values
            .join(y_values, on=x_values.c.id == y_values.c.run_id)
            .group_by(x_values.c.id, y_values.c.y, y_values.c.algorithm_id)
            .order_by(y_values.c.algorithm_id, SQL('x'))
            )

    x = None
    all_y = []
    for datum in data.iterator():
        if x is None:
            x = datum.x
        elif x != datum.x:
            yield x, all_y

            x = datum.x
            all_y = []

        all_y.append(datum.y)

    if x is not None:
        yield x, all_y


def file_source(file, algorithm_name):
    """Load data for algorithm from given file."""
    with open(file, 'r') as f:
        curr = False
        x = None
        for l in f:
            obj = json.loads(l)
            if isinstance(obj, str):
                curr = obj == algorithm_name
                continue
            if not curr:
                continue

            if isinstance(obj, Number):
                x = obj
            elif isinstance(obj, list):
                yield x, obj


def main(x, y, without=(), show=(), img_prefix=None, x_low=None, x_high=None, y_low=None, y_high=None,
         with_ignored=False, violin_width=3, alpha=0.3, type_=None, versions=None, dump=None, in_file=None):
    """Plot results from benchmark runs."""
    plt.figure(figsize=(30, 20))
    plt.gcf().clear()
    plt.grid(True)

    algorithms = Algorithm.select()
    if show:
        algorithms = algorithms.where(Algorithm.name << show)
    elif without:
        algorithms = algorithms.where(~(Algorithm.name << without))

    if versions is None:
        version_constraint = True
    elif isinstance(versions, Version):
        version_constraint = Run.version == versions
    elif isinstance(versions, list):
        version_constraint = Run.version << versions
    else:
        logging.error('Supplied version(s) are not valid')
        return 2

    m_type = PolygonType.get(name=type_)

    logging.info('Starting to retrieve data from database.')

    biggest_all_x = None

    file = None
    tex_file = None
    if dump:
        if img_prefix:
            file_name = '.'.join(
                [img_prefix, type_, '{x}-{y}'.format(x=x, y=y),
                 ','.join(sorted(algorithm.name for algorithm in algorithms))
                 ]
            )
        else:
            file_name = '.'.join(
                [type_, '{x}-{y}'.format(x=x, y=y),
                 ','.join(sorted(algorithm.name for algorithm in algorithms))
                 ]
            )
        if x_low is not None:
            file_name += '.x>=' + str(x_low)
        if x_high is not None:
            file_name += '.x<=' + str(x_high)
        if y_low is not None:
            file_name += '.y>=' + str(y_low)
        if y_high is not None:
            file_name += '.y<=' + str(y_high)
        tex_file_name = file_name + '.tex'
        file_name += '.data'
        try:
            file = open(file_name, 'w')
        except OSError:
            logging.critical('Cannot open file "%s" to dump to.', file_name)
            file = None
        try:
            tex_file = open(tex_file_name, 'w')
        except OSError:
            logging.critical('Cannot open file "%s" to dump to.', tex_file_name)
            tex_file = None

    for algorithm in algorithms:
        if file:
            file.write(json.dumps(algorithm.name))
            file.write('\n')

        logging.info('Looking at algorithm "%s" (%d)', algorithm.name, algorithm.id)

        all_x = []
        median_values = []
        max_values = []

        if in_file is not None:
            data_source = file_source(in_file, algorithm.name)
        else:
            data_source = database_source(x, y, x_low, x_high, y_low, y_high, algorithm, version_constraint,
                                          with_ignored, m_type)

        logging.info('Retrieving data.')
        for curr_x, all_y in data_source:
            if file:
                file.write(json.dumps(curr_x))
                file.write('\n')
                file.write(json.dumps(all_y))
                file.write('\n')

            all_x.append(curr_x)
            median_values.append(np.median(all_y))
            max_values.append(np.max(all_y))

            logging.debug('Plotting algorithm "%s" and x-data "%s".', algorithm.name, curr_x)

            try:
                # Plot next violin
                plot = plt.gca().violinplot(all_y, positions=[curr_x], showmeans=True, showmedians=True,
                                            widths=violin_width)

                for obj in plot['bodies']:
                    obj.set_color(plot_colors[algorithm.name])
                    obj.set_alpha(alpha)
                for part in violin_plot_parts:
                    plot[part].set_color(plot_colors[algorithm.name])
                    plot[part].set_alpha(alpha)
            except (ValueError, LinAlgError):
                logging.debug('Special plotting algorithm "%s", x-data "%s", y-data "%s".', algorithm.name, curr_x,
                              all_y)
                plt.gca().plot([curr_x], [all_y[0]], color=plot_colors[algorithm.name], marker='x')

        if median_values:
            logging.debug('Plotting mean data for algorithm "%s".', algorithm.name)
            plt.gca().plot(all_x, median_values, color=plot_colors[algorithm.name], label=algorithm.name + ' median')

            fit(all_x, median_values, algorithm.name, y, tex_file)

        if max_values:
            logging.debug('Plotting max data for algorithm "%s".', algorithm.name)
            plt.gca().plot(all_x, max_values, color=plot_colors[algorithm.name], label=algorithm.name + ' median',
                           alpha=alpha)

            fit(all_x, max_values, algorithm.name, y, tex_file, 'maxplot')

        if biggest_all_x is None or len(all_x) > len(biggest_all_x):
            biggest_all_x = all_x

    plt.gca().set_xticks(biggest_all_x)

    if file:
        file.close()
    if tex_file:
        tex_file.close()

    try:
        plt.gca().set_xlabel(units[x])
    except KeyError:
        pass
    try:
        plt.gca().set_ylabel(units[y])
    except KeyError:
        pass
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=4, mode='expand', borderaxespad=0.)
    plt.title('{x} vs {y} ({type} polygons)'.format(x=x, y=y, type=type_))

    if img_prefix:
        if in_file:
            file_name = os.path.splitext(in_file)[0] + '.svg'
        else:
            file_name = '.'.join(
                [img_prefix, type_, '{x}-{y}'.format(x=x, y=y),
                 ','.join(sorted(algorithm.name for algorithm in algorithms))
                 ]
            )
            if x_low is not None:
                file_name += '.x>=' + str(x_low)
            if x_high is not None:
                file_name += '.x<=' + str(x_high)
            if y_low is not None:
                file_name += '.y>=' + str(y_low)
            if y_high is not None:
                file_name += '.y<=' + str(y_high)
            file_name += '.svg'
        plt.savefig(file_name, dpi='figure', bbox_inches='tight', pad_inches=0.1)
    else:
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot benchmark data.')
    parser.add_argument('-w', '--without', action='append', default=[], help='skip this algorithm')
    parser.add_argument('-s', '--show', action='append', default=[],
                        help='show only this/these algorithm(s) / takes precedence over --without')
    parser.add_argument('-x', '--x', default='size', help='Which data should be shown on x-axis?')
    parser.add_argument('-y', '--y', default='memory', help='Which data should be shown on y-axis?')

    parser.add_argument('--x-low', type=int, help='The lowest allowed value for x data')
    parser.add_argument('--x-high', type=int, help='The highest allowed value for x data')

    parser.add_argument('--y-low', type=int, help='The lowest allowed value for y data')
    parser.add_argument('--y-high', type=int, help='The highest allowed value for y data')

    parser.add_argument('--type', type=str, choices=config['type_options'], default=config['type'])
    parser.add_argument('--version', action='append', default=[])

    parser.add_argument('--width', type=float, help='The width of each violin-plot', default=3)
    parser.add_argument('--alpha', type=float, help='Alpha value of plot parts', default=0.3)

    parser.add_argument('--include-ignored', action='store_true', help='Also plot ignored data points')

    parser.add_argument('-i', '--image', type=str, help='output image file name prefix', default=None)
    parser.add_argument('-v', '--verbose', action='store_true', help='be more verbose')
    parser.add_argument('-q', '--quiet', action='store_true', help='be quiet')

    parser.add_argument('--dump', action='store_true', help='Should we dump the data to a file?')
    parser.add_argument('--load', type=str, default=None, help='Load data from file?')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif args.quiet:
        logging.basicConfig(level=logging.WARNING)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.version:
        versions = []
        for version in args.version:
            try:
                match = re.match('^(\d+|x)\.(\d+|x)\.(\d+|x)$', version)
            except TypeError:
                logging.error('Option for version has type error: "%s".', version)
                sys.exit(1)
            else:
                if match is None:
                    logging.error('Cannot match version "%s"', version)
                    sys.exit(1)
                try:
                    # "Exact" match
                    criteria = []
                    for field, value in ((Version.major, match.group(1)), (Version.minor, match.group(2)),
                                         (Version.patch, match.group(3))):
                        if value != 'x':
                            criteria.append(field == int(value))

                    print(criteria)
                    try:
                        vs = list(Version.select(Version.id).where(*criteria).execute())
                    except TypeError:
                        vs = []
                    versions.extend(vs)
                except DoesNotExist:
                    logging.error('Given version does not exist, possible versions: %s',
                                  ', '.join('{0}.{1}.{2}'.format(v.major, v.minor, v.patch) for v in Version.select()))
                    sys.exit(1)
        args.version = versions
    else:
        args.version = None

    if args.image is None:
        args.image = date.today().strftime('%Y-%m-%d')

    ret = main(without=args.without, show=args.show, x=args.x, y=args.y, img_prefix=args.image,
               x_low=args.x_low, x_high=args.x_high, y_low=args.y_low, y_high=args.y_high,
               with_ignored=args.include_ignored, violin_width=args.width, alpha=args.alpha, type_=args.type,
               versions=args.version, dump=args.dump, in_file=args.load)
    if ret is not None:
        sys.exit(ret)
