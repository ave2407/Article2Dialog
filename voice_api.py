import os
import random
import re
import sys
import wave
import xml.etree.ElementTree as ET

import grpc

sys.path.append(os.path.abspath("cueta_repo/voicekitexamples_fold/python/"))
sys.path.append(os.path.abspath("cueta_repo/voicekitexamples_fold/python/tinkoff"))
sys.path.insert(0, "cueta_repo/voicekitexamples_fold/python/tinkoff")
sys.path.append("..")
from voicekitexamples_fold.python.tinkoff.cloud.tts.v1 import tts_pb2_grpc, tts_pb2

endpoint = os.environ.get("VOICEKIT_ENDPOINT") or "api.tinkoff.ai:443"
api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InIxUGNSUGsvMVo3WG9QSGxIS3d2cmdWUkxnQ1ZFTnByRHZPK1ArODM2NHM9VFRTX1RFQU0ifQ.eyJpc3MiOiJ0ZXN0X2lzc3VlciIsInN1YiI6InRlc3RfdXNlciIsImF1ZCI6InRpbmtvZmYuY2xvdWQudHRzIiwiZXhwIjoxNzMwMDM0Nzc1LjB9.uxrnKrgaCHxlG4DvB7ekslZ9dtSn-eDc2hw82fAJhFM'
sample_rate = 48000


def add_breaks_before_words(text,
                            words=["объясни", "Помоги", "помоги", "помоги понять", "разъясни", "поясни", "расскажи",
                                   "объясни это", "помоги разобраться", "расскажи понятнее", "разложи на простые",
                                   "поможешь понять?", "объясни, что тут", "разберись со мной", "поясни, о чём",
                                   "расскажи проще", "поможешь объяснить?", "объясни подробнее", "подскажи главное",
                                   "помоги мне понять", "поясни главное", "разъясни это", "помоги понять смысл",
                                   "расшифруй", "покажи суть", "объясни значимость", "Объясни", "Помоги",
                                   "Помоги понять", "Объясни", "Разъясни", "Поясни", "Расскажи",
                                   "Объясни это", "Помоги разобраться", "Расскажи понятнее", "Разложи на простые",
                                   "Поможешь понять?", "Объясни, что тут", "Разберись со мной", "Поясни, о чём",
                                   "Расскажи проще", "Поможешь объяснить?", "Объясни подробнее", "Подскажи главное",
                                   "Помоги мне понять", "Поясни главное", "Разъясни это", "Помоги понять смысл",
                                   "Расшифруй", "Покажи суть", "Объясни значимость", "Привет", " привет", "привет",
                                   "Да", "да"], break_tag='<break time="300ms"/>'):
    pattern = r'\b(' + '|'.join(map(re.escape, words)) + r')\b'

    def insert_break(match):
        return f'{break_tag} {match.group(0)}'

    modified_text = re.sub(pattern, insert_break, text, flags=re.IGNORECASE)

    return modified_text


def add_breaks_punctuations(text, words=["."], break_tag='<break time="150ms"/>'):
    # Create a pattern that matches the specified punctuation marks
    pattern = r'(' + '|'.join(map(re.escape, words)) + r')'

    def insert_break(match):
        return f'{break_tag} {match.group(0)}'

    modified_text = re.sub(pattern, insert_break, text, flags=re.IGNORECASE)

    return modified_text


def insert_prosody_tags(text, insert_probability=1):
    def prosody_insertion(match):
        voice_tag = match.group(1)
        content = match.group(2)
        sentences = re.split(r'(?<=[.!?])\s+', content)

        for i in range(len(sentences)):
            if random.random() < insert_probability:
                # Split the sentence by spaces but retain existing tags
                words = re.findall(r'<[^>]+>|[^<>\s]+', sentences[i])
                eligible_indices = [j for j, w in enumerate(words) if not re.match(r'<[^>]+>', w)]
                if len(eligible_indices) > 3:
                    num_words = random.randint(1, min(4, len(eligible_indices)))
                    selected_indices = sorted(random.sample(eligible_indices, num_words))
                    for index in selected_indices:
                        words[index] = f'<prosody pitch="102%" rate="75%">{words[index]}</prosody>'
                    sentences[i] = ' '.join(words)
        modified_content = ' '.join(sentences)
        return f'{voice_tag}{modified_content}'

    pattern = r'(<voice[^>]*>)(.*?</voice>)'
    modified_text = re.sub(pattern, prosody_insertion, text, flags=re.DOTALL)
    if not re.search(r'<speak>', text, re.IGNORECASE):
        final_ssml = f"<speak>{modified_text}</speak>"
    else:
        final_ssml = modified_text

    return final_ssml


def make_kovalev_human_like_faster(ssml_content):
    tree = ET.ElementTree(ET.fromstring(ssml_content))
    root = tree.getroot()

    desired_pitch = "90%"
    desired_rate = "110%"

    for voice in root.findall('.//voice'):
        if voice.get('name') == 'kovalev':
            for prosody in voice.findall('.//prosody'):
                prosody.set('pitch', desired_pitch)
                prosody.set('rate', desired_rate)

            for elem in voice.iter():
                if elem.tag not in ['prosody', 'emphasis', 's', 'p']:
                    continue
                if 'prosody' not in elem.tag:

                    parent = elem
                    for child in list(parent):
                        if child.tag == 'prosody':
                            child.set('pitch', desired_pitch)
                            child.set('rate', desired_rate)

            global_prosody = ET.Element('prosody', attrib={'pitch': desired_pitch, 'rate': desired_rate})

            for child in list(voice):
                voice.remove(child)
                global_prosody.append(child)
            voice.append(global_prosody)

    for break_tag in root.findall('.//voice[@name="kovalev"]//break'):
        current_time = break_tag.get('time')
        if current_time.endswith('ms'):
            time_ms = int(current_time.replace('ms', ''))
            new_time_ms = max(time_ms - 200, 100)
            break_tag.set('time', f"{new_time_ms}ms")
        elif current_time.endswith('s'):
            time_s = float(current_time.replace('s', ''))
            new_time_s = max(time_s - 0.2, 0.1)
            break_tag.set('time', f"{new_time_s}s")
    return ET.tostring(root, encoding='unicode')


def voice_synth(wav_output_path, prompt_path=None, prompt_text=None):
    if prompt_path is not None:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
    else:
        prompt = prompt_text

    prompt = insert_prosody_tags(prompt)
    prompt = add_breaks_before_words(prompt)
    prompt = add_breaks_punctuations(prompt)
    prompt = make_kovalev_human_like_faster(prompt)
    print(prompt)

    def build_request():
        return tts_pb2.SynthesizeSpeechRequest(
            input=tts_pb2.SynthesisInput(
                ssml=prompt
            ),
            audio_config=tts_pb2.AudioConfig(
                audio_encoding=tts_pb2.LINEAR16,
                sample_rate_hertz=sample_rate,
            ),
        )

    with wave.open(wav_output_path, "wb") as f:
        f.setframerate(sample_rate)
        f.setnchannels(1)
        f.setsampwidth(2)

        stub = tts_pb2_grpc.TextToSpeechStub(grpc.secure_channel(endpoint, grpc.ssl_channel_credentials()))
        request = build_request()
        metadata = [("authorization", f"Bearer {api_key}")]
        responses = stub.StreamingSynthesize(request, metadata=metadata)
        for stream_response in responses:
            f.writeframes(stream_response.audio_chunk)
