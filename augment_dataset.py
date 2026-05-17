import random

# Read original dataset
with open("SMSSpamCollection", "r", encoding="latin-1") as file:
    lines = file.readlines()

augmented_lines = []

def augment_text(text):
    words = text.split()
    
    if len(words) > 3:
        i = random.randint(0, len(words)-1)
        words[i] = words[i] + "!!!"
    
    return " ".join(words)

# Create augmented data
for line in lines:
    parts = line.strip().split("\t")
    
    if len(parts) == 2:
        label = parts[0]
        message = parts[1]
        
        new_message = augment_text(message)
        
        augmented_lines.append(f"{label}\t{new_message}\n")

# Combine original + augmented
final_data = lines + augmented_lines

# Remove duplicates
final_data = list(set(final_data))

# Save new dataset
with open("final_dataset.txt", "w", encoding="latin-1") as file:
    file.writelines(final_data)

print("Dataset increased to:", len(final_data))