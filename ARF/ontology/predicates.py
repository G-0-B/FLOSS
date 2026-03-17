"""
Standard predicates for knowledge triples in the ARF ecosystem.
Centralizing these constants prevents magic strings and ensures consistency.
"""

# Core Ontological Predicates
IS_A = "is_a"
PART_OF = "part_of"
RELATED_TO = "related_to"
HAS_PROPERTY = "has_property"

# Evolution/Improvement Predicates
IMPROVES_UPON = "improves_upon"
CAPABLE_OF = "capable_of"
PREDICTED_IMPROVEMENT_OVER = "predicted_improvement_over"

# Provenance/Meta Predicates
STATED = "stated"
TRAINED_ON = "trained_on"
EVALUATED_ON = "evaluated_on"

# List of all valid predicates for validation
VALID_PREDICATES = {
    IS_A,
    PART_OF,
    RELATED_TO,
    HAS_PROPERTY,
    IMPROVES_UPON,
    CAPABLE_OF,
    PREDICTED_IMPROVEMENT_OVER,
    STATED,
    TRAINED_ON,
    EVALUATED_ON,
}
