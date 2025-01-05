# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).


## [1.1.0] - 2025-01-05
### 🆕 Added
- Added robust retry logic for api calls for unexpected responses
- On last retry, parser will also try to process truncated content
- Added cancel button to interupt workflow on gui
- Anti-cache features to stop api from giving same response (caused issues if it gives bad response, it would then keep giving this bad response on retries making retries not useful)

### ⚠️ Changed
- Processing workflow now takes a chunk of the scraped content and processes it through all chunks before moving onto next chunk, rather than trying to process all chunks at once then moving to next step (if theres more than one step). 

### 🐛 Fixed
- Fixed chunking which was initially broken because the way the prompt being passed to processing stage had already had the full scraped content subbed in and so the chunked content had no where to go and so was just using full scraped content for each chunks prompt and api call

---

## [1.0.0] - 2024-11-18
### 🆕 Added
- Initial release.
