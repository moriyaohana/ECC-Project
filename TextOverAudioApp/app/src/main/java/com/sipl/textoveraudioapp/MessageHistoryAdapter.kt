package com.sipl.textoveraudioapp

import android.content.Context
import android.text.Spannable
import android.text.SpannableString
import android.text.style.BackgroundColorSpan
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
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
        val rawMessage = SpannableString(messageHistory[position].rawData.decodeToString())

        holder.rawMessageView.text = messageHistory[position].data.decodeToString()
    }

    fun addMessage(messageData: MessageData) {
        messageHistory.add(messageData)
        notifyItemInserted(messageHistory.size - 1)
    }

    private fun colorRawMessage(message: String): SpannableString {
        val spannableMessage = SpannableString(message)
        for (index in spannableMessage.indices step eccBlock) {
            val eccSymbolsEnd = min(index + eccBlock, spannableMessage.length)
            val eccSymbolStart= eccSymbolsEnd - eccSymbols
            spannableMessage.setSpan(
                BackgroundColorSpan(ContextCompat.getColor(context, R.color.raw_message_ecc_bg)),
                eccSymbolStart,
                eccSymbolsEnd,
                Spannable.SPAN_INCLUSIVE_EXCLUSIVE
            )

            spannableMessage.setSpan(
                BackgroundColorSpan(ContextCompat.getColor(context, R.color.raw_message_bg)),
                index,
                eccSymbolStart,
                Spannable.SPAN_INCLUSIVE_EXCLUSIVE
            )
        }

        return spannableMessage
    }
}