# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2025-01-06

### 🆕 Added
- Implemented robust retry logic for API calls to handle unexpected responses.
- Introduced fallback handling for truncated content on the final retry attempt.
- Added a **Cancel** button to the GUI to interrupt ongoing workflows.
- Included anti-caching mechanisms to prevent the API from returning the same incorrect response across retries, making retries more effective.
- Duplicate cards are automatically prevented from being added to the same deck. This is managed by add_cards_to_anki.py after the document has been processed. Note that this step operates independently of source document change tracking, which is handled through tracked_docs.json and scrape_notes.py.

### ⚠️ Changed
- **Multi-step processing workflows**: The workflow now processes each chunk through all steps before moving to the next chunk, improving efficiency in multi-step workflows.
- The chunk size parameter is now required only in the first processing step.
- The format reminder is appended only during the final processing step.
- Moved logger into its own file.

### 🐛 Fixed
- Resolved an issue with chunking where the entire scraped content was being used for each API call, instead of the intended chunked content, due to incorrect prompt handling.
- Fixed debug mode for logger

---

## [1.0.0] - 2024-11-18

### 🆕 Added
- Initial release.
