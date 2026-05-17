from logger import update_logs, is_blocked
import csv
import string
import math
import random
import PyPDF2
import sys
import os

# -----------------------------
# LOAD DATASET
# -----------------------------
def load_data(filename):
    data = []

    with open(filename, 'r', encoding='latin-1') as file:
        for line in file:
            parts = line.strip().split("\t")

            if len(parts) == 2:
                label = parts[0].strip()
                message = parts[1].strip()

                data.append((label, message))

    return data


# -----------------------------
# TEXT PREPROCESSING
# -----------------------------
def preprocess(text):
    text = text.lower()

    for char in string.punctuation:
        text = text.replace(char, " ")

    words = text.split()

    cleaned_words = []

    for word in words:
        if len(word) > 1:
            cleaned_words.append(word)

    # create bigrams
    bigrams = []
    for i in range(len(cleaned_words) - 1):
        bigram = cleaned_words[i] + "_" + cleaned_words[i + 1]
        bigrams.append(bigram)

    return cleaned_words + bigrams


# -----------------------------
# TRAIN NAIVE BAYES MODEL
# -----------------------------
def train_naive_bayes(data):
    spam_words = {}
    ham_words = {}

    spam_count = 0
    ham_count = 0

    for label, message in data:
        words = preprocess(message)

        if label == "spam":
            spam_count += 1
            for word in words:
                spam_words[word] = spam_words.get(word, 0) + 1
        else:
            ham_count += 1
            for word in words:
                ham_words[word] = ham_words.get(word, 0) + 1

    return spam_words, ham_words, spam_count, ham_count


# -----------------------------
# PREDICTION FUNCTION
# -----------------------------
def predict(message, spam_words, ham_words, spam_count, ham_count):
    words = preprocess(message)

    total_messages = spam_count + ham_count

    # Prior probabilities
    prob_spam = math.log(spam_count / total_messages)
    prob_ham = math.log(ham_count / total_messages)

    # Vocabulary size
    vocabulary = set(list(spam_words.keys()) + list(ham_words.keys()))
    vocab_size = len(vocabulary)

    total_spam_words = sum(spam_words.values())
    total_ham_words = sum(ham_words.values())

    for word in words:
        spam_word_freq = spam_words.get(word, 0)
        ham_word_freq = ham_words.get(word, 0)

        # Laplace smoothing
        prob_spam += math.log((spam_word_freq + 1) / (total_spam_words + vocab_size))
        prob_ham += math.log((ham_word_freq + 1) / (total_ham_words + vocab_size))

    return "spam" if prob_spam > prob_ham else "ham"


# -----------------------------
# TRAIN TEST SPLIT
# -----------------------------
def split_data(data, train_ratio=0.8):
    random.seed(42)
    random.shuffle(data)

    train_size = int(len(data) * train_ratio)

    train_data = data[:train_size]
    test_data = data[train_size:]

    return train_data, test_data


# -----------------------------
# CALCULATE ACCURACY
# -----------------------------
def calculate_accuracy(test_data, spam_words, ham_words, spam_count, ham_count):
    correct = 0
    total = len(test_data)

    for label, message in test_data:
        prediction = predict(message, spam_words, ham_words, spam_count, ham_count)

        if prediction == label:
            correct += 1

    return correct / total


# -----------------------------
# PDF TEXT EXTRACTION (IMPROVED)
# -----------------------------
def extract_text_from_pdf(file, max_chars=5000):
    text = ""

    try:
        # Supports BOTH file path and Streamlit upload
        if hasattr(file, "read"):
            reader = PyPDF2.PdfReader(file)
        else:
            with open(file, "rb") as f:
                reader = PyPDF2.PdfReader(f)

        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted

            # Limit size (important)
            if len(text) > max_chars:
                break

    except Exception as e:
        print("⚠️ Error reading PDF:", e)

    return text


# -----------------------------
# ALERT FUNCTION (FINAL)
# -----------------------------
def send_alert(prediction):
    if prediction == "spam":
        return """🚨 ALERT: Suspicious document detected!
⚠️ Do NOT click links or share personal info.
📢 Report this file immediately."""
    else:
        return "✅ Document seems safe."
    
#-------------------------------
def log_alert(prediction, text):
    if prediction == "spam":
        with open("alerts.txt", "a", encoding="utf-8") as f:
            f.write("🚨 SCAM DETECTED\n")
            f.write(text[:200] + "\n")  # store first 200 chars
            f.write("-" * 40 + "\n")

#----------------------------------
def auto_response(prediction):
    if prediction == "spam":
        return {
            "message": "⚠️ Automated Action: Scam detected. User is advised to block the sender.",
            "action": "🚫 Sender blocked (simulated) | 📢 Report sent to cyber security (simulated)"
        }
    else:
        return {
            "message": "✅ No threat detected. No action required.",
            "action": "✔ System monitoring continues..."
        }


# -----------------------------
# MAIN PROGRAM (TEST MODE)
# -----------------------------
if __name__ == "__main__":

    data = load_data("final_dataset.txt")

    print("\n----- DATASET INFORMATION -----")
    print("Total messages:", len(data))

    train_data, test_data = split_data(data, 0.8)

    print("\n----- TRAIN TEST SPLIT -----")
    print("Training messages:", len(train_data))
    print("Testing messages:", len(test_data))

    spam_words, ham_words, spam_count, ham_count = train_naive_bayes(train_data)

    print("\n----- MODEL TRAINING COMPLETE -----")
    print("Spam messages in training:", spam_count)
    print("Ham messages in training:", ham_count)

    accuracy = calculate_accuracy(test_data, spam_words, ham_words, spam_count, ham_count)

    print("\n----- MODEL PERFORMANCE -----")
    print("Model Accuracy:", round(accuracy * 100, 2), "%")

    # PDF TEST
    print("\n----- PDF SCAM TEST -----")

    file_path = "sample.pdf"
    text = extract_text_from_pdf(file_path)

    if not text.strip():
        print("⚠️ No readable text found in PDF")
    else:
        prediction = predict(text, spam_words, ham_words, spam_count, ham_count)

        print("\n----- PDF ML RESULT -----")

        if prediction == "spam":
            print("Risk Level: HIGH RISK 🚨")
        else:
            print("Risk Level: LOW RISK ✅")

        # 🔥 NEW: ALERT OUTPUT
        alert = send_alert(prediction)
        print("\n----- ALERT -----")
        print(alert)