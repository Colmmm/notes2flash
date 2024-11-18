# Notes2Flash
AI-powered application to organize online notes (Google Doc, Notion, Obsidian) and convert them into Anki flashcards.

![Notes2Flash Demo](https://github.com/Colmmm/notes2flash/raw/main/docs/notes2flash_demo.gif)

## Features

- **Multi-Platform Support**: Seamless compatibility with Google Docs, Notion, and Obsidian
- **Effortless Setup**: Minimal configuration required to scrape online documents and convert them to Anki flashcards
- **Change Tracking**: Intelligent tracking of document modifications
- **Customizable Workflows**: Highly flexible flashcard creation process via YAML configuration
- **AI Integration**: Support for various LLM models (ChatGPT, Llama, Gemini, and more via OpenRouter.ai)
- **Advanced Processing**: Multi-step prompt chaining capabilities for complex transformations

**Note**: The addon has been tested on the following versions of Anki:
- 24.06.03 (qt6)
- 23.12.1 (qt6)
- 2.1.49

## Installation

### Option 1: Install via Ankiweb (Recommended)
1. Visit the addon's [Ankiweb page](https://ankiweb.net/shared/info/868678030?cb=1731942628370)
2. Copy the addon code:
   ```
   868678030
   ```
3. In Anki, go to Tools > Add-ons > Get Add-ons...
4. Paste the addon code into the Code field and click OK

### Option 2: Install from Source
1. Clone the repository: [GitHub Repository](https://github.com/Colmmm/notes2flash)
2. Build using Docker:
   ```
   docker-compose up
   ```
3. Locate the generated addon in `output/notes2flash.ankiaddon`
4. In Anki, navigate to Tools > Add-ons > Install from file
5. Select the `notes2flash.ankiaddon` file

## Setting Up OpenRouter.ai Account (Required)

1. Create an account at [OpenRouter.ai](https://openrouter.ai/) using Gmail or other authentication
2. Navigate to the "Keys" section and create a new key
3. Configure the addon:
   - Open Anki > Tools > Add-ons > Notes2Flash > Config
   - Insert your key in the `"openrouter_api_key"` field

**Note on Pricing**: You dont have to add any credit card details to use it but you'll be limited to free models which there are many to choose from such as `meta-llama/llama-3.1-70b-instruct:free`, go to the openrouter.ai website to browse all possible models. To use paid models you have to do a minimum top-up of at least $5 USD, recommended for optimal performance. Using `openai/gpt-4o-mini` is a good performance good value model, processing 1 page (≈ 500 words ≈ 25 flashcards) costs approximately $0.0024.

*Note: notes2flash has no affiliation with openrouter.ai, and no money is made by notes2flash*

## Platform-Specific Setup

### Google Docs Integration

1. **Public Documents**
   - Simply make your Google Doc public and use its URL/ID

2. **Private Documents**
   - Set up Google Docs API access
   - Save `service_account.json` to `~/.local/share/Anki2/addons21`

### Notion Integration (Setup Required if using Notion)

1. **Create Integration**
   - Access the Notion Developer Portal
   - Create a new integration
   - Configure workspace permissions
   - Store the Integration Token securely

2. **Configure Access**
   - Open your Notion page
   - Click "Share" > "Invite"
   - Grant access to your integration

### Obsidian Integration

Compatibility with Obsidian is limited due to the lack of free native public access cloud storage. Scraping is done via the [Obsius addon](https://github.com/jonstodle/obsius-obsidian-plugin) (shoutout to the developer!):
1. Install the Obsius addon in Obsidian
2. Publish your note to generate a public URL (e.g., https://obsius.site/2v1e5g2j566s7071371k)

## Workflow Examples

### Example 1: Basic Configuration
```yaml
workflow_name: "barebone notes2flash workflow config example"

user_inputs: [notes_url]

# 1) **scrape notes from online docs (google docs, notion, obsius)**
scrape_notes:
  - url: "{notes_url}"
    output: scraped_notes_output  # the output name for the scraped notes

# 2) **process notes into flashcards**
process_notes_to_cards:
  - step: "organize notes and create flashcards"
    model: "meta-llama/llama-3.1-70b-instruct:free"
    chunk_size: 4000  # maximum chars per chunk (roughly 4 * token limit for english, 1*token_limit for mandarin)
    input:
      - scraped_notes_output  # input is the notes content from scrape_notes stage
    attach_format_reminder: true # if true will append a format reminder to the prompt ensuring api outputs correct format
    output: flashcards  # the output will always be a list of dictionaries with the following fields:
    output_fields:
      - question
      - answer
    prompt: |
      organize the following notes into flashcards:
      {scraped_notes_output} 

#  3)  **add cards to anki**
add_cards_to_anki:
  flashcards_data: flashcards  # input is the list of flashcards
  deck_name: "example_deckname"
  card_template:
    template_name: "Notes2flash Basic Note Type" # 'notes2flash basic note type' is a default note type included in addon found in ./included_note_types/
    front: "{question}"  # the front of the card will show the question
    back: "{answer}"  # the back of the card will show the answer
```

#### Workflow Explanation

1. **Scrape Notes**: In this stage, the `scrape_notes` key is used to specify the source URL from which to scrape the content. The output for the scraped notes is user configurable and defined as `scraped_notes_output` here. This name can be referenced in later stages, allowing you to easily manage and utilize the scraped content in the processing steps.

2. **Process Notes into Flashcards**: This stage takes the output from the `scrape_notes` stage as input. You must specify the output name (`scraped_notes_output` in this case) in the `input` section to ensure the correct data is processed. The model specified will organize the scraped notes and generate flashcards. The output will be a list of dictionaries containing the fields defined in `output_fields`, such as `question` and `answer`. 

Additionally, if `attach_format_reminder` is set to `True`, a structured reminder will be appended to the end of the prompt. This reminder ensures that the API outputs the data in the expected format for the third stage, which is a list of dictionaries where each dictionary represents a flashcard with the specified `output_fields`.
The reminder that would be generated for the above example workflow config would be like the following
 ```
 **IMPORTANT**
 Format the output as a list of dictionaries, where each dictionary represents a flashcard
 Each dictionary must contain exactly these keys: question, answer
 Strictly adhere to this structure. Any deviation from this format will not be accepted
 Example output:
 [
     {
         "question": "example_question_1",
         "answer": "example_answer_1"
     },
     {
         "question": "example_question_2",
         "answer": "example_answer_2"
     },
     ...
 ]
 ``` 

3. **Add Cards to Anki**: In the final stage, the generated flashcards are added to Anki. The `flashcards_data` key takes the output from the previous stage, and you must specify the output name (`flashcards`) to ensure the correct data is added. The card template defines how each flashcard will be structured in Anki.

Save your custom workflow configurations in the `addon/workflow_configs` directory with a `.yml` extension.


### Example 2: Advanced Configuration with User Inputs
The user_inputs key in the config allows you to customize variables that are specified by the user at time before runtime, for example if we add some alterations to the first workflow config by adding some variables to speicify the output anki deckname and also the topic of the notes to give the AI model some context which we can put in the prompt:
```yaml
workflow_name: "barebone notes2flash workflow config example w/ more inputs"

user_inputs: [notes_url, notes_topic, deckname]

# 1) **scrape notes from online docs (google docs, notion, obsius)**
scrape_notes:
  - url: "{notes_url}"
    output: scraped_notes_output  # the output name for the scraped notes

# 2) **process notes into flashcards**
process_notes_to_cards:
  - step: "organize notes and create flashcards"
    model: "meta-llama/llama-3.1-70b-instruct:free"
    chunk_size: 4000
    input:
      - scraped_notes_output
      - notes_topic # Additional context for AI processing
    attach_format_reminder: true
    output: flashcards
    output_fields:
      - question
      - answer
    prompt: |
      organize the following notes of the topic {notes_topic} into flashcards:
      {scraped_notes_output} 

# 3) **add cards to anki**
add_cards_to_anki:
  flashcards_data: flashcards
  deck_name: "{deckname}"
  card_template:
    template_name: "Notes2flash Basic Note Type"
    front: "{question}"
    back: "{answer}"
```

### Example 3: Multi-Step Processing (Language Learning)
```yaml
workflow_name: "Vocabulary Extraction and Multi-step Processing"

user_inputs: [notes_url, deckname]

# 1) Scrape Notes from Online Docs
scrape_notes:
  - url: "{notes_url}"
    output: scraped_notes_output

# 2) Process Notes to Extract Vocabulary and Generate Flashcards
process_notes_to_cards:
  - step: "Extract vocabulary and phrases"
    model: "meta-llama/llama-3.1-70b-instruct:free"
    chunk_size: 4000
    input:
      - scraped_notes_output
    attach_format_reminder: true
    output: extracted_vocabulary
    prompt: |
      Extract vocabulary and phrases from the following document. The document contains Mandarin keywords or short phrases. For each item, provide:
      - The Mandarin word or phrase.
      - Its pinyin representation.
      - Its English translation.

      Ignore irrelevant content and remove duplicates. If there are multiple valid translations, select the most commonly used one. Ensure the output strictly follows this JSON format:
      [
        {"mandarin": "word1", "pinyin": "pinyin1", "translation": "translation1"},
        {"mandarin": "word2", "pinyin": "pinyin2", "translation": "translation2"},
        ...
      ]

      Document:
      {scraped_notes_output}
    
  - step: "Generate example sentences and flashcards"
    model: "meta-llama/llama-3.1-70b-instruct:free"
    chunk_size: 4000
    input:
      - extracted_vocabulary
    attach_format_reminder: false
    output: flashcards
    output_fields:
      - sentence
      - translation
      - keywords
    prompt: |
      Use the vocabulary below to generate example sentences in Mandarin. Each sentence should:
      - Naturally incorporate one or more keywords.
      - Include additional context or keywords if necessary for clarity (only if not commonly known by an upper-intermediate learner).

      For each sentence, provide:
      - The Mandarin sentence.
      - Its English translation.
      - A list of keywords in the format "keyword pinyin translation" separated by `<br>` for multiple keywords.

      Ensure the output strictly follows this JSON format:
      [
        {"sentence": "Example sentence in Mandarin.", "translation": "English translation of the sentence.", "keywords": "keyword1 pinyin1 translation1<br>keyword2 pinyin2 translation2"},
        {"sentence": "Another example sentence in Mandarin.", "translation": "English translation of this sentence.", "keywords": "keywordA pinyinA translationA<br>keywordB pinyinB translationB"},
        ...
      ]

      Keywords:
      {extracted_vocabulary}

# 3) Add Cards to Anki
add_cards_to_anki:
  flashcards_data: flashcards
  deck_name: "{deckname}"
  card_template:
    template_name: "Notes2flash Basic Note Type"
    front: "{sentence}"
    back: "{translation}<br><br>{keywords}"
```

**Note**: Only the final step requires the 'flashcards_data' format. Intermediate steps pass their output as strings.

## Troubleshooting Guide

### Debug Mode
- Enable debug mode in the addon interface
- Monitor `notes2flash.log` for detailed execution logs
- Common issue: Incorrect API output formatting (must match specified output_fields)

### Best Practices
- Write explicit, detailed prompts
- Test workflows with various document types
- Use descriptive workflow filenames
- Verify API key configuration

### Error Resolution
1. Check Anki interface messages
2. Review log files
3. Validate workflow configuration
4. Confirm OpenRouter API key status

## Project Structure

### Core Components
- **addon/**: Main application code
  - **__init__.py**: Entry point
  - **notes2flash.py**: Core functionality
  - **gui.py**: User interface
  - **config.json**: Configuration
  - **manifest.json**: Metadata
  - **process_notes_to_cards.py**: Flashcard generation
  - **add_cards_to_anki.py**: Anki integration
  - **workflow_engine.py**: Workflow management

### Source Handlers
- **addon/scrape_googledoc.py**: Google Docs integration
- **addon/scrape_notion.py**: Notion integration
- **addon/scrape_obsidian.py**: Obsidian integration
- **addon/scrape_utils.py**: Common utilities
- **addon/scrape_notes.py**: Core scraping functionality

### Configuration
- **addon/workflow_configs/**: Workflow definitions
- **addon/included_note_types/**: Note templates
- **requirements.txt**: Dependencies
- **docker-compose.yml**: Build configuration

## Document Tracking

### tracked_docs.json Structure
```json
{
  "document_id": {
    "lines": ["array", "of", "tracked", "lines"],
    "last_updated": "timestamp",
    "version": "document_version",
    "successfully_added_to_anki": boolean,
    "pending_changes": ["array", "of", "pending", "lines"],
    "source_url": "document_url",
    "source_type": "source_platform"
  }
}
```

### Managing Tracking
- **Reset**: Delete `tracked_docs.json`
- **Selective Reset**: Remove specific document entries

## Future Development

- GitHub Actions integration
- Free API access tier
- Enhanced workflow organization
- Expanded documentation

## Contributing

We welcome contributions through GitHub:
- Bug reports
- Code improvements
- Workflow configurations
- Documentation updates
