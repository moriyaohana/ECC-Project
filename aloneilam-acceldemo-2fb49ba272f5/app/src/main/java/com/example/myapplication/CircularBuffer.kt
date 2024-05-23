package com.example.myapplication

data class RGBValue(val red: Int, val green: Int, val blue: Int)

class CircularBuffer(private val size: Int) {
    private val buffer: Array<RGBValue?> = arrayOfNulls(size)
    private var index = 0

    fun add(value: RGBValue) {
        buffer[index] = value
        index = (index + 1) % buffer.size
    }

    fun getBuffer(): List<RGBValue?> = buffer.toList()
}
