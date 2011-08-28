import StringIO
import tokenize

import gobject
import gtk

# Parser

class Token(object):
    def __init__(self, kind, value, start, end):
        self.kind = kind
        self.value = value
        self.start = start
        self.end = end

    def __repr__(self):
        return '<Token %r>' % (self.value, )


class Object(object):
    def __init__(self, name):
        self.name = name
        self.children = []
        self.properties = []
        self.signals = []
        self.is_property = False
        self.child_type = None

    def __repr__(self):
        return '<Object %r>' % (self.name, )


class Property(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return '<Property %s=%r>' % (self.name, self.value)


class Signal(object):
    def __init__(self, name, handler):
        self.name = name
        self.handler = handler

    def __repr__(self):
        return '<Signal %s=%s>' % (self.name, self.handler)


def is_whitespace(token):
    v = token.value.strip()
    if v == "":
        return True
    if v in '\n':
        return True
    return False

def is_comment(token):
    v = token.value.strip()
    if v.startswith("#"):
        return True
    return False


class GMLParser(object):
    def __init__(self):
        self._eof = False
        self._tokens = []

    def parse(self, fp):
        # Pass 1: remove comments
        tokenize.tokenize(fp.readline, self.feed)

        # Pass 2: build AST
        objects = []
        while not self._eof:
            retval = self._parse_statement()
            if retval is None:
                continue

            if isinstance(retval, Object):
                objects.append(retval)
            else:
                raise Exception("Unexpected object: %s" % (retval, ))

        return objects

    # Parser below

    def feed(self, token, value, start, end, raw):
        token = Token(token, value, start, end)
        if is_whitespace(token) or is_comment(token):
            return
        self._tokens.insert(0, token)

    def _pop_token(self):
        if self._tokens:
            return self._tokens.pop()

    def _peek_token(self):
        if self._tokens:
            return self._tokens[-1]

    def _peek_tokens(self, i=0):
        return self._tokens[-i:]

    def _expect(self, value):
        token = self._pop_token()
        if token.value != value:
            raise Exception("Expected %r, got %r" % (value, token.value))

    def _parse_statement(self):
        token = self._pop_token()
        if token is None: # EOF
            self._eof = True
            return
        if token.kind == tokenize.NAME:
            next = self._peek_token()
            if next is None:
                self._eof = True
            elif next.value == '{':
                return self._parse_object(token)

            return self._create_object(token)
        elif token.value == ";":
            pass
        else:
            raise Exception(token)

    def _create_object(self, token, parent=None):
        #print '_create_object', token
        obj = Object(token.value)
        if parent:
            parent.children.append(obj)
        return obj

    def _parse_object(self, name_token, parent=None):
        #print '_parse_object', name_token
        obj = self._create_object(name_token, parent)
        self._expect('{')
        token = self._pop_token()
        while token.value != '}':
            next = self._peek_token()
            if next.value == ':':
                if len(self._tokens) > 2 and self._tokens[-2].value == ':':
                    self._parse_signal(obj, token)
                else:
                    self._parse_property(obj, token)
            elif next.value == '.':
                token = self._parse_property_reference(token)
                self._parse_property(obj, token)
            elif token.value == ';':
                pass
            elif next.value == '{':
                self._parse_object(token, obj)
            else:
                simple = self._parse_object_simple(token, obj)
                if simple is None:
                    raise Exception(token)
            token = self._pop_token()
            if token is None:
                self._eof = True
                break

        return obj

    def _parse_object_simple(self, token, parent=None):
        if token.kind != tokenize.NAME:
            return

        obj = self._create_object(token, parent)
        return obj

    def _parse_property(self, obj, token):
        #print '_parse_property', token
        prop_name = token.value
        self._expect(':')
        prop_token = self._peek_token()
        value = self._parse_property_value()
        if self._peek_token().value == '{':
            value = self._parse_object(prop_token)
            value.is_property = True

        obj.properties.append(Property(prop_name, value))

    def _parse_property_reference(self, token):
        self._pop_token()
        tokens = []
        tokens.append(token)
        while True:
            token = self._peek_token()
            if token.value == ':':
                break
            tokens.append(self._pop_token())
        v = '.'.join(t.value for t in tokens)
        return Token(token.kind, v, 0, 0)

    def _parse_property_value(self):
        tokens = []
        tokens.append(self._pop_token())
        while True:
            token = self._peek_token()
            if token.value != '.':
                break
            self._pop_token()
            tokens.append(self._pop_token())

        return '.'.join(t.value for t in tokens)

    def _parse_signal(self, obj, token):
        signal = token.value
        self._expect(':')
        self._expect(':')
        handler = self._pop_token()
        obj.signals.append(Signal(signal, handler.value))

# Builder

class DelayedProperty(Exception):
    pass

class GMLBuilder(gtk.Builder):
    def __init__(self):
        gtk.Builder.__init__(self)
        self._objects = {}
        self.signals = {}
        self._delayed_properties = []

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
                        properties[name] = self._eval_prop_value(pspec, prop.value)
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
                    value = self._eval_prop_value(pspec, value)
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
                value = self._eval_prop_value(pspec, prop.value)

            inst.set_property(prop_name, value)

    def _eval_prop_value(self, pspec, v):
        if gobject.type_is_a(pspec.value_type, gobject.TYPE_OBJECT):
            if isinstance(v, gobject.GObject):
                return v
            elif isinstance(v, str):
                raise DelayedProperty
            else:
                raise Exception(v)
        elif gobject.type_is_a(pspec.value_type, gobject.TYPE_ENUM):
            if '.' in v:
                enum, value = v.split(".", 1)
                enum_type = gobject.type_from_name(enum)
            else:
                enum_type = pspec.value_type
                value = v
            for e in enum_type.pytype.__enum_values__.values():
                if e.value_nick == value:
                    return e

            raise Exception(v)
        elif gobject.type_is_a(pspec.value_type, gobject.TYPE_BOOLEAN):
            if v == 'true':
                return True
            elif v == 'false':
                return False
            else:
                raise Exception("Unknown value %r for property %r with type %s" % (
                    v, pspec.name, gobject.type_name(pspec.value_type)))

        if v[0] and v[-1] == '"':
            return v[1:-1]
        elif "." in v:
            parts = v.split(".")
            start = parts[0]
            obj = self.get_by_name(start)
            if obj is None:
                raise Exception("Unknown object %r" % (start, ))

            for part in parts[1:]:
                obj = getattr(obj.props, part)
            return obj
        else:
            if v in self._objects:
                return self._objects[v]
            return int(v)

    def _parse_and_construct(self, fp):
        parser = GMLParser()
        for obj in parser.parse(fp):
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
