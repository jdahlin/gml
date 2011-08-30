import StringIO


from .config import use_pygtk
from .parser import (Object, GMLParser, TYPE_STRING, TYPE_IDENTIFIER,
                     TYPE_BOOLEAN, TYPE_NUMBER, TYPE_OBJECT)

if use_pygtk:
    import gobject as GObject
    import gtk as Gtk
else:
    from gi.repository import GObject, Gtk


class DelayedProperty(Exception):
    pass


class GMLBuilder(object):
    def __init__(self):
        self._fake_builder = Gtk.Builder()
        self._objects = {}
        self._property_parsers = {}
        self.signals = {}
        self._delayed_properties = []

        self._register_property_parsers()

    def _register_property_parsers(self):
        self._property_parsers[GObject.TYPE_BOOLEAN] = self._parse_property_bool
        self._property_parsers[GObject.TYPE_INT] = self._parse_property_int
        self._property_parsers[GObject.TYPE_UINT] = self._parse_property_int
        self._property_parsers[GObject.TYPE_STRING] = self._parse_property_string
        self._property_parsers[GObject.TYPE_ENUM] = self._parse_property_enum
        self._property_parsers[GObject.TYPE_OBJECT] = self._parse_property_object
        self._property_parsers[GObject.TYPE_INTERFACE] = self._parse_property_object

    def _construct_object(self, obj, parent=None):
        if parent is not None:
            inst = getattr(parent.props, obj.name, None)
        else:
            inst = None
        if inst:
            obj_type = inst.__gtype__
        else:
            obj_type = GObject.type_from_name(obj.name)

        obj_id = None

        # Properties
        properties = {}
        delayed_properties = []
        for prop in obj.properties:
            name = prop.name
            if name == 'id':
                obj_id = prop.value
                continue

            if name == 'child_type':
                obj.child_type = prop.value
                continue
            if isinstance(prop.value, Object):
                prop.value = self._construct_object(prop.value)

            if '.' in name:
                delayed_properties.append(prop)
            else:
                pspec = getattr(obj_type.pytype.props, name)
                try:
                    properties[name] = self._parse_property(pspec, prop)
                except DelayedProperty:
                    delayed_properties.append(prop)

        if inst is None:
            inst = GObject.new(obj_type, **properties)
            if obj_id is None:
                obj_id = str(hash(obj))
            self._objects[obj_id] = inst

            if parent is not None and not obj.is_property:
                Gtk.Buildable.add_child(parent, self._fake_builder,
                                        inst, obj.child_type)
        else:
            for name, value in properties.items():
                inst.set_property(name, value)

        # Signals
        for signal in obj.signals:
            inst.connect(signal.name, self.signals[signal.handler])

        # Children
        if isinstance(inst, Gtk.Container):
            for child in obj.children:
                properties = self._extract_child_properties(child)
                child_inst = self._construct_object(child, inst)
                child_pspecs = self._get_child_pspecs(inst)
                for prop in properties:
                    pspec = child_pspecs[prop.name]
                    value = self._parse_property(pspec, prop)
                    inst.child_set_property(child_inst, prop.name, value)

        # Delayed_properties
        for prop in delayed_properties:
            self._delayed_properties.append((inst, prop))
        return inst

    def _extract_child_properties(self, obj):
        for child in obj.children[:]:
            if child.name == 'packing':
                obj.children.remove(child)
                return child.properties
        return []

    def _get_child_pspecs(self, inst):
        pspecs = {}
        for pspec in inst.list_child_properties():
            pspecs[pspec.name] = pspec
        return pspecs

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
            if GObject.type_is_a(pspec.value_type, GObject.TYPE_OBJECT):
                value = self._objects[prop.value]
            else:
                value = self._parse_property(pspec, prop)

            inst.set_property(prop_name, value)

    def _parse_property_bool(self, pspec, prop):
        if prop.kind != TYPE_BOOLEAN:
            raise Exception("Invalid boolean property value: %r" % (
                prop.value, ))

        value = prop.value
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            raise Exception("Unknown value %r for property %r with type %s" % (
                value, pspec.name, GObject.type_name(pspec.value_type)))

    def _parse_property_int(self, pspec, prop):
        if prop.kind != TYPE_NUMBER:
            raise Exception("Invalid integer property value: %r" % (
                prop.value, ))

        value = prop.value
        try:
            return int(value)
        except ValueError:
            raise Exception("Invalid integer propety value: %r" % (value, ))

    def _parse_property_enum(self, pspec, prop):
        if prop.kind != TYPE_IDENTIFIER:
            raise Exception("Invalid enum property value: %r" % (
                prop.value, ))

        value = prop.value
        if '.' in value:
            enum, value = value.split(".", 1)
            enum_type = GObject.type_from_name(enum)
        else:
            enum_type = pspec.value_type
        for e in enum_type.pytype.__enum_values__.values():
            if e.value_nick == value:
                return e

        raise Exception(value)

    def _parse_property_string(self, pspec, prop):
        value = prop.value
        if prop.kind == TYPE_STRING:
            return value[1:-1]
        elif prop.kind != TYPE_IDENTIFIER:
            raise Exception("Invalid string property value: %r" % (
                prop.value, ))

        if "." in value:
            parts = value.split(".")
            obj_name = parts[0]
        else:
            parts = []
            obj_name = value
        obj = self.get_by_name(obj_name)
        if obj is None:
            raise Exception("Invalid string property value: %r" % (
                prop.value, ))
        for part in parts[1:]:
            obj = getattr(obj.props, part)
        return obj

    def _parse_property_object(self, pspec, prop):
        if prop.kind not in [TYPE_IDENTIFIER, TYPE_OBJECT]:
            raise Exception("Invalid object property value: %r" % (
                prop.value, ))

        value = prop.value
        if isinstance(value, GObject.GObject):
            return value
        elif isinstance(value, str):
            raise DelayedProperty
        else:
            raise Exception(value)

    def _parse_property(self, pspec, prop):
        value_type = pspec.value_type
        while True:
            parser = self._property_parsers.get(value_type, None)
            if parser is not None:
                return parser(pspec, prop)

            try:
                value_type = GObject.type_parent(value_type)
            except RuntimeError:
                break

        raise NotImplementedError(pspec.value_type)

    def _import(self, import_):
        # FIXME: Proper import system
        name = import_.name
        if name == 'Gtk':
            self.signals["gtk_main_quit"] = Gtk.main_quit
        elif name == 'Clutter':
            if use_pygtk:
                import clutter as Clutter
            else:
                from gi.repository import Clutter
            self.signals["clutter_main_quit"] = Clutter.main_quit

            def convert_color(pspec, prop):
                s = value[1:-1]
                return Clutter.color_from_string(s)
            self._property_parsers[Clutter.Color.__gtype__] = convert_color
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
        Gtk.main()
