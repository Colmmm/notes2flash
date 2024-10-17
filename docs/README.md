# notes2flash
AI-powered application to organize Google Doc notes and convert them into Anki flashcards.

## Features

- Scrape notes from Google Docs
- Process notes using AI models via OpenRouter API
- Create Anki flashcards with custom templates
- Flexible workflow system using YAML configuration files

## Installation

1. Download the addon files and place them in your Anki addons folder.
2. Install the required dependencies by running:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Launch Anki and go to Tools > Add-ons > Notes2Flash > Config to set up your default values.
2. Create a custom workflow configuration file in the `addon/workflow_configs` directory (see example below).
3. In Anki, go to Tools > Notes2Flash to open the addon interface.
4. Select your desired workflow configuration from the dropdown menu.
5. Fill in the required input fields based on the selected workflow.
6. Click "Submit" to start the flashcard creation process.

## Creating Custom Workflows

Custom workflows are defined using YAML configuration files. Here's an example structure:

```yaml
workflow_name: "Vocabulary Extraction and Translation"

stages: ["scrape_notes", "process_notes_to_cards", "add_cards_to_anki"]
user_inputs: [google_doc_id, openrouter_api_key, target_language]

scrape_notes:
  doc_id: "{google_doc_id}"

process_notes_to_cards:
  api_key: "{openrouter_api_key}"
  steps:
    - name: "Extract Vocabulary"
      prompt: "Extract vocabulary from the following content: {notes_content}"
      input:
        - notes_content
      output: vocabulary_list
      model: "openai_gpt3"

    - name: "Translate Vocabulary"
      prompt: "Translate the following vocabulary: {vocabulary_list} to {target_language}"
      input:
        - vocabulary_list
        - target_language
      output: translated_vocabulary
      model: "openai_gpt4"

    - name: "Generate Flashcards"
      prompt: |
        Create flashcards using this vocabulary: {vocabulary_list} and the following translations {translated_vocabulary} into the following format:
        [
          {"vocab": "vocab1", "translation": "translation1"},
          {"vocab": "vocab2", "translation": "translation2"},
          ...
        ]
      input:
        - vocabulary_list
        - translated_vocabulary
      output: flashcards
      model: "openai_gpt4"

add_cards_to_anki:
  deck_name: "Vocabulary Deck"
  card_template:
    template_name: "Basic"
    front: "{vocab}"
    back: "{translation}"
```

Save your custom workflow configurations in the `addon/workflow_configs` directory with a `.yml` extension.

## Customizing Workflows

1. **Stages**: Define the order of operations in your workflow.
2. **User Inputs**: Specify what information the user needs to provide.
3. **Stage Configurations**: Customize each stage with specific parameters and steps.
4. **AI Model Integration**: Use different AI models for various processing steps.
5. **Card Templates**: Define how the flashcards should be formatted in Anki.

## Tips for Creating Effective Workflows

- Start with simple workflows and gradually add complexity.
- Test your workflows with various types of notes to ensure they work as expected.
- Use descriptive names for your workflow files to easily identify their purpose.
- Leverage the flexibility of the system to create workflows for different subjects or study methods.

For more detailed information on creating and customizing workflows, please refer to the documentation in the `docs` folder.
