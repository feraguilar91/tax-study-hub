# Tax Study Hub v0.2

A Streamlit study application for Enrolled Agent exam preparation.

## Included

- 757 normalized flashcards from the uploaded EA study files
- EA Part 1, Part 2, and Part 3 filters
- Previous and Next navigation
- Active-recall quizzes with self-grading
- Clickable IRS references
- Search
- Bookmarks and progress stored in SQLite

## Install and run

```bash
cd tax-study-hub-v0.2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Updating the app

After replacing files or changing code:

```bash
git add .
git commit -m "Update Tax Study Hub"
git push
```

## Reference note

References are assigned by topic when a reliable IRS publication or guidance page is
available. Otherwise, the card links to an IRS-focused search. The uploaded source
files do not contain card-level citation columns, so each rule should be verified
before professional use.
