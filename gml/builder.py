import StringIO

import gobject
import gtk
import clutter

from .parser import Object, GMLParser


class DelayedProperty(Exception):
    pass


class GMLBuilder(gtk.Builder):
    def __init__(self):
        gtk.Builder.__init__(self)
        self._objects = {}
        self._property_parsers = {}
        self.signals = {}
        self._delayed_properties = []

        self._register_property_parsers()

    def _register_property_parsers(self):
        self._property_parsers[gobject.TYPE_BOOLEAN] = self._parse_property_bool
        self._property_parsers[gobject.TYPE_INT] = self._parse_property_int
        self._property_parsers[gobject.TYPE_UINT] = self._parse_property_int
        self._property_parsers[gobject.TYPE_STRING] = self._parse_property_string
        self._property_parsers[gobject.TYPE_ENUM] = self._parse_property_enum
        self._property_parsers[gobject.TYPE_OBJECT] = self._parse_property_object
        self._property_parsers[gobject.TYPE_INTERFACE] = self._parse_property_object

    def _construct_object(self, obj, parent=None):
        if parent is not None:
            inst = getattr(parent.props, obj.name, None)
        else:
            inst = None
        if inst:
            obj_type = inst.__gtype__
        else:
            obj_type = gobject.type_from_name(obj.name)

        obj_id = None

        # Properties
        properties = {}
        child_properties = {}
        delayed_properties = []
        for prop in obj.properties:
            name = prop.name
            if name == 'id':
                obj_id = prop.value
                continue

            if name.startswith('_'):
                name = name[1:]
                child_properties[name] = prop.value
            elif name == 'child_type':
                obj.child_type = prop.value
            else:
                if isinstance(prop.value, Object):
                    prop.value = self._construct_object(prop.value)[0]

                if '.' in name:
                    delayed_properties.append(prop)
                else:
                    pspec = getattr(obj_type.pytype.props, name)
                    try:
                        properties[name] = self._parse_property(pspec, prop.value)
                    except DelayedProperty:
                        delayed_properties.append(prop)

        if inst is None:
            inst = gobject.new(obj_type, **properties)
            if obj_id is None:
                obj_id = str(hash(obj))
            self._objects[obj_id] = inst

            if parent is not None and not obj.is_property:
                gtk.Buildable.add_child(parent, self, inst, obj.child_type)
        else:
            for name, value in properties.items():
                inst.set_property(name, value)

        # Signals
        for signal in obj.signals:
            inst.connect(signal.name, self.signals[signal.handler])

        # Children
        if isinstance(inst, gtk.Container):
            for child in obj.children:
                child_inst, child_props = self._construct_object(child, inst)
                child_pspecs = {}
                for pspec in inst.list_child_properties():
                    child_pspecs[pspec.name] = pspec
                for prop_name, value in child_props.items():
                    pspec = child_pspecs[prop_name]
                    value = self._parse_property(pspec, value)
                    inst.child_set_property(child_inst, prop_name, value)

        # Delayed_properties
        for prop in delayed_properties:
            self._delayed_properties.append((inst, prop))
        return inst, child_properties

    def _apply_delayed_properties(self):
        for inst, prop in self._delayed_properties:
            if '.' in prop.name:
                parts = prop.name.split('.')
                start = parts[0]
                for part in parts[:-1]:
                    inst = getattr(inst.props, part)
                prop_name = parts[-1]
            else:
                prop_name = prop.name
            pspec = getattr(inst.__class__.props, prop_name)
            if gobject.type_is_a(pspec.value_type, gobject.TYPE_OBJECT):
                value = self._objects[prop.value]
            else:
                value = self._parse_property(pspec, prop.value)

            inst.set_property(prop_name, value)

    def _parse_property_bool(self, pspec, value):
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            raise Exception("Unknown value %r for property %r with type %s" % (
                value, pspec.name, gobject.type_name(pspec.value_type)))

    def _parse_property_int(self, pspec, value):
        try:
            return int(value)
        except ValueError:
            raise Exception("Invalid int value: %s" % (value, ))

    def _parse_property_enum(self, pspec, value):
        if '.' in value:
            enum, value = value.split(".", 1)
            enum_type = gobject.type_from_name(enum)
        else:
            enum_type = pspec.value_type
        for e in enum_type.pytype.__enum_values__.values():
            if e.value_nick == value:
                return e

        raise Exception(value)

    def _parse_property_string(self, pspec, value):
        if value[0] and value[-1] == '"':
            return value[1:-1]

        if "." in value:
            parts = value.split(".")
            start = parts[0]
            obj = self.get_by_name(start)
            if obj is None:
                raise Exception("Unknown object %r" % (start, ))

            for part in parts[1:]:
                obj = getattr(obj.props, part)
            return obj

    def _parse_property_object(self, pspec, value):
        if isinstance(value, gobject.GObject):
            return value
        elif isinstance(value, str):
            raise DelayedProperty
        else:
            raise Exception(value)

    def _parse_property(self, pspec, value):
        value_type = pspec.value_type
        while True:
            parser = self._property_parsers.get(value_type, None)
            if parser is not None:
                return parser(pspec, value)

            try:
                value_type = gobject.type_parent(value_type)
            except RuntimeError:
                break

        raise NotImplementedError(pspec.value_type)

    def _import(self, import_):
        # FIXME: Proper import system
        name = import_.name
        if name == 'Gtk':
            import gtk
            self.signals["gtk_main_quit"] = gtk.main_quit
        elif name == 'Clutter':
            import clutter
            self.signals["clutter_main_quit"] = clutter.main_quit

            def convert_color(pspec, value):
                s = value[1:-1]
                return clutter.color_from_string(s)
            self._property_parsers[clutter.Color.__gtype__] = convert_color
        else:
            raise Exception("Unknown module: %r" % (name, ))

    def _parse_and_construct(self, fp):
        parser = GMLParser()
        ns = parser.parse(fp)
        for import_ in ns.imports:
            self._import(import_)

        for obj in ns.objects:
            self._construct_object(obj)

        self._apply_delayed_properties()

    def add_from_file(self, filename):
        fp = open(filename)
        self._parse_and_construct(fp)

    def add_from_string(self, string):
        fp = StringIO.StringIO(string)
        self._parse_and_construct(fp)

    def get_by_name(self, name):
        return self._objects.get(name)

    @property
    def objects(self):
        return self._objects.values()

    def main(self):
        # FIXME: modules should define this
        gtk.main()
