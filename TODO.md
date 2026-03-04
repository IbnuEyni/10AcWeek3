# TODO: Future Improvements

## High Priority
- [ ] None currently

## Medium Priority
- [ ] Add more test coverage for edge cases
- [ ] Implement retry logic for API failures
- [ ] Add rate limiting for API calls

## Low Priority
- [ ] Migrate from `google.generativeai` to `google.genai` package
  - Current: `import google.generativeai as genai`
  - Future: `import google.genai as genai`
  - Reason: Old package is deprecated but still works
  - Impact: None currently, will need update in future
  - Files to update:
    - src/strategies/vision_augmented.py
    - src/strategies/handwriting_ocr.py

## Documentation
- [ ] Add API key setup guide
- [ ] Add troubleshooting section
- [ ] Add performance tuning guide
