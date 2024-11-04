package com.sipl.textoveraudioapp

import android.content.Context
import android.graphics.Color
import android.text.Spannable
import android.text.SpannableString
import android.text.style.BackgroundColorSpan
import android.text.style.ForegroundColorSpan
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import java.nio.charset.Charset
import kotlin.math.min

class MessageHistoryAdapter(var eccSymbols: Int, var eccBlock: Int, val context: Context) : RecyclerView.Adapter<MessageHistoryAdapter.ViewHolder>() {
    private val messageHistory = MessageHistory()

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val rawMessageView: TextView
        val correctedMessageView: TextView

        init {
            rawMessageView = view.findViewById(R.id.rawMessage)
            correctedMessageView = view.findViewById(R.id.correctedMessage)
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_message, parent, false)

        return ViewHolder(view)
    }

    override fun getItemCount(): Int {
        return messageHistory.size
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val errors = messageHistory[position].errors
        Log.d("Error Detection", "Detected ${errors.size} errors")
        val rawMessage = colorRawMessage(
            String(messageHistory[position].rawData, Charsets.US_ASCII),
            messageHistory[position].errors
        )

        val errorsInMessage = errors.intersect(getMessageIndices(rawMessage.length).toSet())

        val correctedMessage = colorCorrectedMessage(
            String(messageHistory[position].data, Charsets.US_ASCII),
            errorsInMessage,
            messageHistory[position].isValid
        )

        holder.rawMessageView.setText(rawMessage, TextView.BufferType.SPANNABLE)
        holder.correctedMessageView.setText(correctedMessage, TextView.BufferType.SPANNABLE)
    }

    fun addMessage(messageData: MessageData) {
        messageHistory.add(messageData)
        notifyItemInserted(messageHistory.size - 1)
    }
    
    private fun getMessageIndices(messageSize: Int): ArrayList<Int> {
        val messageIndices = ArrayList<Int>()
        for (rawIndex in 0..<messageSize step eccBlock) {
            val eccSymbolsEnd = min(rawIndex + eccBlock, messageSize) - 1
            val eccSymbolStart= eccSymbolsEnd - eccSymbols

            for (messageIndex in rawIndex..<eccSymbolStart) {
                messageIndices.add(messageIndex)
            }
        }

        val CRC_SIZE = 4
        messageIndices.dropLast(CRC_SIZE)

        return messageIndices
    }

    private fun colorCorrectedMessage(message:String, correctedErrors: Set<Int>, isValid:Boolean): SpannableString {
        val spannableMessage = SpannableString(message)
        if (!isValid) {
            spannableMessage.setSpan(
                BackgroundColorSpan(ContextCompat.getColor(context, R.color.raw_message_error_fg)),
                0,
                spannableMessage.length,
                Spannable.SPAN_INCLUSIVE_EXCLUSIVE
            )
        }

        for (errorIndex in correctedErrors) {
            spannableMessage.setSpan(
                ForegroundColorSpan(ContextCompat.getColor(context, R.color.corrected_message_fixed_fg)),
                errorIndex,
                errorIndex + 1,
                Spannable.SPAN_EXCLUSIVE_EXCLUSIVE
            )
        }

        return spannableMessage
    }

    private fun colorRawMessage(message: String, errors: Set<Int>): SpannableString {
        val spannableMessage = SpannableString(message)
        spannableMessage.setSpan(
            ForegroundColorSpan(ContextCompat.getColor(context, R.color.raw_message_correct_fg)),
            0,
            spannableMessage.length,
            Spannable.SPAN_INCLUSIVE_EXCLUSIVE
        )
        for (errorIndex in errors) {
            spannableMessage.setSpan(
                ForegroundColorSpan(ContextCompat.getColor(context, R.color.raw_message_error_fg)),
                errorIndex,
                errorIndex + 1,
                Spannable.SPAN_EXCLUSIVE_EXCLUSIVE
            )
        }
        spannableMessage.setSpan(
            BackgroundColorSpan(ContextCompat.getColor(context, R.color.raw_message_ecc_bg)),
            0,
            spannableMessage.length,
            Spannable.SPAN_INCLUSIVE_EXCLUSIVE
        )

        for (messageIndex in getMessageIndices(spannableMessage.length)) {
            spannableMessage.setSpan(
                BackgroundColorSpan(ContextCompat.getColor(context, R.color.raw_message_bg)),
                messageIndex,
                messageIndex + 1,
                Spannable.SPAN_EXCLUSIVE_EXCLUSIVE
            )
        }

        val CRC_SIZE = 4
        val crcStart = spannableMessage.length - eccSymbols - CRC_SIZE
        val crcEnd = crcStart + CRC_SIZE
        spannableMessage.setSpan(
            BackgroundColorSpan(ContextCompat.getColor(context, R.color.raw_message_crc_bg)),
            crcStart,
            crcEnd,
            Spannable.SPAN_INCLUSIVE_EXCLUSIVE
        )

        return spannableMessage
    }
}