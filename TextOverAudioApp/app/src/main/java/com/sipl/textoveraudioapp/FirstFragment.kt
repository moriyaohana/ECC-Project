package com.sipl.textoveraudioapp

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.sipl.textoveraudioapp.databinding.FragmentFirstBinding


/**
 * A simple [Fragment] subclass as the default destination in the navigation.
 */
class FirstFragment : Fragment() {

    private var _binding: FragmentFirstBinding? = null

    // This property is only valid between onCreateView and
    // onDestroyView.
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {

        _binding = FragmentFirstBinding.inflate(inflater, container, false)
        return binding.root

    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val python: Python = Python.getInstance()

        //initialization
        val mainModule: PyObject = python.getModule("transmitter")
        val messageToSound: PyObject = mainModule.callAttr("create_transmitter")

        //event: the user sending a message
        binding.sendMessage.setOnClickListener {

            val inputText: String = binding.messageInput.text.toString()
            val byteArray = messageToSound.call(inputText).toJava(ByteArray::class.java)
            playAudio(byteArray)
        }

        binding.buttonFirst.setOnClickListener {
            findNavController().navigate(R.id.action_FirstFragment_to_SecondFragment)
        }
    }

    private fun playAudio(byteArray: ByteArray) {
        // Convert byte array to short array
        val shortArray = byteArrayToShortArray(byteArray)

        // Define the sample rate
        val sampleRate = 16_000

        // Create and configure AudioTrack using AudioTrack.Builder
        val audioTrack = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                    .build()
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setSampleRate(sampleRate)
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                    .build()
            )
            .setBufferSizeInBytes(shortArray.size * 2) // buffer size in bytes
            .setTransferMode(AudioTrack.MODE_STATIC)
            .build()

        // Load the short array data into AudioTrack
        audioTrack.write(shortArray, 0, shortArray.size)

        // Play the audio
        audioTrack.play()
    }


    // Helper function to convert byte array to short array
    private fun byteArrayToShortArray(byteArray: ByteArray): ShortArray {
        val shortArray = ShortArray(byteArray.size / 2)
        for (i in shortArray.indices) {
            shortArray[i] = ((byteArray[2 * i].toInt() and 0xFF) or
                    (byteArray[2 * i + 1].toInt() shl 8)).toShort()
        }
        return shortArray
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun messageToSound(textOverSound: PyObject, inputText: String, sampleRateHz: Int) {
        val encodedMessage =
            textOverSound.callAttr("string_to_pcm_data", inputText).toJava(ByteArray::class.java)

        val buffSize = AudioTrack.getMinBufferSize(
            sampleRateHz,
            AudioFormat.CHANNEL_OUT_MONO,
            AudioFormat.ENCODING_PCM_16BIT
        )

        val audio = AudioTrack(
            AudioAttributes.Builder()
                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .build(),
            AudioFormat.Builder()
                .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                .setSampleRate(sampleRateHz)
                .build(),
            buffSize,
            AudioTrack.MODE_STREAM,
            AudioManager.AUDIO_SESSION_ID_GENERATE
        )

        audio.play()
        audio.write(encodedMessage, 0, encodedMessage.size)
        audio.stop()
    }
}
