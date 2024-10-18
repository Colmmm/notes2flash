# notes2flash
AI-powered application to organize Google Doc notes and convert them into Anki flashcards.

## Features

- Scrape notes from Google Docs
- Process notes using AI models via OpenRouter API
- Create Anki flashcards with custom templates
- Flexible workflow system using YAML configuration files
- Improved error handling and debugging capabilities

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
6. (Optional) Enable debug mode for more detailed logging.
7. Click "Submit" to start the flashcard creation process.

## Creating Custom Workflows

Custom workflows are defined using YAML configuration files. Here's an example structure:

```yaml
workflow_name: "Vocabulary Extraction and Translation"

stages: ["scrape_notes", "process_notes_to_cards", "add_cards_to_anki"]
user_inputs: [google_doc_id, openrouter_api_key, target_language, deckname]

scrape_notes:
  doc_id: "{google_doc_id}"
  output:
    name: scraped_notes_output
    keys:
      - notes_content

process_notes_to_cards:
  api_key: "{openrouter_api_key}"
  steps:
    - name: "Extract Vocabulary"
      prompt: |
        Extract vocabulary from the following content: {scraped_notes_output.notes_content}.
        Output the result as a JSON object in this format:
        {
          "vocabulary_list": ["word1", "word2", "word3", ...]
        }
      input:
        - scraped_notes_output.notes_content
      output:
        name: vocabulary_extraction_output
        keys:
          - vocabulary_list
      model: "meta-llama/llama-3.1-8b-instruct:free"

    - name: "Translate and Generate Flashcards"
      prompt: |
        Translate the following vocabulary: {vocabulary_extraction_output.vocabulary_list} into {target_language}. 
        Then, using the translations, generate flashcards in this format:
        {
          "flashcards": [
            {"vocab": "word1", "translation": "translation1"},
            {"vocab": "word2", "translation": "translation2"},
            ...
          ]
        }
      input:
        - vocabulary_extraction_output.vocabulary_list
        - target_language
      output:
        name: flashcards_output
        keys:
          - flashcards
      model: "meta-llama/llama-3.1-8b-instruct:free"

add_cards_to_anki:
  input:
    - flashcards_output.flashcards
  deck_name: "{deckname}"
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

## Debugging and Troubleshooting

- Enable debug mode in the addon interface for more detailed logging.
- Check the `notes2flash.log` file in the addon directory for detailed error messages and execution logs.
- Use the logs to identify issues in your workflow configuration or API calls.

## Tips for Creating Effective Workflows

- Start with simple workflows and gradually add complexity.
- Test your workflows with various types of notes to ensure they work as expected.
- Use descriptive names for your workflow files to easily identify their purpose.
- Leverage the flexibility of the system to create workflows for different subjects or study methods.
- Use the debug mode and logs to fine-tune your prompts and improve the quality of generated flashcards.

## Error Handling

The addon now provides more detailed error messages and logging. If you encounter any issues:

1. Check the error message displayed in the Anki interface.
2. Review the `notes2flash.log` file for more detailed information.
3. Ensure your workflow configuration is correct and all required fields are provided.
4. Verify that your API keys and other credentials are valid and correctly entered.

For more detailed information on creating and customizing workflows, troubleshooting, and advanced features, please refer to the documentation in the `docs` folder.
