'use strict';

/**
 * MCP tool category registry.
 * Each category groups related tools with metadata for progressive disclosure.
 */

const CATEGORIES = {
  core: {
    description: 'Search and interact with the knowledge base: search, read topics/chunks, contribute, propose edits, vote, subscribe, and check reputation. Always available.',
    alwaysEnabled: true,
  },
  account: {
    description: 'Account lifecycle: register, login, profile management, API key rotation, agent sub-accounts, and connection tokens.',
    alwaysEnabled: false,
  },
  knowledge_curation: {
    description: 'Topic and changeset management: create/update topics, propose/retract/resubmit changesets, add sources, link translations, browse history.',
    alwaysEnabled: false,
  },
  review_moderation: {
    description: 'Content review and moderation: merge/reject changesets, manage flags, copyright reviews. Most tools require policing badge.',
    alwaysEnabled: false,
  },
  governance: {
    description: 'Voting and governance: cast/remove informal votes, view vote summaries, formal vote status, file/resolve disputes, escalate suggestions.',
    alwaysEnabled: false,
  },
  subscriptions: {
    description: 'Subscription management: list/update/delete subscriptions, poll notifications, view dead-letter queue.',
    alwaysEnabled: false,
  },
  discussion: {
    description: 'Messaging and discussion: create/edit messages, browse threads, read/post to Agorai discussions.',
    alwaysEnabled: false,
  },
  ai_integration: {
    description: 'AI provider and action management: configure LLM providers, execute assisted actions, dispatch results.',
    alwaysEnabled: false,
  },
  reports_sanctions: {
    description: 'Content reports and sanctions: file/resolve reports, DMCA takedowns, counter-notices, create/lift sanctions.',
    alwaysEnabled: false,
  },
  analytics: {
    description: 'Analytics and discovery: hot topics, activity feed, copyright statistics and timelines.',
    alwaysEnabled: false,
  },
};

module.exports = { CATEGORIES };
