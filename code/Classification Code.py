import re
import json
import pandas as pd
from google.colab import drive
import anthropic

# Mount Google Drive
drive.mount('/content/drive')

# Initialize Model
key = 
client = 

# Load JSON data
json_path = '/content/drive/MyDrive/Algoverse research/sarcasm_data.json'
with open(json_path, 'r') as file:
    data = json.load(file)

# Load ground truth labels from CSV
csv_path = '/content/drive/MyDrive/Algoverse research/data - Sheet1.csv'
df_labels = pd.read_csv(csv_path)

# Map example keys to correct labels
label_dict = dict(zip(df_labels['Example key #'].astype(str), df_labels['Our classification'].str.lower().str.strip()))

# Prompt
prompt = """
Before classifying the type of sarcasm, perform the following steps:


1. **Emotion Detection**:
   Identify the primary emotions present in the statement based on both word choice and delivery cues. The possible emotions are:


   - **Happiness**
   - **Sadness**
   - **Anger**
   - **Fear**
   - **Surprise**
   - **Disgust**


   If no specific emotion can be identified, assign a neutral emotional cue.
   Do not use any other emotions outside this list.




2. **Sarcasm Detection**:
   If the speaker’s intent and emotional cues do not suggest mockery, insincerity, or irony — clearly state that this statement is not sarcastic.


   If the statement is sarcastic, proceed to classify it as one of the following using the emotional cues:


  - **Self-deprecating sarcasm**
  - **Brooding sarcasm**
  - **Deadpan sarcasm**
  - **Polite sarcasm**
  - **Obnoxious sarcasm**
  - **Raging sarcasm**
  - **Manic sarcasm**


3. **Final Output**:
   After the explanation, clearly state the best-matching sarcasm type on a new line in this format:
   `[Type]`


   If the statement is not sarcastic, write:
   `[Not Sarcasm]`


"""

# Lists to store results
true_labels = []
predicted_labels = []

# Main loop to classify and evaluate
for num, value in data.items():
    utterance = value['utterance']
    speaker = value['speaker']
    context = value['context']
    context_speakers = value['context_speakers']
    example_key = str(num)

    # Build formatted context string
    formatted_context = "\n".join(
        f"{speaker_name}: {utterance_line}"
        for speaker_name, utterance_line in zip(context_speakers, context)
    )

    # Create full message for the API
    message_content = (
        f"Speaker: {speaker}\n"
        f"Utterance: {utterance}\n"
        f"Context:\n{formatted_context}\n\n"
        f"{prompt}"
    )

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",  # or claude-3-sonnet-20240229 if you want faster/cheaper
            max_tokens=1000,
            messages=[
                {"role": "user", "content": message_content}
            ]
        )

        full_response = response.content[0].text  # Anthropic returns a list of blocks

        # Extract sarcasm type from square brackets
        match = re.search(r"\[(.*?)\]", full_response)
        predicted_type = match.group(1).lower().strip() if match else "not detected"

        predicted_labels.append(predicted_type)

        # Get the true label
        true_label = label_dict.get(example_key, "not found").lower().strip()
        true_label = re.sub(r'^\d+_\d+', '', true_label)  # Remove any leading numbers if needed
        true_labels.append(true_label)

        print(f"Statement {num}: True Label = {true_label}, Predicted = {predicted_type}\n{'-'*40}")

        # Calculate running accuracy
        correct = sum(1 for true, pred in zip(true_labels, predicted_labels) if true == pred)
        accuracy = correct / len(true_labels) * 100
        print(f"Running Accuracy: {accuracy:.2f}% ({correct}/{len(true_labels)} correct)")

    except Exception as e:
        print(f"Error processing statement {num}: {e}")
        predicted_labels.append("error")
        true_labels.append(label_dict.get(example_key, "not found").lower().strip())

# Final accuracy
correct = sum(1 for true, pred in zip(true_labels, predicted_labels) if true == pred)
accuracy = correct / len(true_labels) * 100

print(f"\nFinal Accuracy: {accuracy:.2f}% ({correct}/{len(true_labels)} correct)")

# Save results
results_df = pd.DataFrame({
    'Example Key': list(data.keys()),
    'True Label': true_labels,
    'Predicted Label': predicted_labels
})
results_df.to_csv('/content/drive/MyDrive/Algoverse research/claude_sarcasm_classification_results.csv', index=False)
print("Results saved to claude_sarcasm_classification_results.csv.")