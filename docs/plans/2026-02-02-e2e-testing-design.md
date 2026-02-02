# E2E Testing Design - InfiniLing

## Overview

End-to-end testing with Cypress covering the full MVP user flows. Uses a dedicated test account in Supabase for realistic integration testing.

## Tech Stack

- **Framework:** Cypress
- **Test Account:** Dedicated user in Supabase
- **Coverage:** Full MVP (~14 tests)

## Folder Structure

```
web/
├── cypress/
│   ├── e2e/
│   │   ├── auth.cy.js          # Signup, login, logout
│   │   ├── onboarding.cy.js    # First-time user flow
│   │   ├── vocabulary.cy.js    # Add, edit, delete words
│   │   ├── review.cy.js        # Flashcard session
│   │   ├── story.cy.js         # Story generation + audio
│   │   └── settings.cy.js      # Settings, import/export
│   ├── fixtures/
│   │   └── test-data.json      # Reusable test data
│   ├── support/
│   │   ├── commands.js         # Custom commands (login, etc.)
│   │   └── e2e.js              # Global setup
│   └── cypress.config.js
```

## Test Cases

### 1. Auth Tests (`auth.cy.js`) - 3 tests
- `should sign up a new user` - Creates account, verifies redirect to onboarding
- `should login with valid credentials` - Login, verify dashboard loads
- `should logout` - Click logout, verify redirect to login page

### 2. Onboarding Tests (`onboarding.cy.js`) - 2 tests
- `should complete onboarding flow` - Select mother tongue → intro → dashboard
- `should redirect to onboarding if no settings` - New user gets redirected

### 3. Vocabulary Tests (`vocabulary.cy.js`) - 3 tests
- `should add a new word` - Enter word, submit, verify appears in list
- `should edit a word` - Click edit, change translation, save, verify update
- `should delete a word` - Click delete, confirm, verify removed from list

### 4. Review Tests (`review.cy.js`) - 2 tests
- `should complete a review session` - Flip card, score, progress through cards
- `should show completion stats` - After session, verify stats shown

### 5. Story Tests (`story.cy.js`) - 2 tests
- `should generate a story` - Select words, generate, verify story displays
- `should play audio` - Generate story, click listen, verify audio element

### 6. Settings Tests (`settings.cy.js`) - 2 tests
- `should update language settings` - Change mother tongue, save, verify
- `should export vocabulary` - Click export CSV, verify file downloads

**Total: 14 tests**

## Custom Commands

```js
// support/commands.js

// Login with email/password
Cypress.Commands.add('login', (email, password) => {
  cy.visit('/login')
  cy.get('input[type="email"]').type(email)
  cy.get('input[type="password"]').type(password)
  cy.get('button[type="submit"]').click()
  cy.url().should('not.include', '/login')
})

// Login with test account
Cypress.Commands.add('loginTestUser', () => {
  cy.fixture('test-data').then((data) => {
    cy.login(data.testUser.email, data.testUser.password)
  })
})

// Add a vocabulary word
Cypress.Commands.add('addWord', ({ word, translation, languageFrom }) => {
  cy.visit('/vocabulary')
  cy.contains('Add').click()
  cy.get('input[name="word"]').type(word)
  cy.get('input[name="translation"]').type(translation)
  cy.get('button[type="submit"]').click()
})

// Wait for API call to complete
Cypress.Commands.add('waitForApi', (route) => {
  cy.intercept(route).as('apiCall')
  cy.wait('@apiCall')
})
```

## Test Data

```json
// fixtures/test-data.json
{
  "testUser": {
    "email": "test@infinilig.dev",
    "password": "TestPassword123!"
  },
  "words": [
    { "word": "hola", "translation": "hello", "languageFrom": "Spanish" },
    { "word": "gracias", "translation": "thank you", "languageFrom": "Spanish" }
  ]
}
```

## Configuration

```js
// cypress.config.js
const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5173',
    viewportWidth: 1280,
    viewportHeight: 720,
    defaultCommandTimeout: 10000,
    env: {
      apiUrl: 'http://localhost:8000'
    },
    setupNodeEvents(on, config) {
      // Node event listeners
    }
  }
})
```

## NPM Scripts

```json
{
  "scripts": {
    "cy:open": "cypress open",
    "cy:run": "cypress run",
    "test:e2e": "cypress run"
  }
}
```

## Running Tests

```bash
# Terminal 1 - Backend
uv run uvicorn api.main:app --reload

# Terminal 2 - Frontend
npm run dev

# Terminal 3 - Tests (interactive)
npm run cy:open

# Or headless
npm run cy:run
```

## Prerequisites

1. Create test user in Supabase: `test@infinilig.dev` / `TestPassword123!`
2. Run `schema.sql` in Supabase if not done
3. Backend and frontend must be running

## Test Isolation

- **Auth tests:** Use unique email with timestamp for signup tests
- **Vocabulary tests:** Clean up created words in `afterEach`
- **Review tests:** Ensure at least one word exists before running

## Future: CI Integration

GitHub Actions workflow can be added to:
- Start backend and frontend services
- Run `npm run cy:run`
- Upload screenshots/videos on failure
