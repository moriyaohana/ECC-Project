package com.sipl.textoveraudioapp

import android.annotation.SuppressLint
import android.content.SharedPreferences
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.activity.result.contract.ActivityResultContracts
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.preference.PreferenceManager
import com.chaquo.python.Python
import com.sipl.textoveraudioapp.databinding.FragmentReceiverBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.nio.ByteBuffer
import kotlin.time.measureTime


/**
 * A simple [Fragment] subclass as the default destination in the navigation.
 */
class ReceiverFragment : Fragment() {

    private var _binding: FragmentReceiverBinding? = null

    // This property is only valid between onCreateView and
    // onDestroyView.
    private val binding get() = _binding!!
    private lateinit var receiver : ReceiverWrapper
    private var audioProcessingJob: Job? = null

    private var isReceivingMessage = false
    private val bufferSize = 4096
    private var allDataShort = ArrayList<Short>()
    private var allDataBytes = ArrayList<Byte>()
    private lateinit var audioRecord: AudioRecord


    private val isReceiving = false

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {

        val python: Python = Python.getInstance()
        val sharedPreferences = PreferenceManager.getDefaultSharedPreferences(requireContext())

        receiver = constructReceiverWrapperFromPreferences(python, sharedPreferences)

        val onSharedPreferenceChangeCallback = { newSharedPreferences: SharedPreferences, _: String? ->
            receiver = constructReceiverWrapperFromPreferences(python, newSharedPreferences)
        }

        sharedPreferences.registerOnSharedPreferenceChangeListener(onSharedPreferenceChangeCallback)


        _binding = FragmentReceiverBinding.inflate(inflater, container, false)
        return binding.root

    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val requestPermissionLauncher =
            registerForActivityResult(
                ActivityResultContracts.RequestPermission()
            ) { isGranted: Boolean ->
                if (!isGranted) {
                    throw RuntimeException("No recording permissions granted")
                }
            }

        requestPermissionLauncher.launch(android.Manifest.permission.RECORD_AUDIO)

        //event: the user sending a message
        binding.receive.setOnClickListener {
            receiveClicked()
        }

        binding.toTransitter.setOnClickListener {
            findNavController().navigate(R.id.action_ReceiverFragment_to_TransmitterFragment)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun constructReceiverWrapperFromPreferences(python: Python, sharedPreferences: SharedPreferences): ReceiverWrapper {
        // TODO: Should validate preferences
        return ReceiverWrapper(
            python,
            sharedPreferences.getString("symbol_weight", null)!!.toInt(),
            sharedPreferences.getString("symbol_size", null)!!.toInt(),
            sharedPreferences.getString("samples_per_symbol", null)!!.toInt(),
            sharedPreferences.getString("sample_rate_hz", null)!!.toFloat(),
            sharedPreferences.getString("frequency_range_start_hz", null)!!.toFloat(),
            sharedPreferences.getString("frequency_range_end_hz", null)!!.toFloat(),
            sharedPreferences.getString("ecc_symbols", null)!!.toInt(),
            sharedPreferences.getString("ecc_block", null)!!.toInt(),
            sharedPreferences.getString("snr_threshold", null)!!.toFloat(),
            sharedPreferences.getString("correlation_threshold", null)!!.toFloat())
    }

    private fun receiveClicked() {
        if (audioProcessingJob == null) {
            startListening()
        }
        else {
            stopListening()
        }
    }

    private fun stopListening() {
        audioProcessingJob?.cancel()
        audioProcessingJob = null
        audioRecord.stop()
        audioRecord.release()
        isReceivingMessage = false

        binding.receive.text = "receive"
    }

    @SuppressLint("MissingPermission")
    private fun startListening() {
        binding.receive.text = "listening..."

        val RESERVED_BUFFER_FACTOR = 16
        audioRecord = AudioRecord(
            MediaRecorder.AudioSource.MIC,
            receiver.sampleRateHz.toInt(),
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            RESERVED_BUFFER_FACTOR * receiver.samplesPerSymbol
        )

        audioRecord.startRecording()

        audioProcessingJob = lifecycleScope.launch(Dispatchers.IO) {
            val audioBuffer = ShortArray(receiver.samplesPerSymbol)
            while (isActive) {
                val t = measureTime {
                    audioRecord.read(audioBuffer, 0, audioBuffer.size)
//                    val receivedBytes = shortArrayToByteArray(audioBuffer)
                    receiver.receivePcmBuffer(audioBuffer)
                    val isSynchronised = receiver.isSynchronised()
                    if (!isReceivingMessage && isSynchronised) {
                        withContext(Dispatchers.Main) {
                            updateMessageView()
                        }
                    } else if (isReceivingMessage && !isSynchronised) {
                        withContext(Dispatchers.Main) {
                            binding.receive.text = "receiving message..."
                        }
                    }
                    isReceivingMessage = isSynchronised
//                    allDataBytes.addAll(receivedBytes.asIterable())
                    allDataShort.addAll(audioBuffer.asIterable())
                }
                Log.d("Timing", "Block took $t")
            }
        }
    }

    private fun updateMessageView() {

    }

    private fun shortArrayToByteArray(shortArray: ShortArray): ByteArray {
        val byteArray = ByteArray(shortArray.size * 2)
        var index = 0
        shortArray.forEach {
            byteArray[index++] = (it.toInt() shr 8).toByte()
            byteArray[index++] = it.toByte()
        }

        return byteArray
    }
}
