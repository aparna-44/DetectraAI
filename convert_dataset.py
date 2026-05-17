input_file = "SMSSpamCollection"
output_file = "sms_dataset.csv"

with open(input_file, "r", encoding="utf-8") as infile, \
     open(output_file, "w", encoding="utf-8") as outfile:
    
    outfile.write("label,message\n")  # header
    
    for line in infile:
        parts = line.strip().split("\t")  # split using TAB
        if len(parts) == 2:
            label = parts[0]
            message = parts[1].replace(",", "")  # remove extra commas inside message
            outfile.write(f"{label},{message}\n")

print("Conversion completed successfully!")