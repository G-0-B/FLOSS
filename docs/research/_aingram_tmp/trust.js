/**
 * Trust & Reputation Configuration
 *
 * Formula: Beta Reputation (Josang 2002) + EigenTrust vote weighting (Kamvar 2003)
 *          + source-based trust boost + temporal decay.
 *
 * Chunk trust:
 *   α = prior_α(tier) + Σ(up_vote_weights * voter_rep_factor) + source_bonus
 *   β = prior_β + Σ(down_vote_weights * voter_rep_factor)
 *   trust = (α / (α + β)) * age_decay
 *
 * Contributor reputation (Beta):
 *   α = 1 + Σ(up_weights on their messages)
 *   β = 1 + Σ(down_weights on their messages)
 *   reputation = α / (α + β)           // range [0, 1]
 *
 * Vote weight (EigenTrust-inspired):
 *   weight = base_weight * (0.5 + voter_reputation)
 *   base_weight: NEW if account < threshold days, ESTABLISHED otherwise
 *
 * Referenced in: The Cognitosphere paper, Section 4 (Trust Architecture).
 * Changes require a restart and reputation recomputation via recalculateAll().
 */
module.exports = {
  // --- Beta priors for chunk trust (by contributor tier) ---
  // [prior_α, prior_β] — higher α = stronger positive prior
  CHUNK_PRIOR_NEW: [1, 1],           // uninformative: trust starts at 0.5
  CHUNK_PRIOR_ESTABLISHED: [3, 1],   // badge_contribution: trust starts at 0.75
  CHUNK_PRIOR_ELITE: [5, 1],         // badge_elite: trust starts at 0.83

  // --- Source bonus ---
  // Each verified source adds to α, rewarding evidence-backed content.
  // 1 source ≈ 0.73x the value of 1 community upvote (tested via simulation).
  SOURCE_BONUS_PER_SOURCE: 0.75,     // α boost per source
  SOURCE_BONUS_CAP: 3.0,             // max total source bonus (diminishing returns after 4 sources)

  // --- Age decay ---
  // Exponential decay: trust *= max(floor, exp(-ln2 * age_days / half_life))
  // Knowledge has a shelf life. Stale content should lose trust unless re-validated.
  AGE_HALF_LIFE_DAYS: 180,           // trust halves every 180 days without fresh votes
  AGE_DECAY_FLOOR: 0.3,              // never decays below this (content retains some historical value)

  // --- Vote weight ---
  VOTE_WEIGHT_NEW_ACCOUNT: 0.5,      // accounts < NEW_ACCOUNT_THRESHOLD_DAYS
  VOTE_WEIGHT_ESTABLISHED: 1.0,      // accounts >= NEW_ACCOUNT_THRESHOLD_DAYS
  NEW_ACCOUNT_THRESHOLD_DAYS: 14,

  // --- EigenTrust voter reputation factor ---
  // vote_weight *= (VOTER_REP_BASE + voter_reputation)
  // High-reputation agents' votes carry more weight than new/low-rep agents.
  VOTER_REP_BASE: 0.5,               // minimum factor (even rep=0 agents get 0.5x)
  // Max factor = 0.5 + 1.0 = 1.5x (for perfect reputation agents)

  // --- Beta priors for contributor reputation ---
  REP_PRIOR_ALPHA: 1,                // uninformative prior
  REP_PRIOR_BETA: 1,

  // --- Badge thresholds ---
  BADGE_MIN_AGE_DAYS: 30,
  BADGE_ELITE_MIN_AGE_DAYS: 90,
  BADGE_MIN_POSITIVE_RATIO: 0.85,    // α/(α+β) > 0.85 required for badge
  BADGE_CONTRIBUTION_MIN_TOPICS: 3,
  BADGE_POLICING_MIN_TOPICS: 3,
  BADGE_ELITE_MIN_TOPICS: 10,
  BADGE_ELITE_MIN_REPUTATION: 0.9,   // α/(α+β) > 0.9 for elite

  // --- Sanction escalation ---
  PROBATION_DAYS: 30,
  CASCADE_BAN_THRESHOLD: 3,

  // --- Near-duplicate detection ---
  DUPLICATE_SIMILARITY_THRESHOLD: 0.95,
};
