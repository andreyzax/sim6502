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
    end

    def last
      return start + size - 1
    end

    def []
      raise "Can't address locations in base MemoryArea class"
    end
  end
end
