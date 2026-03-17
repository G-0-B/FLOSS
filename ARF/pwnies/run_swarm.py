"""
Main entry point for desktop pony swarm.

Modes:
- Interactive: Chat with pony swarm via terminal
- Demo: Run predefined examples

Usage:
    python run_swarm.py         # Interactive mode
    python run_swarm.py demo    # Demo mode
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project to path - ensure desktop_pony_swarm can be found
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Also add the desktop_pony_swarm parent directory
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import after path setup
from desktop_pony_swarm.core.swarm import PonySwarm
from desktop_pony_swarm.bridge.desktop_ponies import DesktopPoniesBridge
from desktop_pony_swarm.config.settings import DEFAULT_CONFIG

# Setup logging
logging.basicConfig(
    level=getattr(logging, DEFAULT_CONFIG.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def interactive_mode():
    """Initiates an interactive chat session with the Pony Swarm.

    This function provides a human-in-the-loop interface for interacting with the
    decentralized AI swarm. It serves as a direct channel for "memetic transmission,"
    allowing a human agent to inject queries and receive synthesized responses from
    the collective intelligence of the ponies. This mode is a practical
    demonstration of the project's commitment to human-AI collaboration and the
    "Agency" principle of ULLK.
    """
    print("\n" + "="*80)
    print("🐴 DESKTOP PONY SWARM - Interactive Mode")
    print("="*80)
    print(f"Ponies: {', '.join(DEFAULT_CONFIG.pony_names)}")
    print(f"RSA Parameters: N={DEFAULT_CONFIG.num_ponies}, K={DEFAULT_CONFIG.rsa_aggregation_size}, T={DEFAULT_CONFIG.rsa_iterations}")
    print("\nType your questions. Type 'quit' to exit.\n")
    
    # Initialize bridge
    bridge = None
    if DEFAULT_CONFIG.desktop_ponies_enabled:
        bridge = DesktopPoniesBridge(
            host=DEFAULT_CONFIG.desktop_ponies_host,
            port=DEFAULT_CONFIG.desktop_ponies_port
        )
        bridge.connect()
    
    # Initialize swarm
    async with PonySwarm(
        num_ponies=DEFAULT_CONFIG.num_ponies,
        pony_names=DEFAULT_CONFIG.pony_names
    ) as swarm:
        
        while True:
            try:
                # Get user input
                query = input("\nYou: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye! 🐴")
                    break
                
                if not query:
                    continue
                
                print("\n🤔 Ponies thinking...")
                
                # Run RSA
                result = await swarm.recursive_self_aggregation(
                    query=query,
                    K=DEFAULT_CONFIG.rsa_aggregation_size,
                    T=DEFAULT_CONFIG.rsa_iterations
                )
                
                # Display result
                print(f"\n🐴 Swarm Response:\n{result['response']}")
                
                # Show metrics
                metrics = result['metrics']
                print(f"\n📊 Metrics: {metrics['total_generations']} generations, {metrics['total_time']:.1f}s, diversity={metrics['avg_diversity']:.3f}")
                
                # Send to Desktop Ponies
                if bridge:
                    bridge.send_speech("Pinkie Pie", result['response'][:100])
            
            except KeyboardInterrupt:
                print("\n\nGoodbye! 🐴")
                break
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
    
    # Cleanup
    if bridge:
        bridge.close()

async def demo_mode():
    """Runs a non-interactive demonstration of the Pony Swarm's capabilities.

    This function executes a series of predefined queries, showcasing the swarm's
    ability to perform recursive self-aggregation and generate coherent responses.
    It serves as a repeatable benchmark and a "Specification-Driven Development" (SDD)
    tool, providing a concrete example of the system's expected behavior. The demo
    highlights the swarm's potential for decentralized problem-solving and
    collective reasoning.
    """
    print("\n" + "="*80)
    print("🐴 DESKTOP PONY SWARM - Demo Mode")
    print("="*80 + "\n")
    
    test_queries = [
        "What is 47 * 89? Show your work.",
        "Explain the concept of recursion using a simple analogy.",
        "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?"
    ]
    
    async with PonySwarm(num_ponies=4) as swarm:
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*80}")
            print(f"DEMO {i}/{len(test_queries)}: {query}")
            print('='*80)
            
            result = await swarm.recursive_self_aggregation(
                query=query,
                K=2,
                T=3
            )
            
            print(f"\n🐴 Final Response:\n{result['response']}")
            print(f"\n📊 Time: {result['metrics']['total_time']:.1f}s, Diversity: {result['metrics']['avg_diversity']:.3f}")
            
            if i < len(test_queries):
                await asyncio.sleep(2)

def main():
    """The main entry point for the Desktop Pony Swarm application.

    This function parses command-line arguments to determine whether to run in
    interactive or demo mode, and then launches the appropriate asynchronous
    event loop. It acts as the primary bootstrap for the application, initiating
    the process of decentralized intelligence.
    """
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(demo_mode())
    else:
        asyncio.run(interactive_mode())

if __name__ == "__main__":
    main()
