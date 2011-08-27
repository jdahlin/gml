# GML

This is an experimental parser and runtime for a QML like markup language
for Gtk+/Clutter.

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

