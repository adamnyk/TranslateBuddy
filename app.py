import deepl
from secret import AUTH_KEY


translator = deepl.Translator(AUTH_KEY)
languages = [l.name for l in translator.get_target_languages()]


# result = translator.translate_text("Hello, wild one!", target_lang="FR")
# print(result.text)  # "Bonjour, le monde !"

# result = translator.translate_document_from_filepath(input_path="phrases.txt", output_path="result.txt", target_lang="FR")
# print(result.text)  # "Bonjour, le monde !"

with open('phrases.txt') as f1, open('result.txt') as f2:
    for l1, l2 in zip(f1,f2):
        print(l1 + '          ' + l2)