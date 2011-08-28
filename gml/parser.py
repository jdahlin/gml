import token
import tokenize


class Token(object):
    def __init__(self, kind, value, start, end):
        self.kind = kind
        self.value = value
        self.start = start
        self.end = end

    def __repr__(self):
        return '<Token %s, %r>' % (token.tok_name[self.kind], self.value, )


class Object(object):
    def __init__(self, name):
        self.name = name
        self.children = []
        self.properties = []
        self.signals = []
        self.is_property = False
        self.child_type = None

    def json(self):
        od = dict()
        od['name'] = self.name
        if self.children:
            od['c'] = [c.json() for c in self.children]
        if self.properties:
            od['props'] = [p.json() for p in self.properties]
        if self.signals:
            od['signals'] = [s.json() for s in self.signals]
        return od

    def __repr__(self):
        return '<Object %r>' % (self.name, )


class Property(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def json(self):
        return (self.name, self.value)

    def __repr__(self):
        return '<Property %s=%r>' % (self.name, self.value)


class Signal(object):
    def __init__(self, name, handler):
        self.name = name
        self.handler = handler

    def json(self):
        return { 'name' : self.name,
                 'handler' : self.handler }

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

    def tokenize(self, fp):
        # Pass 1: remove comments
        tokenize.tokenize(fp.readline, self.feed)

    @property
    def tokens(self):
        return list(reversed(self._tokens))

    def parse(self, fp):
        self.tokenize(fp)
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

