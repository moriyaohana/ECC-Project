package com.example.myapplication
import android.util.Log
import java.util.Random
import kotlin.math.pow
import kotlin.math.sqrt

fun addNoiseToRGB(red: Int, green: Int, blue: Int, snrDb: Double): RGBValue {
    val random = Random()  // Java's Random

    // Convert SNR from dB to linear scale
    val snrLinear = 10.0.pow(snrDb / 10.0)

    // Calculate the power of the signal
    val signalPower = 255.0.pow(2) / 3.0  // Max RGB value squared and averaged over 3 channels

    // Calculate noise power based on the SNR
    val noisePower = signalPower / snrLinear

    // Standard deviation of the noise
    val noiseStd = sqrt(noisePower)

    // Generate Gaussian noise for each channel using Java's Random
    val redNoise = (random.nextGaussian() * noiseStd).toInt()
    val greenNoise = (random.nextGaussian() * noiseStd).toInt()
    val blueNoise = (random.nextGaussian() * noiseStd).toInt()

    // Add noise to each channel and clip the values to [0, 255]
    val noisyRed = (red + redNoise).coerceIn(0, 255)
    val noisyGreen = (green + greenNoise).coerceIn(0, 255)
    val noisyBlue = (blue + blueNoise).coerceIn(0, 255)

    return RGBValue(noisyRed, noisyGreen, noisyBlue)
}



