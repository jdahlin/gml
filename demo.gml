# // -*- mode: javascript -*-
GtkListStore {
    id: liststore1
}

GtkWindow {
    id: window1
    default_height: 250
    default_width: 440
    title: "GtkBuilder demo"
    destroy:: main_quit
    visible: true
    GtkVBox {
        GtkMenuBar {
            _expand: false

            GtkMenuItem {
                label: "_File"
                use_underline: true
                GtkMenu {
                    child_type: submenu
                    GtkImageMenuItem { label: "gtk-new"; use_stock: true
                                       tooltip_text: "Create a new file" }
                    GtkImageMenuItem { label: "gtk-open"; use_stock: true
                                       tooltip_text: "Open a file" }
                    GtkImageMenuItem { label: "gtk-save"; use_stock: true
                                       tooltip_text: "Save a file" }
                    GtkImageMenuItem { label: "gtk-save-as"; use_stock: true
                                       tooltip_text: "Save with a different name" }
                    GtkSeparatorMenuItem
                    GtkImageMenuItem { label: "gtk-quit"; use_stock: true
                                       tooltip_text: "Quit the program"
                                       activate:: main_quit }
                }
            }

            GtkMenuItem {
                label: "_Edit"
                use_underline: true
                GtkMenu {
                    child_type: submenu
                    GtkImageMenuItem { label: "gtk-copy"; use_stock: true
                                       tooltip_text: "Copy selected object into the clipboard" }
                    GtkImageMenuItem { label: "gtk-cut" use_stock: true
                                       tooltip_text: "Cut selected object into the clipboard" }
                    GtkImageMenuItem { label: "gtk-paste" use_stock: true
                                       tooltip_text: "Paste object from the Clipboard" }
                }
            }

            GtkMenuItem {
                label: "_Help"
                use_underline: true
                GtkMenu {
                    child_type: submenu
                    GtkImageMenuItem { label: "gtk-about"; use_stock: true}
                }
            }
        }

        GtkToolbar {
            _expand: false
            GtkToolButton { stock_id: "gtk-new" }
            GtkToolButton { stock_id: "gtk-open" }
            GtkToolButton { stock_id: "gtk-save" }
            GtkSeparatorToolItem
            GtkToolButton { stock_id: "gtk-copy" }
            GtkToolButton { stock_id: "gtk-cut" }
            GtkToolButton { stock_id: "gtk-paste" }
        }

        GtkScrolledWindow {
            id: scrolledwindow1
            hscrollbar_policy: GtkPolicyType.automatic
            vscrollbar_policy: automatic
            shadow_type: GtkShadowType.in
            GtkTreeView {
                model: liststore1
                tooltip_column: 3
                GtkTreeViewColumn {
                    title: "Name"
                    GtkCellRendererText { text: 0 }
                }
                GtkTreeViewColumn {
                    title: "Surname"
                    GtkCellRendererText { text: 1 }
                }
                GtkTreeViewColumn {
                    title: "Age"
                    GtkCellRendererText { text: 2 }
                }
            }
        }

        GtkStatusbar {
            id: statusbar1
            _expand: false
        }
    }
}
