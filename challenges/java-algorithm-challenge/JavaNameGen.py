import subprocess

while True:
    text = input("Input name: ")

    filename = "".join(word.capitalize() for word in text.split()) + ".java"

    subprocess.run(
        "clip",
        input=filename,
        text=True,
        shell=True
    )

    print(f"Copied: {filename}")
