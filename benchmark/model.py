#!/usr/bin/env python3.5
"""Defines a database model to be used with peewee for benchmark data."""

from socket import gethostname

from peewee import BooleanField, CharField, DateTimeField, DoubleField, FixedCharField, ForeignKeyField, \
    IntegerField, Model, PostgresqlDatabase, TextField
from playhouse.migrate import PostgresqlMigrator, migrate

import geometry

if gethostname() == 'denkbrett':
    db = PostgresqlDatabase('mca', host='localhost', user='jonascleve')
else:
    db = PostgresqlDatabase('ag_ti_mca', host='agdbs-srv01', password='ag-ti-mca')

db.autorollback = True


class BaseModel(Model):
    """A base model for nice formatting."""

    def __repr__(self):
        """Print a nice representation containing all fields."""
        return '{class_name}({data})'.format(class_name=self.__class__.__name__, data=', '.join(
            '{key}={value!r}'.format(key=k, value=v) for k, v in sorted(self._data.items())))

    class Meta:
        database = db


class Point(BaseModel):
    """A point in 2d."""

    x = DoubleField()
    y = DoubleField()

    class Meta:
        indexes = (
            # Make combination unique.
            (('x', 'y'), True),
        )
        order_by = ('x', 'y')

    def as_geometry(self):
        """Return a geometry class representation of this point."""
        return geometry.Point(self.x, self.y)


class Host(BaseModel):
    """A host with its name."""

    name = CharField(20, index=True, unique=True)

    class Meta:
        order_by = ('name',)


class Algorithm(BaseModel):
    """An algorithm with its name."""

    name = CharField(50, index=True, unique=True)

    class Meta:
        order_by = ('name',)


class PolygonType(BaseModel):
    """A type a polygon can be of (e.g. random, sleeve, etc.)."""

    name = CharField(50, index=True, unique=True)

    class Meta:
        order_by = ('name',)


class Polygon(BaseModel):
    """A polygon is of a specific type."""

    type = ForeignKeyField(PolygonType, related_name='polygons', default=1)
    size = IntegerField(index=True)

    class Meta:
        order_by = ('type', 'size')

    def as_geometry(self):
        """Return a geometry class representation of this polygon."""
        from geometry.polygons import polygon_from_database
        return polygon_from_database(self.id)

    def wipe(self):
        """Remove this polygon and all additional and depending data from the database."""
        instances = Instance.select(Instance.id).where(Instance.run << self.runs)
        IntegerProperty.delete().where(IntegerProperty.instance << instances).execute()
        Time.delete().where(Time.instance << instances).execute()
        PathPoint.delete().where(PathPoint.instance << instances).execute()
        Instance.delete().where(Instance.id << instances).execute()
        self.delete_instance(recursive=True)
        db.execute_sql(
            'DELETE FROM point WHERE NOT EXISTS (SELECT NULL FROM polygonpoint WHERE polygonpoint.point_id = point.id)'
        )


class PolygonPoint(BaseModel):
    """A polygon point is defined by a point an index and a polygon."""

    polygon = ForeignKeyField(Polygon, related_name='polygon_points')
    point = ForeignKeyField(Point, related_name='polygon_points')
    index = IntegerField(index=True)
    is_vertex = BooleanField(default=True, index=True)

    class Meta:
        indexes = (
            # Make combination unique.
            (('polygon', 'point', 'index', 'is_vertex'), True),
        )
        order_by = ('polygon', 'is_vertex', 'index')

    def as_geometry(self):
        """Return a geometry class representation of this polygon point."""
        return geometry.PolygonPoint(self.point.as_geometry(), index=self.index)


class Version(BaseModel):
    """Version information contains a version number, date and time information, and a possibly empty git commit."""

    date = DateTimeField(index=True)
    description = TextField()
    major = IntegerField(index=True)
    minor = IntegerField(index=True)
    patch = IntegerField(index=True)
    commit = FixedCharField(max_length=40, index=True, null=True)

    class Meta:
        order_by = ('-major', '-minor', '-patch', '-date')


class Run(BaseModel):
    """A pair of points (s, t) from one polygon tested against all known algorithms."""

    polygon = ForeignKeyField(Polygon, related_name='runs')
    host = ForeignKeyField(Host, related_name='runs')
    start = DateTimeField(index=True)
    end = DateTimeField(index=True)
    s = ForeignKeyField(PolygonPoint, related_name='runs_as_s')
    t = ForeignKeyField(PolygonPoint, related_name='runs_as_t')
    version = ForeignKeyField(Version, related_name='runs')

    class Meta:
        order_by = ('polygon', 's', 't')


class Instance(BaseModel):
    """One instance of a pair run on one specific algorithm."""

    run = ForeignKeyField(Run, related_name='instances')
    algorithm = ForeignKeyField(Algorithm, related_name='instances')
    memory = IntegerField(index=True)
    median_time = DoubleField(default=0)
    path_length = IntegerField(index=True, default=-1)

    class Meta:
        indexes = (
            # Make combination unique.
            (('run', 'algorithm'), True),
        )
        order_by = ('run', 'algorithm')


class PathPoint(BaseModel):
    """One point on the resulting path for a specific run on a specific algorithm."""

    instance = ForeignKeyField(Instance, related_name='path_points')
    index = IntegerField(index=True)
    polygon_point = ForeignKeyField(PolygonPoint, related_name='path_points')

    class Meta:
        indexes = (
            # Make combination unique.
            (('instance', 'index'), True),
        )
        order_by = ('instance', 'index')


class PropertyName(BaseModel):
    """Names for additional properties."""

    name = CharField(50, index=True, unique=True)

    class Meta:
        order_by = ('name',)


class IntegerProperty(BaseModel):
    """An additional property for runs."""

    instance = ForeignKeyField(Instance, related_name='integer_properties')
    name = ForeignKeyField(PropertyName, related_name='integer_properties')
    value = IntegerField()

    class Meta:
        order_by = ('instance', 'name')


class Time(BaseModel):
    """Runtime for a specific run with a specific algorithm."""

    instance = ForeignKeyField(Instance, related_name='times')
    time = DoubleField(index=True)

    class Meta:
        order_by = ('instance', 'time')


def reset():
    """Reset all database tables."""
    db.drop_tables(BaseModel.__subclasses__(), cascade=True, safe=True)
    db.create_tables(BaseModel.__subclasses__())


def migration_001():
    """Add time property to instance, so we do not "need" to calculate median in database."""
    migrator = PostgresqlMigrator(db)
    with db.transaction():
        migrate(
            migrator.add_column(Instance._meta.db_table, Instance.median_time.db_column, Instance.median_time)
        )


def migration_002():
    """Add path length property to instance, so we do not "need" to calculate it on the fly."""
    migrator = PostgresqlMigrator(db)
    with db.transaction():
        migrate(
            migrator.add_column(Instance._meta.db_table, Instance.path_length.db_column, Instance.path_length)
        )
