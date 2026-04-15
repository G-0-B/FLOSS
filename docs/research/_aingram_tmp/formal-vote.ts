/**
 * Formal vote domain logic — pure functions, no I/O.
 * Implements commit-reveal voting protocol from Paper 3 (Deliberative Curation).
 *
 * Commit phase: voter submits SHA-256(voteValue || reasonTag || salt)
 * Reveal phase: voter reveals plaintext, server verifies against hash
 */

import { createHash } from 'crypto';

// --- Constants ---

export const FORMAL_REASON_TAGS = [
  'accurate',
  'well_sourced',
  'novel',
  'redundant',
  'inaccurate',
  'unsourced',
  'harmful',
  'unclear',
] as const;

export type FormalReasonTag = typeof FORMAL_REASON_TAGS[number];

export type VoteValue = -1 | 0 | 1;

export type VoteDecision = 'accept' | 'reject' | 'indeterminate' | 'no_quorum';

export interface WeightedVote {
  weight: number;
  voteValue: VoteValue;
}

// --- Functions ---

/**
 * Compute SHA-256 commitment hash for a vote.
 * Format: SHA-256(voteValue + "|" + reasonTag + "|" + salt)
 */
export function hashCommitment(voteValue: VoteValue, reasonTag: string, salt: string): string {
  const payload = `${voteValue}|${reasonTag}|${salt}`;
  return createHash('sha256').update(payload).digest('hex');
}

/**
 * Verify that a reveal matches a previously submitted commitment hash.
 */
export function verifyReveal(
  commitHash: string,
  voteValue: VoteValue,
  reasonTag: string,
  salt: string,
): boolean {
  const expected = hashCommitment(voteValue, reasonTag, salt);
  return commitHash === expected;
}

/**
 * Clamp a raw vote weight to [wMin, wMax].
 */
export function clampWeight(rawWeight: number, wMin: number, wMax: number): number {
  if (rawWeight < wMin) return wMin;
  if (rawWeight > wMax) return wMax;
  return rawWeight;
}

/**
 * Compute the weighted vote score V(c) = Σ w_i * v_i
 * Only includes revealed votes (with numeric voteValue).
 */
export function computeVoteScore(votes: WeightedVote[]): number {
  let score = 0;
  for (const v of votes) {
    score += v.weight * v.voteValue;
  }
  return score;
}

/**
 * Evaluate the voting decision based on score, quorum, and thresholds.
 *
 * - no_quorum: not enough revealed votes (count < qMin)
 * - accept: V(c) >= tauAccept AND quorum met
 * - reject: V(c) <= tauReject (regardless of quorum — rejection is protective)
 * - indeterminate: between thresholds with quorum met
 */
export function evaluateDecision(
  score: number,
  revealedCount: number,
  qMin: number,
  tauAccept: number,
  tauReject: number,
): VoteDecision {
  // Rejection is protective: even below quorum, if score is very negative, reject
  if (score <= tauReject) {
    return 'reject';
  }

  if (revealedCount < qMin) {
    return 'no_quorum';
  }

  if (score >= tauAccept) {
    return 'accept';
  }

  return 'indeterminate';
}

/**
 * Validate that a reason tag is a valid formal vote reason.
 */
export function isValidFormalReasonTag(tag: string): tag is FormalReasonTag {
  return (FORMAL_REASON_TAGS as readonly string[]).includes(tag);
}
