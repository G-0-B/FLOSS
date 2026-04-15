/**
 * Vote weight calculation — pure function, no I/O.
 */

export interface VoteWeightParams {
  accountCreatedAt: Date;
  now?: Date;
  newAccountThresholdDays: number;
  weightNew: number;
  weightEstablished: number;
  voterReputation: number;
  voterRepBase: number;
}

/**
 * Calculate the weight of a vote based on account age and voter reputation.
 * Base weight: age dampening (new accounts get lower weight).
 * EigenTrust factor: voter's own reputation amplifies/dampens their vote.
 */
export function calculateVoteWeight(params: VoteWeightParams): number {
  const {
    accountCreatedAt,
    now = new Date(),
    newAccountThresholdDays,
    weightNew,
    weightEstablished,
    voterReputation,
    voterRepBase,
  } = params;

  const accountAgeMs = now.getTime() - accountCreatedAt.getTime();
  const thresholdMs = newAccountThresholdDays * 24 * 60 * 60 * 1000;

  const baseWeight = accountAgeMs < thresholdMs ? weightNew : weightEstablished;
  const repFactor = voterRepBase + voterReputation;

  return baseWeight * repFactor;
}
