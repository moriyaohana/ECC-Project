package com.example.myapplication

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.view.View

class RGBView(context: Context, private val bufferSize: Int) : View(context) {

    private val circularBuffer = CircularBuffer(bufferSize)
    private val paint = Paint()

    fun addRGBValue(rgbValue: RGBValue) {
        circularBuffer.add(rgbValue)
        invalidate() // Request to redraw the view
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        canvas?.let {
            val buffer = circularBuffer.getBuffer()
            val width = width.toFloat()
            val height = height / bufferSize.toFloat()

            buffer.forEachIndexed { i, rgbValue ->
                rgbValue?.let {
                    paint.color = Color.rgb(it.red, it.green, it.blue)
                    canvas.drawRect(0f, i * height, width, (i + 1) * height, paint)
                }
            }
        }
    }
}

