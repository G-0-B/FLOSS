/**
 * Chunk lifecycle state machine — pure function, no I/O.
 * Implements the 6-state lifecycle from Paper 3 (Deliberative Curation).
 *
 * States: proposed → under_review → published → disputed → retracted → superseded
 * All transitions are guarded. Invalid transitions throw LifecycleError.
 */

export const CHUNK_STATES = ['proposed', 'under_review', 'published', 'disputed', 'retracted', 'superseded'] as const;
export type ChunkState = typeof CHUNK_STATES[number];

export const LIFECYCLE_EVENTS = [
  'OBJECT',           // objection filed → proposed → under_review
  'AUTO_MERGE',       // fast-track (no objection within timeout) → proposed → published
  'WITHDRAW',         // author withdraws → proposed/under_review → retracted
  'TIMEOUT',          // review/dispute timeout → under_review/disputed → retracted
  'VOTE_ACCEPT',      // formal vote passed → under_review → published
  'VOTE_REJECT',      // formal vote rejected → under_review → retracted
  'DISPUTE',          // dispute filed → published → disputed
  'SUPERSEDE',        // newer version merged → published → superseded
  'DISPUTE_UPHELD',   // dispute resolved in favor of content → disputed → published
  'DISPUTE_REMOVED',  // dispute resolved against content → disputed → retracted
  'RESUBMIT',         // resubmission after retraction → retracted → proposed
] as const;
export type LifecycleEvent = typeof LIFECYCLE_EVENTS[number];

export class LifecycleError extends Error {
  constructor(
    public readonly currentState: ChunkState,
    public readonly event: LifecycleEvent,
    message?: string,
  ) {
    super(message || `Invalid transition: cannot apply ${event} to chunk in state ${currentState}`);
    this.name = 'LifecycleError';
  }
}

/**
 * Transition table: [currentState][event] → newState
 * Missing entries = invalid transition.
 */
const TRANSITIONS: Partial<Record<ChunkState, Partial<Record<LifecycleEvent, ChunkState>>>> = {
  proposed: {
    OBJECT: 'under_review',
    AUTO_MERGE: 'published',
    WITHDRAW: 'retracted',
    TIMEOUT: 'retracted',
  },
  under_review: {
    VOTE_ACCEPT: 'published',
    VOTE_REJECT: 'retracted',
    WITHDRAW: 'retracted',
    TIMEOUT: 'retracted',
  },
  published: {
    DISPUTE: 'disputed',
    SUPERSEDE: 'superseded',
  },
  disputed: {
    DISPUTE_UPHELD: 'published',
    DISPUTE_REMOVED: 'retracted',
    TIMEOUT: 'retracted',
  },
  retracted: {
    RESUBMIT: 'proposed',
  },
  // superseded: terminal state, no transitions out
};

/**
 * Apply an event to the current chunk state.
 * Returns the new state, or throws LifecycleError if the transition is invalid.
 */
export function transition(currentState: ChunkState, event: LifecycleEvent): ChunkState {
  const stateTransitions = TRANSITIONS[currentState];
  if (!stateTransitions) {
    throw new LifecycleError(currentState, event, `State ${currentState} has no valid transitions`);
  }

  const newState = stateTransitions[event];
  if (!newState) {
    throw new LifecycleError(currentState, event);
  }

  return newState;
}

/**
 * Check if a transition is valid without throwing.
 */
export function canTransition(currentState: ChunkState, event: LifecycleEvent): boolean {
  const stateTransitions = TRANSITIONS[currentState];
  if (!stateTransitions) return false;
  return event in stateTransitions;
}

/**
 * Get all valid events for a given state.
 */
export function validEvents(state: ChunkState): LifecycleEvent[] {
  const stateTransitions = TRANSITIONS[state];
  if (!stateTransitions) return [];
  return Object.keys(stateTransitions) as LifecycleEvent[];
}

/**
 * Map lifecycle events to retract_reason values.
 * Only applicable when transitioning TO 'retracted'.
 */
export type RetractReason = 'rejected' | 'withdrawn' | 'timeout' | 'admin' | 'copyright';

const EVENT_TO_RETRACT_REASON: Partial<Record<LifecycleEvent, RetractReason>> = {
  VOTE_REJECT: 'rejected',
  WITHDRAW: 'withdrawn',
  TIMEOUT: 'timeout',
  DISPUTE_REMOVED: 'rejected',
};

/**
 * Get the retract_reason for an event that causes retraction.
 * Returns undefined if the event doesn't cause retraction or has no default reason.
 */
export function retractReasonForEvent(event: LifecycleEvent): RetractReason | undefined {
  return EVENT_TO_RETRACT_REASON[event];
}
