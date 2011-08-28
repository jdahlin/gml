# GML

This is an experimental parser and runtime for a QML like markup language
for Gtk+/Clutter. It is inspired by Qt's <http://en.wikipedia.org/wiki/QML>.

GML is licensed under GNU GPLv2+.

# Syntax

## Creating objects

Creating a new toplevel object you just use the type name

```javascript
GtkWindow
```

You can also specify a new type without any properties

```javascript
GtkWindow {}
```

## Properties

Properties are similar to JavaScript properties:

```javascript
GtkWindow { title: "Window Title" }
```

You can insert newlines anywhere you like:

```javascript
GtkWindow {
  title: "Window Title"
}
```

There's a special property called **id** which can is used to identify the object:

```javascript
GtkWindow {
  id: window1
}
```

# References

You can reference properties with an id, for instance:

```javascript
GtkListStore {
  id: liststore
}
GtkTreeView {
  model: liststore
}
```

You can also reference objects by using a dot notation:

```javascript
GtkButton {
  id: button1
  label: "Label"
}
GtkButton {
  id: button2
  label: button1.label
}
```

# Children

GML has a child concept implemented by a few types:
* GtkContainer

To add an child to an object, you just create it:

```javascript
GtkWindow {
  GtkVBox
}
```

It can of course be nested:

```javascript
GtkWindow {
  GtkVBox {
    GtkButton
    GtkLabel
  }
}
```

GtkContainers supports the concept of child properties, they are currently implemented
as underscore properties, eg:

```javascript
GtkWindow {
  GtkVBox {
    GtkButton {
      _expand: true
  }
}
```

# Supported types

* Strings: "string" or 'string'
* Integers: 123
* Floating point: 0.1
* Boolean: true or false
* Identifiers: button1
* References: same as identifiers

# TODO

Things to do, ordered by category

## General
* Build system
* Add license headers
* Gtk+3/Introspection port
* Glade output
* Clutter
* C rewrite

## Parser
* Lists
* New tokenizer
* Check token types better in parser
* Add error messages to parser
* Add a type for property referencs

## Builder
* GtkListStore columns & rows

## Tool
* Split into commands: run, validate, tokenize, parse, convert
* Add a validator
* Output: C
* Output: GtkBuilder
* Input: GtkBuilder
* Input: Existing widget tree via a GtkModule

## Tests
* 100% coverage (might be redundant for Python impl)
