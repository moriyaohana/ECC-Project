package com.sipl.textoveraudioapp

import android.content.SharedPreferences
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.View.OnClickListener
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import androidx.preference.PreferenceManager
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.sipl.textoveraudioapp.databinding.FragmentTransmitterBinding
import java.util.concurrent.CompletableFuture
import kotlin.math.roundToInt


/**
 * A simple [Fragment] subclass as the default destination in the navigation.
 */
class TransmitterFragment : Fragment() {

    private var _binding: FragmentTransmitterBinding? = null

    // This property is only valid between onCreateView and
    // onDestroyView.
    private val binding get() = _binding!!
    private var sendingFuture: CompletableFuture<Void>? = null
    private val sendingHandler = Handler(Looper.getMainLooper())
    private var isSending = false
    private lateinit var transmitter : TransmitterWrapper

    override fun onCreateView(
            inflater: LayoutInflater, container: ViewGroup?,
            savedInstanceState: Bundle?
    ): View {

        val python: Python = Python.getInstance()
        val sharedPreferences = PreferenceManager.getDefaultSharedPreferences(requireContext())

        transmitter = constructTransmitterWrapperFromPreferences(python, sharedPreferences)

        val onSharedPreferenceChangeCallback = { newSharedPreferences: SharedPreferences, _: String? ->
            transmitter = constructTransmitterWrapperFromPreferences(python, newSharedPreferences)
        }

        sharedPreferences.registerOnSharedPreferenceChangeListener(onSharedPreferenceChangeCallback)


        _binding = FragmentTransmitterBinding.inflate(inflater, container, false)
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
            sendClicked(it)
        }

        binding.toReceiver.setOnClickListener {
            findNavController().navigate(R.id.action_TransmitterFragment_to_ReceiverFragment)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
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

    private fun sendClicked(v: View) {
        if (sendingFuture == null || sendingFuture!!.isDone) {
            sendMessage()
        }
        else {
            cancelMessage()
        }
    }

    private fun sendMessage() {
        binding.sendMessage.text = getString(R.string.sending)
        binding.sendMessage.isClickable = false
        binding.toReceiver.isClickable = false

        sendingFuture = CompletableFuture.runAsync {
            try {
                val inputText: String = binding.messageInput.text.toString()
                messageToSound(
                    transmitter.transmitBuffer(inputText.encodeToByteArray()),
                    transmitter.sampleRateHz
                )
            }
            catch (_: InterruptedException) {
                Log.e("Transmitter", "Interupted got to sendMessage")
            }
        }.thenRun {
            sendingHandler.post {
                binding.sendMessage.text = getString(R.string.send)
                binding.toReceiver.isClickable = true
                binding.sendMessage.isClickable = true
            }
        }

        sendingFuture!!.handle {_, _ ->
            sendingHandler.post {
                Log.e("Transmitter", "Got to handler")
                binding.sendMessage.text = getString(R.string.send)
                binding.toReceiver.isClickable = true
                binding.sendMessage.isClickable = true
            }
        }
    }

    private fun cancelMessage() {
        // TODO: Canceling doesn't work
        sendingFuture?.cancel(true)
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

        try {
            audio.play()
            audio.write(messageData, 0, messageData.size)
            audio.stop()
        }
        catch (exception: InterruptedException) {
            Log.e("Transmitter", "Interrupted during audio play")
            audio.stop()
        }
    }
}
