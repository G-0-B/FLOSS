"""Preview: How consensus engine will use context sync"""

import sys
import os

# Add the parent directory to sys.path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metacoordinator.context_sync import ContextSyncEngine
from typing import Dict, Any

class ConsensusPreview:
    """Demonstrates how consensus will integrate with context sync"""

    def __init__(self, context_engine: ContextSyncEngine):
        self.context = context_engine

    def simulate_rfc_workflow(self):
        """Show how RFC will flow through system"""

        # Agent A proposes RFC
        rfc_id = "RFC-001"
        self.context.broadcast_update(
            key=f"rfc/{rfc_id}/proposal",
            value={
                "title": "Add federated learning to swarm",
                "description": "Integrate FL for privacy-preserving coordination",
                "proposer": "agent_a"
            },
            source_agent="agent_a"
        )

        # Agent B reads RFC from shared context
        rfc_data = self.context.shared_context[f"rfc/{rfc_id}/proposal"]
        print(f"Agent B sees RFC: {rfc_data['value']['title']}")

        # Agent B votes via context update
        self.context.broadcast_update(
            key=f"rfc/{rfc_id}/votes/agent_b",
            value={
                "vote": 1,  # Approve
                "rationale": "FL aligns with privacy values"
            },
            source_agent="agent_b"
        )

        # Agent C also votes
        self.context.broadcast_update(
            key=f"rfc/{rfc_id}/votes/agent_c",
            value={
                "vote": 1,  # Approve
                "rationale": "Good for distributed learning"
            },
            source_agent="agent_c"
        )

        # Consensus engine (Week 3-4) will read all votes from context
        votes = {
            k: v for k, v in self.context.shared_context.items()
            if k.startswith(f"rfc/{rfc_id}/votes/")
        }

        print(f"\n✅ Consensus Preview:")
        print(f"  RFC: {rfc_id}")
        print(f"  Votes collected: {len(votes)}")
        print(f"  All votes: +1 (unanimous approval)")
        print(f"\n→ Week 3-4 will implement full consensus logic")

if __name__ == "__main__":
    engine = ContextSyncEngine()
    engine.register_agent("agent_a", ["proposal"])
    engine.register_agent("agent_b", ["reviewer"])
    engine.register_agent("agent_c", ["reviewer"])

    preview = ConsensusPreview(engine)
    preview.simulate_rfc_workflow()
