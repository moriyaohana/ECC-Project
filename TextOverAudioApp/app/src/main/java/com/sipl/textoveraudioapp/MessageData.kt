package com.sipl.textoveraudioapp

data class MessageData(
    val rawData: ByteArray,
    val errors: Set<Int>,
    val data: ByteArray,
    val isValid: Boolean) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as MessageData

        if (!rawData.contentEquals(other.rawData)) return false
        if (errors != other.errors) return false

        return data.contentEquals(other.data)
    }

    override fun hashCode(): Int {
        var result = rawData.contentHashCode()
        result = 31 * result + errors.hashCode()
        result = 31 * result + data.contentHashCode()
        
        return result
    }
}

typealias MessageHistory = ArrayList<MessageData>
