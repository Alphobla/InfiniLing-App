describe('Podcast search', () => {
  it('searches by name and adds a podcast via the dropdown', () => {
    // Mock the search endpoint so the test doesn't depend on iTunes
    cy.intercept('GET', '/api/podcasts/search*', {
      statusCode: 200,
      body: {
        results: [
          {
            title: 'Test Mock Podcast',
            artist: 'Mock Host',
            image_url: 'https://via.placeholder.com/100',
            rss_url: 'https://example.com/test-mock-feed.xml',
          },
        ],
      },
    }).as('searchPodcasts')

    // Mock the add endpoint so we don't actually fetch & parse a fake RSS feed
    cy.intercept('POST', '/api/podcasts', {
      statusCode: 200,
      body: {
        id: 'mock-id-123',
        title: 'Test Mock Podcast',
        description: 'Mock description',
        rss_url: 'https://example.com/test-mock-feed.xml',
        image_url: 'https://via.placeholder.com/100',
        language: 'pl',
        is_starter: false,
      },
    }).as('addPodcast')

    // Use the pre-existing test user (email confirmation is required for new signups,
    // so we log in rather than sign up to reach the app directly)
    cy.loginTestUser()

    // Navigate to Podcasts
    cy.visit('/podcast')

    // Type into the search input — the debounce is 250ms
    cy.get('[data-cy="podcast-search-input"]').type('test mock')
    cy.wait('@searchPodcasts')

    // Dropdown shows the mocked result
    cy.get('[data-cy="podcast-search-dropdown"]').should('be.visible')
    cy.get('[data-cy="podcast-search-result"]').should('contain', 'Test Mock Podcast')
    cy.get('[data-cy="podcast-search-result"]').should('contain', 'Mock Host')

    // Click the result → triggers add
    cy.get('[data-cy="podcast-search-result"]').first().click()
    cy.wait('@addPodcast')

    // Dropdown closes; the new podcast appears in the grid
    cy.get('[data-cy="podcast-search-dropdown"]').should('not.exist')
    // Podcast cards render the title as the image alt attribute, not as visible text
    cy.get('img[alt="Test Mock Podcast"]').should('be.visible')

    // Search input is cleared
    cy.get('[data-cy="podcast-search-input"]').should('have.value', '')
  })
})
