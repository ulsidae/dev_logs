import os, time, wave, sys, tempfile

if sys.platform == "win32":
    import winsound


def trim_and_speed_up(file_path, start=0.05, end=0.2, speed_factor=3.0):
    with wave.open(file_path, 'rb') as wf:
        params = wf.getparams()
        frame_rate = int(params.framerate * speed_factor)
        start_frame = int(params.framerate * start)
        end_frame = int(params.framerate * end)

        wf.setpos(start_frame)
        audio_frames = wf.readframes(end_frame - start_frame)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with wave.open(temp_file.name, 'wb') as wf:
        wf.setnchannels(params.nchannels)
        wf.setsampwidth(params.sampwidth)
        wf.setframerate(frame_rate)
        wf.writeframes(audio_frames)

    return temp_file.name


def play_wav(file_path):
    try:
        processed_wav = trim_and_speed_up(file_path, start=0.15, end=0.35, speed_factor=1.023)
        if sys.platform == "win32":
            winsound.PlaySound(processed_wav, winsound.SND_FILENAME)
        else:
            os.system(f"aplay {processed_wav}" if sys.platform == "linux" else f"afplay {processed_wav}")
        os.remove(processed_wav)
    except FileNotFoundError:
        print(f"error) File not found: {file_path}")


def play_sequence(input_text, wav_folder="./wav_files"):
    silence_duration = 0.1  #wait 0.1sec

    for part in input_text.split(" "):
        if part == "@": #function like space key
            time.sleep(silence_duration)
        else:
            file_path = os.path.join(wav_folder, f"{part}.wav")
            if os.path.exists(file_path):
                play_wav(file_path)
            else:
                print(f"error) File not found: {file_path}")


if __name__ == "__main__":
    while True:
        user_input = input("input text: ")
        if user_input.strip() == 'exit': #literally stop process
            break
        play_sequence(user_input)
