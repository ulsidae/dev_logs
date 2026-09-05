Add-Type -AssemblyName System.Speech

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer

$synth.SelectVoice("Microsoft Zira Desktop")

$synth.Speak("Hello world!")
