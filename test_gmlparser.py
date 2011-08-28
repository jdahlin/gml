import unittest

import gtk

from gml.builder import GMLBuilder


class GMLBuilderTest(unittest.TestCase):
    def testEmpty(self):
        p = GMLBuilder()
        p.add_from_string("")
        self.assertEquals(p.objects, [])

    def testComment(self):
        p = GMLBuilder()
        p.add_from_string("# This is a comment")
        self.assertEquals(p.objects, [])

    def testSimple(self):
        p = GMLBuilder()
        p.add_from_string("GtkButton {}")
        self.assertEquals(len(p.objects), 1)

        p = GMLBuilder()
        p.add_from_string("GtkButton")
        self.assertEquals(len(p.objects), 1)

        p = GMLBuilder()
        p.add_from_string("GtkButton; GtkButton")
        self.assertEquals(len(p.objects), 2)

        p = GMLBuilder()
        p.add_from_string("GtkButton {}; GtkButton; GtkButton {}")
        self.assertEquals(len(p.objects), 3)

    def testMultiToplevel(self):
        p = GMLBuilder()
        p.add_from_string('GtkWindow { id: w1 } GtkWindow { id: w2 }')
        self.assertEquals(len(p.objects), 2)
        w1 = p.get_by_name("w1")
        self.failUnless(isinstance(w1, gtk.Window))
        w2 = p.get_by_name("w2")
        self.failUnless(isinstance(w2, gtk.Window))

    def testNested(self):
        p = GMLBuilder()
        p.add_from_string("GtkWindow { id: w1; GtkButton { } }")
        win = p.get_by_name('w1')
        self.failUnless(isinstance(win, gtk.Window))
        children = win.get_children()
        self.failUnless(children)
        self.assertEquals(len(children), 1)
        button = children[0]
        self.failUnless(isinstance(button, gtk.Button))

    def testPropertyString(self):
        p = GMLBuilder()
        p.add_from_string('GtkButton { label: "Label" }')
        self.assertEquals(len(p.objects), 1)
        button = p.objects[0]
        self.failUnless(isinstance(button, gtk.Button))
        self.assertEquals(button.get_label(), "Label")

    def testPropertyBool(self):
        p = GMLBuilder()
        p.add_from_string('GtkButton { use_underline: true }')
        self.assertEquals(len(p.objects), 1)
        button = p.objects[0]
        self.failUnless(isinstance(button, gtk.Button))
        self.assertEquals(button.props.use_underline, True)

    def testPropertyEnum(self):
        p = GMLBuilder()
        p.add_from_string('GtkScrolledWindow { id: sw1; hscrollbar_policy: automatic }')
        sw = p.get_by_name("sw1")
        self.assertEquals(sw.props.hscrollbar_policy, gtk.POLICY_AUTOMATIC)

        p = GMLBuilder()
        p.add_from_string("""GtkScrolledWindow {
            id: sw1
            hscrollbar_policy: GtkPolicyType.automatic
        }""")
        sw = p.get_by_name("sw1")
        self.assertEquals(sw.props.hscrollbar_policy, gtk.POLICY_AUTOMATIC)

    def testPropertyChild(self):
        p = GMLBuilder()
        p.add_from_string("""GtkVBox {
            id: box
            GtkButton {
            id: button
               _expand: true
            }
        }""")
        box = p.get_by_name("box")
        button = p.get_by_name("button")
        self.assertEquals(box.child_get_property(button, "expand"), True)

    def testPropertyMultiple(self):
        p = GMLBuilder()
        p.add_from_string("""GtkButton {
          label: "Label"
          use_underline:  true
        }""")
        self.assertEquals(len(p.objects), 1)
        button = p.objects[0]
        self.failUnless(isinstance(button, gtk.Button))
        self.assertEquals(button.get_label(), "Label")
        self.assertEquals(button.props.use_underline, True)

    def testPropertyMultipleSemiColon(self):
        p = GMLBuilder()
        p.add_from_string("""GtkButton {
          label: "Label"; use_underline: true
        }""")
        self.assertEquals(len(p.objects), 1)
        button = p.objects[0]
        self.failUnless(isinstance(button, gtk.Button))
        self.assertEquals(button.get_label(), "Label")
        self.assertEquals(button.props.use_underline, True)

    def testPropertyReference(self):
        p = GMLBuilder()
        p.add_from_string("""
        GtkWindow {
           name: "window1"; GtkButton { id: b1; label: "Label" }
        }
        GtkButton { id: b2; label: b1.label }
        GtkButton { id: b3; label: b1.parent.name }
        """)

        b1 = p.get_by_name("b1")
        b2 = p.get_by_name("b2")
        b3 = p.get_by_name("b3")
        self.assertEquals(b1.props.label, "Label")
        self.assertEquals(b2.props.label, "Label")
        self.assertEquals(b3.props.label, "window1")

    def testPropertyNestedReference(self):
        p = GMLBuilder()
        p.add_from_string("""
        GtkButton {
            id: b1
            label: "gtk-new"
            use_stock: true
            image.pixel_size: 32
        }
        GtkButton {
            id: b2
            label: "gtk-new"
            use_stock: true
            image { pixel_size: 64
                    stock: "gtk-edit" }
        }
        """)
        b1 = p.get_by_name("b1")
        self.assertEquals(b1.get_image().get_pixel_size(), 32)
        b2 = p.get_by_name("b2")
        self.assertEquals(b2.get_image().get_pixel_size(), 64)
        self.assertEquals(b2.get_image().get_stock()[0], "gtk-edit")

    def testPropertyNew(self):
        p = GMLBuilder()
        p.add_from_string("""
        GtkButton {
            id: b1
            image: GtkImage { stock: "gtk-edit" }
        }
        """)
        b1 = p.get_by_name("b1")
        self.assertEquals(b1.get_image().get_stock()[0], "gtk-edit")

        p = GMLBuilder()
        p.add_from_string("""
        GtkButton {
            id: b1
            image: GtkImage { stock: "gtk-edit" }
        }
        GtkButton {
            id: b2
            label: "gtk-edit"
            image: GtkImage { stock: b1.image.stock }
        }
        """)
        b2 = p.get_by_name("b2")
        self.assertEquals(b2.get_label(), "gtk-edit")
        self.assertEquals(b2.get_image().get_stock()[0], "gtk-edit")

    def testPropertyAfterChild(self):
        p = GMLBuilder()
        p.add_from_string("""
        GtkVBox {
          id: box
          GtkMenuBar {
            id: menubar
            _expand: false
            GtkMenuItem
            _fill: false
          }
        }""")

        box = p.get_by_name("box")
        menubar = p.get_by_name("menubar")

        self.assertEquals(box.child_get_property(menubar, 'expand'), False)
        self.assertEquals(box.child_get_property(menubar, 'fill'), False)

    def testSignal(self):
        self.called = False
        def activate(action):
            self.called = True
        p = GMLBuilder()
        p.signals['activate'] = activate
        p.add_from_string("""
        GtkAction {
          id: a
          activate:: activate
        }
        """)

        a = p.get_by_name("a")
        a.activate()

        self.failUnless(self.called)

    def testImport(self):
        p = GMLBuilder()
        p.add_from_string("import Gtk; GtkWindow; import Clutter")
        self.assertEquals(len(p.objects), 1)


class BoxTest(unittest.TestCase):
    def testChildren(self):
        p = GMLBuilder()
        p.add_from_string("""GtkWindow {
          id: w1
          GtkVBox {
            GtkButton
            GtkLabel
          }
        }""")
        win = p.get_by_name("w1")
        self.failUnless(isinstance(win, gtk.Window))
        box = win.get_child()
        children = box.get_children()
        self.failUnless(children)
        self.assertEquals(len(children), 2)
        button = children[0]
        self.failUnless(isinstance(button, gtk.Button))
        label = children[1]
        self.failUnless(isinstance(label, gtk.Label))

unittest.main()

