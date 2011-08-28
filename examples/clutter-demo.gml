# // -*- mode: Javascript -*-
import Clutter

ClutterStage {
  id: main_stage
  color: "white"
  width: 800; height: 600
  title: "Script demo"
  ClutterText {
    id: hello_label
    x: 400; y: 300
    text: "Hello World!"
    color: "black"
    font_name: "Sans 48px"
  }
  destroy:: clutter_main_quit
}
