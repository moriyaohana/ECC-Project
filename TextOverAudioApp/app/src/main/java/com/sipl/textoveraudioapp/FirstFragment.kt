package com.sipl.textoveraudioapp

import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
import android.os.Bundle
import androidx.fragment.app.Fragment
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.navigation.fragment.findNavController
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.sipl.textoveraudioapp.databinding.FragmentFirstBinding
import java.nio.ByteBuffer

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
    ): View? {

        _binding = FragmentFirstBinding.inflate(inflater, container, false)
        return binding.root

    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val python: Python = Python.getInstance();
        val textOverAudioModule: PyObject = python.getModule("text_over_audio");
        val textOverAudio: PyObject = textOverAudioModule.callAttr("TextOverAudio",250, 10, 20, 16, 3, 16);

        binding.sendMessage.setOnClickListener {
            val inputText: String = binding.messageInput.text.toString();

            val messageSound = textOverAudio.callAttr("string_to_pcm_data", inputText).toJava(ByteBuffer)

            val bufferSize = AudioTrack.getMinBufferSize(16,
                AudioFormat.CHANNEL_OUT_MONO,
                AudioFormat.ENCODING_PCM_16BIT);

            val audioTrack = AudioTrack(AudioManager.STREAM_MUSIC,
                16000,
                AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT,
                bufferSize,
                AudioTrack.MODE_STREAM);

            audioTrack.play();
            audioTrack.write()

            val stringBuilder = StringBuilder()
            for ((index, innerList) in encodedMessage.withIndex()) {
                stringBuilder.append("Symbol $index: $innerList\n");
            }



            binding.textView.text = stringBuilder.toString();
        }


        binding.buttonFirst.setOnClickListener {
            findNavController().navigate(R.id.action_FirstFragment_to_SecondFragment)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}