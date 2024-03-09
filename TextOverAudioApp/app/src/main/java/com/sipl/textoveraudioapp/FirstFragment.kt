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
        val textOverSoundModule: PyObject = python.getModule("text_over_sound")
        val textOverSound: PyObject = textOverSoundModule.callAttr("TextOverSound",250, 10, 20, 16, 3, 16)

        //event: the user sending a message
        binding.sendMessage.setOnClickListener {
            val inputText: String = binding.messageInput.text.toString()
            messageToSound(textOverSound, inputText, 16000)
        }




        binding.buttonFirst.setOnClickListener {
            findNavController().navigate(R.id.action_FirstFragment_to_SecondFragment)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun messageToSound(textOverSound: PyObject, inputText: String, sampleRateHz: Int ){
        val encodedMessage = textOverSound.callAttr("string_to_pcm_data", inputText).toJava(ByteArray::class.java)

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
