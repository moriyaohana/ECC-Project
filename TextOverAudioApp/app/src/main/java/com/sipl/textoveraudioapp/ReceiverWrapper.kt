package com.sipl.textoveraudioapp

import android.os.Message
import com.chaquo.python.PyObject
import com.chaquo.python.Python


class ReceiverWrapper(
    private val pythonInstance: Python,
    val symbolWeight: Int,
    val symbolSize: Int,
    val samplesPerSymbol: Int,
    val sampleRateHz: Float,
    val frequencyRangeStartHz: Float,
    val frequencyRangeEndHz: Float,
    val eccSymbols: Int,
    val eccBlock: Int,
    val snrThreshold: Float,
    val correlationThreshold: Float
) {
    private val receiver: PyObject

    init {
        val receiverModule = pythonInstance.getModule("receiver")
        receiver = receiverModule.callAttr(
            "Receiver",
            symbolWeight,
            symbolSize,
            samplesPerSymbol,
            sampleRateHz,
            frequencyRangeStartHz,
            frequencyRangeEndHz,
            eccSymbols,
            eccBlock,
            snrThreshold,
            correlationThreshold
        )
    }

    private enum class MessageDataFields{
        RAW_DATA,
        ERRORS,
        DATA
    }

    fun getMessageHistory(): MessageHistory{
        val messageList = receiver["message_history"]!!.asList()
        val messageHistory = MessageHistory()

        for (messageFields in messageList) {
            val messageFieldsList = messageFields.asList()
            messageHistory.add(
                MessageData(
                    messageFieldsList[MessageDataFields.RAW_DATA.ordinal].toJava(ByteArray::class.java),
                    messageFieldsList[MessageDataFields.ERRORS.ordinal].asSet().map { pyObject -> pyObject.toInt() }.toSet(),
                    messageFieldsList[MessageDataFields.DATA.ordinal].toJava(ByteArray::class.java)
                )
            )
        }

        return messageHistory
    }

    fun receivePcmBuffer(buffer: ByteArray) {
        val pythonBuffer = PyObject.fromJava(buffer)
        receiver.callAttr("receive_pcm_buffer", pythonBuffer)
    }

    fun isSynchronised(): Boolean {
        return receiver["is_synchronised"]!!.toBoolean()
    }
}