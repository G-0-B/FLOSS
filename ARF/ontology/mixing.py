"""Meaningful mixing logic for interaction patterns."""

from .patterns import InteractionPattern


class PatternMixer:
    """
    Mixes two interaction patterns to create a new hybrid pattern.
    """

    @staticmethod
    def mix(
        pattern_a: InteractionPattern,
        pattern_b: InteractionPattern,
        strategy: str = "interleave",
    ) -> InteractionPattern:
        """
        Combines two patterns.

        Args:
            pattern_a: First pattern.
            pattern_b: Second pattern.
            strategy: Mixing strategy ('interleave', 'append', 'llm').

        Returns:
            A new InteractionPattern.
        """
        new_name = f"{pattern_a.name} + {pattern_b.name}"
        new_desc = f"A hybrid of {pattern_a.name} and {pattern_b.name}."
        new_keywords = list(set(pattern_a.keywords + pattern_b.keywords))

        if strategy == "interleave":
            new_structure = []
            len_a = len(pattern_a.structure)
            len_b = len(pattern_b.structure)
            max_len = max(len_a, len_b)

            for i in range(max_len):
                if i < len_a:
                    new_structure.append(f"[A] {pattern_a.structure[i]}")
                if i < len_b:
                    new_structure.append(f"[B] {pattern_b.structure[i]}")

        elif strategy == "append":
            new_structure = pattern_a.structure + pattern_b.structure

        else:
            # Default fallback
            new_structure = pattern_a.structure + pattern_b.structure

        return InteractionPattern(
            name=new_name,
            description=new_desc,
            structure=new_structure,
            keywords=new_keywords,
        )

    async def mix_with_llm(
        self, pattern_a: InteractionPattern, pattern_b: InteractionPattern, llm_client
    ) -> InteractionPattern:
        """
        Uses an LLM to creatively mix patterns.
        (Placeholder for future implementation)
        """
        del llm_client
        return self.mix(pattern_a, pattern_b, strategy="append")
