from char_symbol_map import CharSymbolMap


def main():
    initial_message = "Sofi and Moriya!"
    char_map = CharSymbolMap(16, 3)

    encoded_message = [char_map.char_to_symbol(char) for char in initial_message]

    print(encoded_message)

    decoded_message = "".join([char_map.symbol_to_char(sym) for sym in encoded_message])

    print(decoded_message)


if __name__ == '__main__':
    main()
