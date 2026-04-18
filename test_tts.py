import os

text = "Your bank account is compromised. Share OTP immediately."

# Save audio
os.system(f'say -o test.aiff "{text}"')

# Convert to wav
os.system("afconvert test.aiff test.wav")

print("✅ Audio generated: test.wav")