package com.sipl.textoveraudioapp

import android.os.Bundle
import android.text.InputType
import androidx.preference.EditTextPreference
import androidx.preference.PreferenceFragmentCompat

class SettingsFragment : PreferenceFragmentCompat() {

    override fun onCreatePreferences(savedInstanceState: Bundle?, rootKey: String?) {
        setPreferencesFromResource(R.xml.preferences, rootKey)
        setEditTextPreferencesToNumberInput("samples_per_symbol")
        setEditTextPreferencesToNumberInput("frequency_range_start_hz")
        setEditTextPreferencesToNumberInput("frequency_range_end_hz")
        setEditTextPreferencesToNumberInput("symbol_size")
        setEditTextPreferencesToNumberInput("symbol_weight")
        setEditTextPreferencesToNumberInput("sample_rate_hz")
        setEditTextPreferencesToNumberInput("ecc_symbols")
        setEditTextPreferencesToNumberInput("ecc_block")
        setEditTextPreferencesToNumberInput("snr_threshold")
        setEditTextPreferencesToNumberInput("correlation_threshold")
    }

    private fun setEditTextPreferencesToNumberInput(key: String) {
        val preference = preferenceScreen.findPreference<EditTextPreference>(key)
        preference!!.setOnBindEditTextListener { editText ->
            editText.inputType = InputType.TYPE_CLASS_NUMBER
        }
    }
}