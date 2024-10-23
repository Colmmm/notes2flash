# notes2flash
AI-powered application to organize Google Doc notes and convert them into Anki flashcards.

![Notes2Flash Demo](notes2flash_demo.gif)

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
   pip install --target addon/libs -r requirements.txt
   ```

## Usage

1. Launch Anki and go to Tools > Add-ons > Notes2Flash > Config to set up your OpenRouter API key.
2. Create a custom workflow configuration file in the `addon/workflow_configs` directory (see example below).
3. In Anki, go to Tools > Notes2Flash to open the addon interface.
4. Select your desired workflow configuration from the dropdown menu.
5. Fill in the required input fields based on the selected workflow.
6. (Optional) Enable debug mode for more detailed logging.
7. Click "Submit" to start the flashcard creation process.

## Creating Custom Workflows

Custom workflows are defined using YAML configuration files. Here's an example structure:

```yaml
workflow_name: "Vocabulary Extraction and Flashcard Generation"

user_inputs: [google_doc_id, target_language, native_language, deckname]

# 1) **Scrape Notes from Google Docs**
scrape_notes:
  - doc_id: "{google_doc_id}"
    output: scraped_notes_output  # Only specifying the output name

# 2) **Process Notes into Flashcards**
process_notes_to_cards:
  - step: "Process notes and create flashcards"
    model: "meta-llama/llama-3.1-8b-instruct:free"
    input:
      - scraped_notes_output  # Input is the notes content from Google Docs
      - native_language  # Input is the native language for translation
      - target_language
    output: flashcards  # The output should always be a list of dictionaries with the following fields:
    output_fields:
      - vocabulary
      - translation
    prompt: |
      Extract {target_language} vocabulary from {scraped_notes_output}. Translate it into {native_language}.
      For each vocabulary word, generate flashcards in the exact format below, where the key for the word should be "vocabulary" and the key for the translation should be "translation". 
      Do not use any other keys or formats.

      Output flashcards in this format:
      [
        {"vocabulary": "word1", "translation": "translation1"},
        {"vocabulary": "word2", "translation": "translation2"},
        ...
      ]
     
#  3)  **Add Cards to Anki**
add_cards_to_anki:
  flashcards_data: flashcards  # Input is the list of flashcards
  deck_name: "{deckname}"
  card_template:
    template_name: "Basic"
    front: "{vocabulary}"
    back: "{translation}"

```

Save your custom workflow configurations in the `addon/workflow_configs` directory with a `.yml` extension.

## Customizing Workflows

1. **User Inputs**: Specify what information the user needs to provide.
2. **Scrape Notes**: Configure the Google Doc scraping step.
3. **Process Notes to Cards**: Define the AI processing step, including the model, input, output, and prompt.
4. **Add Cards to Anki**: Specify how the flashcards should be added to Anki.

## Debugging and Troubleshooting

- Enable debug mode in the addon interface for more detailed logging.
- Check the `notes2flash.log` file in the addon directory for detailed error messages and execution logs.
- Use the logs to identify issues in your workflow configuration or API calls.

## Tips for Creating Effective Workflows

- Ensure your prompts are explicit and clearly define the expected output format.
- Test your workflows with various types of notes to ensure they work as expected.
- Use descriptive names for your workflow files to easily identify their purpose.
- Leverage the flexibility of the system to create workflows for different subjects or study methods.

## Error Handling

The addon now provides more detailed error messages and logging. If you encounter any issues:

1. Check the error message displayed in the Anki interface.
2. Review the `notes2flash.log` file for more detailed information.
3. Ensure your workflow configuration is correct and all required fields are provided.
4. Verify that your OpenRouter API key is correctly entered in the addon configuration.

For more detailed information on creating and customizing workflows, troubleshooting, and advanced features, please refer to the documentation in the `docs` folder.
