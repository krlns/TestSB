import os
import re
import chardet
import zlib


class SloganSearcher:
    slogans = {
        "Свобода и равенство",
        "Долой коррупцию",
        "За справедливость",
        "Наше время настало",
        "Нет войне",
        "Слава Украине"
    }

    RUSSIAN_ENCODINGS = [
        'utf-8',
        'windows-1251',
        'koi8-r',
        'iso-8859-5',
        'mac-cyrillic',
        'cp866'
    ]

    @staticmethod
    def find_scattered_slogan(text, slogan):
        words = slogan.split()
        slogan_no_spaces = ''.join(words)

        pattern = r'\b' + r'\b.*?\b'.join(re.escape(word) for word in words) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            return True

        text_no_spaces = re.sub(r'\s+', '', text)
        if re.search(re.escape(slogan_no_spaces), text_no_spaces, re.IGNORECASE):
            return True

        found_words = []

        def search_word(text, keyword, index, current_pos):
            if index == len(keyword):
                return True
            for i in range(current_pos, len(text)):
                if text[i] == keyword[index]:
                    if search_word(text, keyword, index + 1, i + 1):
                        return True
            return False
        for keyword in words:
            if search_word(text, keyword, 0, 0):
                found_words.append(keyword)

        return found_words == words

    @staticmethod
    def detect_encoding(file_path):
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)
        result = chardet.detect(raw_data)
        encoding = result['encoding']

        if encoding is None or encoding.lower() not in SloganSearcher.RUSSIAN_ENCODINGS:
            for enc in SloganSearcher.RUSSIAN_ENCODINGS:
                try:
                    with open(file_path, 'rb') as f:
                        data = f.read().decode(enc)
                        return enc
                except UnicodeDecodeError:
                    continue
        return encoding

    @staticmethod
    def search_in_binary(file_path):
        encoding = SloganSearcher.detect_encoding(file_path)
        with open(file_path, 'rb') as f:
            data = f.read()

            try:
                text_data = data.decode(encoding, errors='ignore')
            except UnicodeDecodeError:
                text_data = data.decode('latin1', errors='ignore')

            found_slogans = set()
            for slogan in SloganSearcher.slogans:
                if SloganSearcher.find_scattered_slogan(text_data, slogan):
                    found_slogans.add(slogan)

            return found_slogans

    @staticmethod
    def decompress_and_search(file_path):
        with open(file_path, 'rb') as f:
            data = f.read()

            try:
                decompressed_data = zlib.decompress(data)
                decompressed_text = decompressed_data.decode('utf-8', errors='ignore')

                found_slogans = set()
                for slogan in SloganSearcher.slogans:
                    if SloganSearcher.find_scattered_slogan(decompressed_text, slogan):
                        found_slogans.add(slogan)
            except (zlib.error, UnicodeDecodeError):
                return set()

            return found_slogans

    @staticmethod
    def xor_decrypt(data, key):
        return bytes([byte ^ key for byte in data])

    @staticmethod
    def xor_search(file_path):
        with open(file_path, "rb") as f:
            data = f.read()

        found_slogans = set()
        for key in range(256):
            decrypted_data = SloganSearcher.xor_decrypt(data, key)
            try:
                for enc in SloganSearcher.RUSSIAN_ENCODINGS:
                    decrypted_text = decrypted_data.decode(enc, errors='ignore')
                    for slogan in SloganSearcher.slogans:
                        if SloganSearcher.find_scattered_slogan(decrypted_text, slogan):
                            found_slogans.add(slogan)
            except UnicodeDecodeError:
                continue
        return found_slogans

    @staticmethod
    def is_xor_encrypted(file_path):
        with open(file_path, "rb") as f:
            data = f.read()

        try:
            text = data.decode("utf-8")
            return False
        except UnicodeDecodeError:
            return True

    @staticmethod
    def is_compressed(file_path):
        with open(file_path, 'rb') as f:
            data = f.read()
            try:
                zlib.decompress(data)
                return True
            except zlib.error:
                return False

    @staticmethod
    def analyze_binary_file(file_path):
        found_slogans = set()

        if SloganSearcher.is_compressed(file_path):
            found_slogans.update(SloganSearcher.decompress_and_search(file_path))
        elif SloganSearcher.is_xor_encrypted(file_path):
            found_slogans.update(SloganSearcher.xor_search(file_path))
        else:
            found_slogans.update(SloganSearcher.search_in_binary(file_path))

        return found_slogans

    @staticmethod
    def search_in_directory(directory_path):
        found_slogans = {}
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                if not file.lower().endswith(('.exe', '.bin', '.dll', '.pdf', '.docx', ".txt")):
                    continue

                slogans_found = SloganSearcher.analyze_binary_file(file_path)
                if slogans_found:
                    found_slogans[file_path] = slogans_found
        return found_slogans

    @staticmethod
    def print_results(path):
        if os.path.isfile(path):
            found_slogans = SloganSearcher.analyze_binary_file(path)
            if found_slogans:
                print(f"[INFO]: В файле {path} найдены следующие лозунги:")
                for slogan in found_slogans:
                    print(f"  - {slogan}")
            else:
                print(f"[INFO]: В файле {path} не найдено политических лозунгов.")
        elif os.path.isdir(path):
            found_slogans = SloganSearcher.search_in_directory(path)
            if found_slogans:
                for file_path, slogans in found_slogans.items():
                    print(f"[INFO]: В файле {file_path} найдены следующие лозунги:")
                    for slogan in slogans:
                        print(f"  - {slogan}")
            else:
                print("[INFO]: Политические лозунги не найдены.")
        else:
            print("[WARN]:  Указанный путь не существует или не является файлом/директорией.")


if __name__ == "__main__":
    path = input("[*]: Введите путь к файлу или директории для поиска: ")
    SloganSearcher.print_results(path)
