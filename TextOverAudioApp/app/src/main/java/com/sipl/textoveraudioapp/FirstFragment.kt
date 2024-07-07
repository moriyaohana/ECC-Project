package com.sipl.textoveraudioapp

import android.content.SharedPreferences
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
import androidx.preference.PreferenceManager
import com.chaquo.python.Python
import com.sipl.textoveraudioapp.databinding.FragmentFirstBinding
import kotlin.math.roundToInt


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

    private fun constructTransmitterWrapperFromPreferences(python: Python, sharedPreferences: SharedPreferences): TransmitterWrapper {
        // TODO: Should validate preferences
        return TransmitterWrapper(
            python,
            sharedPreferences.getString("symbol_weight", null)!!.toInt(),
            sharedPreferences.getString("symbol_size", null)!!.toInt(),
            sharedPreferences.getString("samples_per_symbol", null)!!.toInt(),
            sharedPreferences.getString("sample_rate_hz", null)!!.toFloat(),
            sharedPreferences.getString("frequency_range_start_hz", null)!!.toFloat(),
            sharedPreferences.getString("frequency_range_end_hz", null)!!.toFloat(),
            sharedPreferences.getString("ecc_symbols", null)!!.toInt(),
            sharedPreferences.getString("ecc_block", null)!!.toInt(),
            sharedPreferences.getString("snr_threshold", null)!!.toFloat())
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val python: Python = Python.getInstance()
        val sharedPreferences = PreferenceManager.getDefaultSharedPreferences(requireContext())

        var transmitter = constructTransmitterWrapperFromPreferences(python, sharedPreferences)

        val onSharedPreferenceChangeCallback = { newSharedPreferences: SharedPreferences, _: String? ->
            transmitter = constructTransmitterWrapperFromPreferences(python, newSharedPreferences)
        }

        sharedPreferences.registerOnSharedPreferenceChangeListener(onSharedPreferenceChangeCallback)

        //event: the user sending a message
        binding.sendMessage.setOnClickListener {
            val inputText: String = binding.messageInput.text.toString()
            messageToSound(transmitter.transmitBuffer(inputText.encodeToByteArray()), transmitter.sampleRateHz)
        }

        binding.buttonFirst.setOnClickListener {
            findNavController().navigate(R.id.action_FirstFragment_to_SecondFragment)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun messageToSound(messageData: ByteArray, sampleRateHz: Float ){
        val buffSize = AudioTrack.getMinBufferSize(
            sampleRateHz.roundToInt(),
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
                .setSampleRate(sampleRateHz.roundToInt())
                .build(),
            buffSize,
            AudioTrack.MODE_STREAM,
            AudioManager.AUDIO_SESSION_ID_GENERATE
        )

        audio.play()
        audio.write(messageData, 0, messageData.size)
        audio.stop()
    }
}
