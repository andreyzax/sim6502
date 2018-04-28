require './ui'

module System
  STEP_SECONDS = 1.0

  class << self
    attr_accessor :memory_map
  end

  @memory_map = [] # Array of MemoryAreas


  def System::memory_area_overlaps?(memory_area1, memory_area2)
    if memory_area1.start >= memory_area2.start and memory_area1.start <= memory_area2.last
      return true
    elsif memory_area1.last >= memory_area2.start and memory_area1.last <= memory_area2.last
      return true
    elsif memory_area1.start <= memory_area2.start and memory_area1.last >= memory_area2.last
      return true
    else
      return false
    end
  end

  class MemoryArea

    attr_reader :start
    attr_reader :size

    def initialize(start: 0, size: 0)
      @start = start
      @size = size
      System.memory_map.each do |ma|
        if System::memory_area_overlaps?(self, ma)
          raise "Can't create MemoryArea that overlaps with another"
        end
      end
      System.memory_map << self
    end

    def last
      return start + size - 1
    end

    def []
      raise "Can't address locations in base MemoryArea class"
    end

    def []=
      raise "Can't address locations in base MemoryArea class"
    end
  end

  class RAM < MemoryArea
    def initialize(start: 0, size: 0)
      super(start: start, size: size)
      @storage = Array.new(size)
    end

    def [](index)
      raise 'Out of bounds access' if index < start or index >= start + size
      @storage[index - start]
    end

    def []=(index, value)
      raise 'Out of bounds access' if index < start or index >= start + size
      raise 'Memory can only store 8 bit postive values' if value < 0 or value > 255
      @storage[index - start] = value
    end
  end

  class Screen < MemoryArea
    def initialize(start: 500, cols: 15, rows: 8)
      super(start: start, size: cols * rows)
      @cols = cols
      @rows = rows
      UI.init_ui
      @cn = UI::Console.new(cols: cols, rows: rows)
    end

    def []=(index,value)
      raise 'Out of bounds access' if index < start or index >= start + size
      raise 'Screen can only accept 8 bit postive characters' if value < 0 or value > 255

      col = (index - start) % @cols
      row = (index - start) / @cols

      @cn.set_ch(value.chr, col, row)
    end
  end
end
