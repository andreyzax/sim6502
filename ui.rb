module UI

  require 'curses'

  BYTES_PER_CHAR = 1
  private_constant :BYTES_PER_CHAR


  @@initalized = false
  def UI::initalized
    return @@initalized
  end

  def UI::init_ui
    return if @@initalized
    Curses.init_screen
    Curses.cbreak
    Curses.noecho
    @@initalized = true
  end

  def UI::shutdown_ui
    Curses.close_screen
    @@initalized = false
  end

  class Console
    def initialize(cols: 15, rows: 7)
      raise 'Cant create Console object without initializing the UI module' unless UI.initalized

      @@count ||= 0 # initialize if not alredy set
      @@count += 1
      raise 'Only one Console object is allowed to exist' if @@count > 1

      @cols = cols
      @rows = rows
      @frame_buffer = Array.new(cols * rows, 0)
      @win = Curses::Window.new(rows + 2, cols + 2, 2, Curses.cols - cols - 4)
      @win.box('|', '-')
      @win.setpos(1,1)
    end

    def set_ch(ch, x, y)
      raise "Can't set character outside of window" if (x < 0 or x > @cols -1) or (y < 0 or y > @rows - 1)
      raise "#{ch.dump} is not a valid character" if ch.length != 1 or ch[0] =~ /[^[:print:]]/ # Check we are passing 1 printable char

      @win.setpos(y + 1, x + 1)
      @win.addch(ch)
      @win.refresh
    end

    def pos(x,y)
      raise "Can't set postion outside of window" if (x < 1 or x > @rows) or (y < 1 or y > @cols)
      @win.setpos(y,x)
    end

    def put_ch(ch)
      raise "#{ch.dump} is not a valid character" if ch.length != 1 or ch[0] =~ /[^[:print:]]/ # Check we are passing 1 printable char
      if @win.curx > @cols # Move one line down
        pos(1,@win.cury + 1)
      end
      if @win.cury > @rows
        raise "Can't put character outside of window"
      end
      @win.addch(ch)
      @win.refresh
    end

    def put_s(str)
      str.each_char { |ch| put_ch(ch) }
    end
  end
end
