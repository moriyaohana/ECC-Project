package com.example.myapplication

import java.net.Socket
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.PrintWriter

class ClientThread(private val serverIp: String, private val port: Int) : Thread() {

    override fun run() {
        try {
            val socket = Socket(serverIp, port)
            val writer = PrintWriter(socket.getOutputStream(), true)
            val reader = BufferedReader(InputStreamReader(socket.getInputStream()))

            // Send a message to the server
            writer.println("Hello, Server!")
            val response = reader.readLine()
            println("Server response: $response")

            // Close the socket
            socket.close()
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}
