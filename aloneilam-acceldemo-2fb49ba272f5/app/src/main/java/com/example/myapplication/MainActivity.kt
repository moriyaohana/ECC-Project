package com.example.myapplication

import android.graphics.Color
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import android.content.Context
import android.net.wifi.WifiManager
import android.text.format.Formatter
import android.widget.TextView


class MainActivity : AppCompatActivity(), SensorEventListener {

    private lateinit var sensorManager: SensorManager
    private var accelerometer: Sensor? = null
    private lateinit var rgbView: RGBView
    private val handler = Handler(Looper.getMainLooper())

    private val updateInterval = 100L // 100 milliseconds

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        rgbView = RGBView(this, bufferSize = 100) // Buffer size for 10 seconds with updates every 100ms
        setContentView(rgbView)

        sensorManager = getSystemService(SENSOR_SERVICE) as SensorManager
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)

        val ipAddress = getIpAddress()
        Log.d("MainActivity", "IP Address: $ipAddress")
//        val ipAddressTextView: TextView = findViewById(R.id.ipAddressTextView)
//        ipAddressTextView.text = "IP Address: $ipAddress"

    }

    private fun getIpAddress(): String? {
        val wifiManager = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
        val ipAddress = wifiManager.connectionInfo.ipAddress
        return Formatter.formatIpAddress(ipAddress)
    }

    override fun onResume() {
        super.onResume()
        accelerometer?.also { sensor ->
            sensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_UI)
        }
        handler.post(updateRunnable)
    }

    override fun onPause() {
        super.onPause()
        sensorManager.unregisterListener(this)
        handler.removeCallbacks(updateRunnable)
    }

    private val updateRunnable = object : Runnable {
        override fun run() {
            handler.postDelayed(this, updateInterval)
        }
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event?.sensor?.type == Sensor.TYPE_ACCELEROMETER) {
            val x = event.values[0]
            val y = event.values[1]
            val z = event.values[2]
            // print x y z values to logcat

            val red = ((x + 10) / 20 * 255).toInt().coerceIn(0, 255)
            val green = ((y + 10) / 20 * 255).toInt().coerceIn(0, 255)
            val blue = ((z + 10) / 20 * 255).toInt().coerceIn(0, 255)

//            val rgbValue = RGBValue(red, green, blue)
//            Log.d("RGBValue", "Red: ${rgbValue.red}, Green: ${rgbValue1.green}, Blue: ${rgbValue.blue}")

            val snrDb = 5.0 // Define your desired SNR in dB

            val noisyRGBValue = addNoiseToRGB(red, green, blue, snrDb)

// Print noisy RGB values to Logcat
            Log.d("NoisyRGBValues", "Red: ${noisyRGBValue.red}, Green: ${noisyRGBValue.green}, Blue: ${noisyRGBValue.blue}")

            val rgbValue = RGBValue(noisyRGBValue.red, noisyRGBValue.green, noisyRGBValue.blue)

            rgbView.addRGBValue(noisyRGBValue)
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
        // We can ignore this for now
    }
}
