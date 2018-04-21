#!/usr/bin/env ruby

require './ui'

UI.init_ui

cn = UI::Console.new(cols: 30, rows: 15)
cn.put_s("x" * 6)
cn.set_ch('0', 0, 14)
sleep 5
UI.shutdown_ui
