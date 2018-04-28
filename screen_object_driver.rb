#!/usr/bin/env ruby

require './system'


screen = System::Screen.new(cols: 10, rows: 5)

screen[549] = "x".ord



sleep 3
UI.shutdown_ui
