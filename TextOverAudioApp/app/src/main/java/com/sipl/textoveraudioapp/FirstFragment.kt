package com.sipl.textoveraudioapp

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
    ): View? {

        _binding = FragmentFirstBinding.inflate(inflater, container, false)
        return binding.root

    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val python: Python = Python.getInstance();

        val textOverSoundModule: PyObject = python.getModule("text_over_sound");
        val textOverSound: PyObject = textOverSoundModule.callAttr("TextOverSound",250, 10, 20, 16, 3, 16);

        binding.sendMessage.setOnClickListener {
            val inputText: String = binding.messageInput.text.toString();

            val encodedMessage = textOverSound.callAttr("string_to_pcm_data", inputText).toJava(ByteArray::class.java);

            val buffSize = AudioTrack.getMinBufferSize(
                16000,
                AudioFormat.CHANNEL_OUT_MONO,
                AudioFormat.ENCODING_PCM_16BIT
            )

            val audio = AudioTrack(
                AudioManager.STREAM_MUSIC,
                16000,  //sample rate
                AudioFormat.CHANNEL_OUT_MONO,  //2 channel
                AudioFormat.ENCODING_PCM_16BIT,  // 16-bit
                buffSize,
                AudioTrack.MODE_STREAM
            )

            audio.play();
            audio.write(encodedMessage, 0, encodedMessage.size);
            audio.stop();
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