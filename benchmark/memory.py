"""A memory profiler to look into the memory consumption of the functions."""

import io
import logging
import sys
import types
from collections import Mapping, Set, deque
from collections import OrderedDict
from json import dump
from matplotlib import pyplot as plt
from matplotlib.ticker import FixedLocator


def memprof(*args, **kwargs):
    """Decorate any function to be memory profiled."""
    def inner(func):
        return MemoryProfiler(func, *args, **kwargs)

    # To allow @memprof with parameters
    if len(args) and callable(args[0]):
        func = args[0]
        args = args[1:]
        return inner(func)
    else:
        return inner


class MemoryProfiler:
    """Bundle everything that is needed to profile one function."""

    ignored = (
        '__builtins__',
        '__cached__',
        '__doc__',
        '__file__',
        '__loader__',
        '__name__',
        '__package__',
        '__spec__',
    )

    not_interesting = (
        type,
        types.ModuleType,
        types.FunctionType,
        types.LambdaType,
        types.MethodType,
        types.GetSetDescriptorType,
        types.BuiltinFunctionType,
        types.BuiltinMethodType,
        types.GeneratorType,
        io.IOBase,
    )

    core_types = (
        type(None),
        int,
        float,
        str,
        complex,
    )

    def __init__(self, function):
        """Create new profiler for one function."""
        self.function = function
        self.variables = []
        self.bytes = []
        self.info = []
        self.last_byte_count = 0
        self.bytes_stack = []
        self.last_seen = set()
        self.seen_stack = []

    def __call__(self, *args, **kwargs):
        """Call the original function with the profiler attached."""
        trace_function = sys.gettrace()
        logging.debug('setting tracer function and calling original function')
        sys.settrace(self.tracer)
        result = self.function(*args, **kwargs)
        sys.settrace(trace_function)
        logging.debug('tracer function was reset')
        self.save()
        self.plot()
        return result

    def save(self):
        """Save the collected data in a json file."""
        with open(self.function.__name__ + '.json', 'w') as f:
            logging.debug('storing data')
            dump(self.info, f)

    def plot(self):
        """Plot the collected data."""
        logging.debug('plotting data')
        plt.figure(figsize=(1000, 20))
        plt.gcf().clear()
        plt.grid(True)
        plt.gca().plot(list(range(len(self.bytes))), self.bytes)
        ticks = OrderedDict(
            (ix, '{0} {1}'.format(event, name)) for
            ix, (event, name, _, _, _, _) in filter(lambda x: x[1][0] in ('call', 'return'), enumerate(self.info)))
        loc = FixedLocator(list(ticks.keys()))
        plt.gca().xaxis.set_major_locator(loc)
        plt.gca().set_xlim([0, len(self.bytes) - 1])
        plt.gca().set_xticklabels(list(ticks.values()))
        plt.setp(plt.gca().xaxis.get_majorticklabels(), rotation=90)
        logging.debug('saving plot')
        plt.savefig(self.function.__name__ + '.svg', dpi='figure', bbox_inches='tight', pad_inches=0.1)

    def is_interesting(self, value):
        """Decide whether a value is worth looking deeper into it."""
        if isinstance(value, self.__class__):
            return False
        if isinstance(value, self.not_interesting):
            return False
        return True

    def has_core_type(self, value):
        """Decide whether a value's type is a core type."""
        return isinstance(value, self.core_types)

    def size_of(self, value, already_seen):
        """Return the (recursive) size of a value."""
        def _size_of(value):
            if id(value) in already_seen or not self.is_interesting(value):
                return 0

            already_seen.add(id(value))

            size = sys.getsizeof(value)

            if self.has_core_type(value):
                return size

            if isinstance(value, (tuple, list, Set, deque)):
                size += sum(_size_of(i) for i in value)
            elif isinstance(value, Mapping) or hasattr(value, 'items'):
                size += sum(_size_of(k) + _size_of(v) for k, v in value.items())

            if hasattr(value, '__dict__'):
                size += _size_of(vars(value))
            if hasattr(value, '__slots__'):
                size += sum(_size_of(getattr(value, s)) for s in value.__slots__ if hasattr(value, s))

            return size

        return _size_of(value)

    def memory_consumption(self, variables, already_seen):
        """Obtain the memory consumption of all variables."""
        for name, value in variables.items():
            if value is self.__class__:
                continue
            if not self.is_interesting(value):
                continue

            yield name, self.size_of(value, already_seen)

    def tracer(self, frame, event, arg):
        """Check all variables for every line of code."""
        if event not in ('call', 'line', 'return'):
            return

        # logging.debug('{} in {} line {} ({})'.format(event, frame.f_code.co_name, frame.f_code.co_firstlineno,
        #                                              frame.f_code.co_filename))

        if event == 'call':
            self.bytes_stack.append(self.last_byte_count)
            self.seen_stack.append(self.last_seen)

        variables = frame.f_locals.copy()
        # variables = frame.f_globals.copy()
        # variables.update(frame.f_locals)

        for key in self.ignored:
            variables.pop(key, None)

        function_name = frame.f_code.co_name
        try:
            function_name = frame.f_locals['self'].__class__.__name__ + '.' + function_name
        except KeyError:
            pass

        variables.pop('self', None)

        self.last_seen = self.seen_stack[-1].copy()

        self.variables.append(dict(self.memory_consumption(variables, self.last_seen)))
        self.last_byte_count = self.bytes_stack[-1] + sum(v for v in self.variables[-1].values())
        self.bytes.append(self.last_byte_count)
        self.info.append((event, function_name, self.variables[-1], self.bytes[-1], frame.f_code.co_filename,
                          frame.f_lineno))

        if event == 'return':
            self.bytes_stack.pop()
            self.seen_stack.pop()

        return self.tracer
