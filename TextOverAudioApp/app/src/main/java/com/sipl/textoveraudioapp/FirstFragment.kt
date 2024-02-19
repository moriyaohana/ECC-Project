package com.sipl.textoveraudioapp

import android.os.Bundle
import androidx.fragment.app.Fragment
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
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
        val charSymbolMapModule: PyObject = python.getModule("char_symbol_map");
        val charSymbolMap: PyObject = charSymbolMapModule.callAttr("CharSymbolMap",16, 3, 256);

        binding.sendMessage.setOnClickListener {
            val inputText: String = binding.messageInput.text.toString();

            val encodedMessage = charSymbolMap.callAttr("string_to_symbols", inputText).asList();

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