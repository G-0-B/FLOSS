# Quickstart: Desktop Pony RSA Swarm

Welcome to the FLOSSI0ULLK project! This guide will help you get the "Desktop Pony RSA Swarm" running on your local machine in just a few minutes.

This implementation brings to life the project's core principles, allowing multiple AI agents (ponies) to collaborate on tasks using a novel Recursive Self-Aggregation (RSA) algorithm.

## Prerequisites

- **Python 3.8+**
- **pip** (Python's package installer)

## 1. Installation

First, you need to install the core dependencies.

Navigate to the `pwnies` directory in your terminal:
```bash
cd ARF/pwnies
```

Now, install the required Python packages using the `requirements_swarm.txt` file:
```bash
pip install -r requirements_swarm.txt
```
This will install `aiohttp` for asynchronous web requests to the Horde.AI network and `numpy` for numerical operations.

## 2. Running the Validation Tests (Optional but Recommended)

Before running the swarm, you can run the built-in tests to ensure everything is set up correctly. These tests validate the core criteria outlined in the project's Architectural Decision Records (ADR-0).

```bash
python desktop_pony_swarm/tests/test_swarm.py
```
If the tests pass, you're ready to go!

## 3. Running the Swarm

The swarm can be run in two modes: `demo` and `interactive`.

### Demo Mode

This mode runs a series of predefined prompts to showcase the swarm's capabilities without requiring user input. It's a great way to see the system in action for the first time.

From the `ARF/pwnies` directory, run:
```bash
python run_swarm.py demo
```
You will see the ponies "thinking" and then a final, aggregated response, along with performance metrics.

### Interactive Mode

This mode allows you to chat with the swarm directly. Ask it a question and the pony agents will work together to provide a refined answer.

From the `ARF/pwnies` directory, run:
```bash
python run_swarm.py
```

Wait for the prompt, then type your question and press Enter.

**Example:**
```
You: What is 15 * 23?
🤔 Ponies thinking...

🐴 Swarm Response:
15 * 23 = 345. Here's the work:
15 * 20 = 300
15 * 3 = 45
300 + 45 = 345

📊 Metrics: 12 generations, 15.3s, diversity=0.234
```

## What's Next?

Congratulations, you've successfully run the Desktop Pony RSA Swarm!

To dive deeper into the project, check out these resources:

- **The Master Guide:** `ARF/FLOSS_MASTER_GUIDE.md` provides a central hub for all project documentation.
- **Detailed README:** `ARF/pwnies/README.md` contains in-depth information about the swarm's architecture, research background, configuration, and advanced features.
- **Troubleshooting:** The `ARF/pwnies/SETUP_TROUBLESHOOTING.md` file has solutions for common issues.
