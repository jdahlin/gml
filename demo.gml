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
            GtkMenuItem {
                label: "_File"
                use_underline: true
                GtkMenu {
                    child_type: submenu
                    GtkImageMenuItem {
                        label: "gtk-new"
                        tooltip_text: "Create a new file"
                        use_stock: true
                    }
                    GtkImageMenuItem {
                        label: "gtk-open"
                        tooltip_text: "Open a file"
                        use_stock: true
                    }
                    GtkImageMenuItem {
                        label: "gtk-save"
                        tooltip_text: "Save a file"
                        use_stock: true
                    }
                    GtkImageMenuItem {
                        label: "gtk-save-as"
                        tooltip_text: "Save with a different name"
                        use_stock: true
                    }
                    GtkSeparatorMenuItem
                    GtkImageMenuItem {
                        label: "gtk-quit"
                        use_stock: true
                        tooltip_text: "Quit the program"
                        activate:: main_quit
                    }
                }
            }
            GtkMenuItem {
                label: "_Edit"
                use_underline: true
                GtkMenu {
                    child_type: submenu
                    GtkImageMenuItem {
                        label: "gtk-copy"
                        tooltip_text: "Copy selected object into the clipboard"
                        use_stock: true
                    }
                    GtkImageMenuItem {
                        label: "gtk-cut"
                        tooltip_text: "Cut selected object into the clipboard"
                        use_stock: true
                    }
                    GtkImageMenuItem {
                        label: "gtk-paste"
                        tooltip_text: "Paste object from the Clipboard"
                        use_stock: true
                    }
                }
            }
            GtkMenuItem {
                label: "_Help"
                use_underline: true
                GtkMenu {
                    child_type: submenu
                    GtkImageMenuItem {
                        label: "gtk-about"
                        use_stock: true
                        #accelerator: "F1"
                    }
                }
            }
            _expand: false
        }

        GtkToolbar {
            _expand: false
            GtkToolButton {
                label: "New"
                stock_id: "gtk-new"
            }
            GtkToolButton {
                stock_id: "gtk-open"
            }
            GtkToolButton {
                stock_id: "gtk-save"
            }
            GtkSeparatorToolItem
            GtkToolButton {
                stock_id: "gtk-copy"
            }
            GtkToolButton {
                stock_id: "gtk-cut"
            }
            GtkToolButton {
                stock_id: "gtk-paste"
            }
        }

        GtkScrolledWindow {
            id: scrolledwindow1
            hscrollbar_policy: GtkPolicyType.automatic
            vscrollbar_policy: automatic
            shadow_type: GtkShadowType.in
            GtkTreeView {
                model: liststore1
                tooltip_column: 3
            }
        }

        GtkStatusbar {
            id: statusbar1
            _expand: false
        }
    }
}
