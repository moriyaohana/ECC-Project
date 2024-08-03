package com.sipl.textoveraudioapp

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
        DATA,
        IS_VALID
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
                    messageFieldsList[MessageDataFields.DATA.ordinal].toJava(ByteArray::class.java),
                    messageFieldsList[MessageDataFields.IS_VALID.ordinal].toBoolean()
                )
            )
        }

        return messageHistory
    }

    fun receivePcmBuffer(buffer: ShortArray) {
        val pythonBuffer = PyObject.fromJava(buffer)
        receiver.callAttr("receive_pcm16_buffer", pythonBuffer)
    }

    fun isSynchronised(): Boolean {
        return receiver["is_synchronised"]!!.toBoolean()
    }
}