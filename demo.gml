// -*- mode: javascript -*-
GtkListStore {
    id: "liststore1"
}

GtkWindow {
    id: "window1"
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
            }
            _expand: false
        }

        GtkScrolledWindow {
            id: "scrolledwindow1"
            hscrollbar_policy: GtkPolicyType.automatic
            vscrollbar_policy: automatic
            shadow_type: GtkShadowType.in
            GtkTreeView {
                model: liststore1
                tooltip_column: 3
            }
        }
        GtkStatusbar {
            id: "statusbar1"
            _expand: false
        }
    }
}
