package com.example.myapplication

import java.net.ServerSocket
import java.net.Socket
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.PrintWriter

class ServerThread : Thread() {
    private lateinit var serverSocket: ServerSocket
    private val port = 12345

    override fun run() {
        try {
            serverSocket = ServerSocket(port)
            println("Server is running on port $port")

            while (true) {
                val clientSocket = serverSocket.accept()
                handleClient(clientSocket)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun handleClient(clientSocket: Socket) {
        try {
            val reader = BufferedReader(InputStreamReader(clientSocket.getInputStream()))
            val writer = PrintWriter(clientSocket.getOutputStream(), true)

            var message: String?
            while (reader.readLine().also { message = it } != null) {
                println("Received: $message")
                writer.println("Message received: $message")
            }
        } catch (e: Exception) {
            e.printStackTrace()
        } finally {
            clientSocket.close()
        }
    }
}
