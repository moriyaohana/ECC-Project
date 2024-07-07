package com.sipl.textoveraudioapp

import android.content.SharedPreferences
import androidx.preference.PreferenceManager
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import java.nio.ByteBuffer

class TransmitterWrapper(
    private val pythonInstance: Python,
    val symbolWeight: Int,
    val symbolSize: Int,
    val samplesPerSymbol: Int,
    val sampleRateHz: Float,
    val frequencyRangeStartHz: Float,
    val frequencyRangeEndHz: Float,
    val eccSymbols: Int,
    val eccBlock: Int,
    val snrThreshold: Float
) {
    private val transmitter: PyObject

    init {
        val transmitterModule = pythonInstance.getModule("transmitter")
        transmitter = transmitterModule.callAttr(
            "Transmitter",
            symbolWeight,
            symbolSize,
            samplesPerSymbol,
            sampleRateHz,
            frequencyRangeStartHz,
            frequencyRangeEndHz,
            eccSymbols,
            eccBlock,
            snrThreshold
            )
    }

    fun transmitBuffer(buffer: ByteArray): ByteArray {
        val pythonBuffer = PyObject.fromJava(buffer)
        return transmitter.callAttr("transmit_pcm_data", pythonBuffer).toJava(ByteArray::class.java)
    }
}
