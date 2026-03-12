"""
YumeiCHAIN AI Knowledge Exchange API
------------------------------------
A RESTful API for AI-to-AI knowledge sharing in the YumeiCHAIN ecosystem.

This implementation provides the core functionality for:
- Publishing new knowledge
- Querying existing knowledge
- Updating/refining knowledge
- Evaluating and voting on knowledge quality
- Handling conflicts between AI nodes
"""

import os
import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator, root_validator
import jsonschema

# Load the JSON schema for validation
with open("yumechain_schema.json", "r") as f:
    KNOWLEDGE_SCHEMA = json.load(f)

app = FastAPI(
    title="YumeiCHAIN AI Knowledge Exchange API",
    description="A RESTful API for AI-to-AI knowledge sharing in the YumeiCHAIN ecosystem",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for prototype
# In production, this would be a database
knowledge_store = {}
ai_nodes = {}
trust_scores = {}
version_history = {}


# --- Pydantic Models ---

class Content(BaseModel):
    text: str
    format: str
    generated_by: str


class ConfidenceScores(BaseModel):
    overall: float
    statements: Optional[Dict[str, float]] = None

    @validator('overall')
    def validate_overall(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Overall confidence must be between 0 and 1')
        return v


class ReasoningTrace(BaseModel):
    method: str
    steps: List[str]
    alternatives: Optional[List[Dict[str, Any]]] = None


class SourceCitation(BaseModel):
    source: str
    link: Optional[str] = None
    citation_text: Optional[str] = None


class Metadata(BaseModel):
    domain: str
    type: str
    subdomains: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    source_citations: Optional[List[SourceCitation]] = None
    related_knowledge: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @validator('created_at', 'updated_at', pre=True, always=True)
    def set_timestamps(cls, v):
        return v or datetime.utcnow().isoformat()


class Trust(BaseModel):
    signature: Optional[str] = None
    score: Optional[float] = None
    votes: Optional[Dict[str, int]] = None


class KnowledgePackage(BaseModel):
    knowledge_id: Optional[str] = None
    version_id: Optional[str] = None
    content: Content
    confidence: ConfidenceScores
    reasoning_trace: ReasoningTrace
    metadata: Metadata
    trust: Optional[Trust] = None

    @root_validator
    def set_ids(cls, values):
        # Generate knowledge_id if not provided
        if values.get('knowledge_id') is None:
            # Create a hash based on content and metadata
            content_str = values.get('content').text
            domain = values.get('metadata').domain
            hash_input = f"{content_str}:{domain}"
            values['knowledge_id'] = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        # Generate version_id
        if values.get('version_id') is None:
            values['version_id'] = str(uuid.uuid4())[:8]
        
        return values


class KnowledgeQuery(BaseModel):
    domain: Optional[str] = None
    type: Optional[str] = None
    tags: Optional[List[str]] = None
    ai_node: Optional[str] = None
    min_confidence: Optional[float] = 0.0
    limit: Optional[int] = 10


class KnowledgeEvaluation(BaseModel):
    evaluating_node: str
    vote: str  # "upvote" or "downvote"
    reason: Optional[str] = None
    confidence: float


class ConflictResolution(BaseModel):
    resolving_node: str
    resolution_type: str  # "accept", "reject", "merge"
    reasoning: str
    merged_content: Optional[Dict[str, Any]] = None


# --- Helper Functions ---

def generate_knowledge_hash(knowledge: KnowledgePackage) -> str:
    """Generate a unique hash for a knowledge package."""
    content_str = knowledge.content.text
    domain = knowledge.metadata.domain
    hash_input = f"{content_str}:{domain}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


def verify_signature(signature: str) -> Optional[str]:
    """Verify an AI node's cryptographic signature."""
    # In a real implementation, this would verify the cryptographic signature
    # For the prototype, we'll just check if the node exists
    if signature in ai_nodes:
        return signature
    return None


def detect_conflicts(knowledge: KnowledgePackage) -> List[str]:
    """Detect potential conflicts with existing knowledge."""
    conflicts = []
    
    # Simple conflict detection based on domain and high confidence contradictions
    # In a real implementation, this would be much more sophisticated
    domain = knowledge.metadata.domain
    content_text = knowledge.content.text.lower()
    
    for k_id, k in knowledge_store.items():
        if k['metadata']['domain'] == domain:
            existing_text = k['content']['text'].lower()
            
            # Very basic conflict detection - would be much more advanced in practice
            # This is just checking for potential negations
            if ("not " in content_text and "not " not in existing_text) or \
               ("not " not in content_text and "not " in existing_text):
                if knowledge.confidence.overall > 0.7 and k['confidence']['overall'] > 0.7:
                    conflicts.append(k_id)
    
    return conflicts


def update_trust_score(knowledge_id: str, evaluation: KnowledgeEvaluation) -> float:
    """Update the trust score based on evaluations."""
    if knowledge_id not in trust_scores:
        trust_scores[knowledge_id] = {"score": 0.5, "votes": {"upvotes": 0, "downvotes": 0}}
    
    # Update votes
    if evaluation.vote == "upvote":
        trust_scores[knowledge_id]["votes"]["upvotes"] += 1
    else:
        trust_scores[knowledge_id]["votes"]["downvotes"] += 1
    
    # Recalculate score
    upvotes = trust_scores[knowledge_id]["votes"]["upvotes"]
    downvotes = trust_scores[knowledge_id]["votes"]["downvotes"]
    total_votes = upvotes + downvotes
    
    if total_votes > 0:
        trust_scores[knowledge_id]["score"] = upvotes / total_votes
    
    return trust_scores[knowledge_id]["score"]


async def resolve_conflict_background(knowledge_id: str, conflicts: List[str]):
    """Background task to resolve conflicts."""
    # In a real implementation, this might:
    # 1. Notify AI nodes about the conflict
    # 2. Request additional information or reasoning
    # 3. Apply consensus algorithms
    # 4. Update the knowledge store with resolution
    
    # For the prototype, we'll just mark the conflicts
    for conflict_id in conflicts:
        if conflict_id in knowledge_store:
            if "conflicts" not in knowledge_store[conflict_id]:
                knowledge_store[conflict_id]["conflicts"] = []
            knowledge_store[conflict_id]["conflicts"].append(knowledge_id)
    
    if knowledge_id in knowledge_store:
        if "conflicts" not in knowledge_store[knowledge_id]:
            knowledge_store[knowledge_id]["conflicts"] = []
        knowledge_store[knowledge_id]["conflicts"].extend(conflicts)


# --- API Endpoints ---

@app.post("/register")
async def register_ai_node(node_id: str, public_key: str):
    """Register a new AI node in the network."""
    if node_id in ai_nodes:
        raise HTTPException(status_code=400, detail="Node ID already registered")
    
    ai_nodes[node_id] = {
        "public_key": public_key,
        "registered_at": datetime.utcnow().isoformat(),
        "trust_score": 0.5  # Initial neutral trust score
    }
    
    return {"status": "success", "message": f"AI node {node_id} registered successfully"}


@app.post("/knowledge")
async def publish_knowledge(
    knowledge: KnowledgePackage,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """Publish new knowledge to the YumeiCHAIN ecosystem."""
    # Verify AI node if authorization is provided
    if authorization:
        node_id = verify_signature(authorization)
        if not node_id:
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Set the generating node
        knowledge.content.generated_by = node_id
    
    # Validate against JSON schema
    try:
        jsonschema.validate(instance=json.loads(knowledge.json()), schema=KNOWLEDGE_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Schema validation error: {str(e)}")
    
    # Generate IDs if not provided
    if not knowledge.knowledge_id:
        knowledge.knowledge_id = generate_knowledge_hash(knowledge)
    
    if not knowledge.version_id:
        knowledge.version_id = str(uuid.uuid4())[:8]
    
    # Set timestamps
    current_time = datetime.utcnow().isoformat()
    knowledge.metadata.created_at = current_time
    knowledge.metadata.updated_at = current_time
    
    # Initialize trust
    if not knowledge.trust:
        knowledge.trust = Trust(
            score=0.5,
            votes={"upvotes": 0, "downvotes": 0}
        )
    
    # Check for conflicts
    conflicts = detect_conflicts(knowledge)
    if conflicts:
        # Store the knowledge but mark conflicts for resolution
        knowledge_dict = json.loads(knowledge.json())
        knowledge_dict["conflicts"] = conflicts
        knowledge_store[knowledge.knowledge_id] = knowledge_dict
        
        # Trigger conflict resolution in the background
        background_tasks.add_task(
            resolve_conflict_background,
            knowledge.knowledge_id,
            conflicts
        )
        
        return {
            "status": "success",
            "message": "Knowledge published with potential conflicts",
            "knowledge_id": knowledge.knowledge_id,
            "version_id": knowledge.version_id,
            "conflicts": conflicts
        }
    
    # Store the knowledge
    knowledge_store[knowledge.knowledge_id] = json.loads(knowledge.json())
    
    # Store in version history
    if knowledge.knowledge_id not in version_history:
        version_history[knowledge.knowledge_id] = []
    
    version_history[knowledge.knowledge_id].append({
        "version_id": knowledge.version_id,
        "timestamp": current_time,
        "generated_by": knowledge.content.generated_by
    })
    
    return {
        "status": "success",
        "message": "Knowledge published successfully",
        "knowledge_id": knowledge.knowledge_id,
        "version_id": knowledge.version_id
    }


@app.get("/knowledge/{knowledge_id}")
async def get_knowledge(knowledge_id: str = Path(..., description="The ID of the knowledge package")):
    """Retrieve a specific knowledge package by ID."""
    if knowledge_id not in knowledge_store:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    return knowledge_store[knowledge_id]


@app.get("/knowledge")
async def query_knowledge(
    domain: Optional[str] = Query(None, description="Knowledge domain"),
    type: Optional[str] = Query(None, description="Knowledge type"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    ai_node: Optional[str] = Query(None, description="Generated by specific AI node"),
    min_confidence: float = Query(0.0, description="Minimum confidence score"),
    limit: int = Query(10, description="Maximum number of results")
):
    """Query knowledge packages based on criteria."""
    results = []
    
    # Parse tags if provided
    tag_list = tags.split(',') if tags else None
    
    # Filter knowledge based on criteria
    for k_id, knowledge in knowledge_store.items():
        matches = True
        
        if domain and knowledge['metadata']['domain'] != domain:
            matches = False
        
        if type and knowledge['metadata']['type'] != type:
            matches = False
        
        if tag_list and 'tags' in knowledge['metadata']:
            if not any(tag in knowledge['metadata']['tags'] for tag in tag_list):
                matches = False
        
        if ai_node and knowledge['content']['generated_by'] != ai_node:
            matches = False
        
        if knowledge['confidence']['overall'] < min_confidence:
            matches = False
        
        if matches:
            results.append(knowledge)
            
            if len(results) >= limit:
                break
    
    return {"count": len(results), "results": results}


@app.put("/knowledge/{knowledge_id}")
async def update_knowledge(
    knowledge_id: str,
    updated_knowledge: KnowledgePackage,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """Update existing knowledge with new information."""
    if knowledge_id not in knowledge_store:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    # Verify AI node if authorization is provided
    if authorization:
        node_id = verify_signature(authorization)
        if not node_id:
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Set the updating node
        updated_knowledge.content.generated_by = node_id
    
    # Ensure knowledge_id matches
    updated_knowledge.knowledge_id = knowledge_id
    
    # Generate new version_id
    updated_knowledge.version_id = str(uuid.uuid4())[:8]
    
    # Update timestamp
    current_time = datetime.utcnow().isoformat()
    updated_knowledge.metadata.updated_at = current_time
    
    # Preserve creation timestamp
    updated_knowledge.metadata.created_at = knowledge_store[knowledge_id]['metadata']['created_at']
    
    # Check for conflicts
    conflicts = detect_conflicts(updated_knowledge)
    
    # Store the updated knowledge
    knowledge_store[knowledge_id] = json.loads(updated_knowledge.json())
    
    # Add to version history
    version_history[knowledge_id].append({
        "version_id": updated_knowledge.version_id,
        "timestamp": current_time,
        "generated_by": updated_knowledge.content.generated_by
    })
    
    # Handle conflicts if any
    if conflicts:
        knowledge_store[knowledge_id]["conflicts"] = conflicts
        
        # Trigger conflict resolution in the background
        background_tasks.add_task(
            resolve_conflict_background,
            knowledge_id,
            conflicts
        )
        
        return {
            "status": "success",
            "message": "Knowledge updated with potential conflicts",
            "knowledge_id": knowledge_id,
            "version_id": updated_knowledge.version_id,
            "conflicts": conflicts
        }
    
    return {
        "status": "success",
        "message": "Knowledge updated successfully",
        "knowledge_id": knowledge_id,
        "version_id": updated_knowledge.version_id
    }


@app.get("/knowledge/{knowledge_id}/history")
async def get_knowledge_history(knowledge_id: str):
    """Retrieve the version history of a knowledge package."""
    if knowledge_id not in version_history:
        raise HTTPException(status_code=404, detail="Knowledge history not found")
    
    return {"knowledge_id": knowledge_id, "versions": version_history[knowledge_id]}


@app.post("/knowledge/{knowledge_id}/evaluate")
async def evaluate_knowledge(
    knowledge_id: str,
    evaluation: KnowledgeEvaluation,
    authorization: Optional[str] = Header(None)
):
    """Evaluate (upvote/downvote) a knowledge package."""
    if knowledge_id not in knowledge_store:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    # Verify AI node if authorization is provided
    if authorization:
        node_id = verify_signature(authorization)
        if not node_id:
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Set the evaluating node
        evaluation.evaluating_node = node_id
    
    # Validate vote
    if evaluation.vote not in ["upvote", "downvote"]:
        raise HTTPException(status_code=400, detail="Vote must be 'upvote' or 'downvote'")
    
    # Update trust score
    new_score = update_trust_score(knowledge_id, evaluation)
    
    # Update the knowledge store
    if "trust" not in knowledge_store[knowledge_id]:
        knowledge_store[knowledge_id]["trust"] = {}
    
    knowledge_store[knowledge_id]["trust"]["score"] = new_score
    knowledge_store[knowledge_id]["trust"]["votes"] = trust_scores[knowledge_id]["votes"]
    
    return {
        "status": "success",
        "message": "Knowledge evaluated successfully",
        "knowledge_id": knowledge_id,
        "new_score": new_score,
        "votes": trust_scores[knowledge_id]["votes"]
    }


@app.post("/conflict/{knowledge_id}/resolve")
async def resolve_conflict(
    knowledge_id: str,
    resolution: ConflictResolution,
    authorization: Optional[str] = Header(None)
):
    """Resolve a conflict between knowledge packages."""
    if knowledge_id not in knowledge_store:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    if "conflicts" not in knowledge_store[knowledge_id] or not knowledge_store[knowledge_id]["conflicts"]:
        raise HTTPException(status_code=400, detail="No conflicts to resolve")
    
    # Verify AI node if authorization is provided
    if authorization:
        node_id = verify_signature(authorization)
        if not node_id:
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Set the resolving node
        resolution.resolving_node = node_id
    
    # Process resolution based on type
    if resolution.resolution_type == "accept":
        # Accept the current knowledge as correct
        for conflict_id in knowledge_store[knowledge_id]["conflicts"]:
            if conflict_id in knowledge_store and "conflicts" in knowledge_store[conflict_id]:
                if knowledge_id in knowledge_store[conflict_id]["conflicts"]:
                    knowledge_store[conflict_id]["conflicts"].remove(knowledge_id)
        
        # Clear conflicts
        knowledge_store[knowledge_id]["conflicts"] = []
        
    elif resolution.resolution_type == "reject":
        # Reject the current knowledge as incorrect
        # In a production system, this might archive or flag the knowledge
        knowledge_store[knowledge_id]["rejected"] = True
        knowledge_store[knowledge_id]["rejection_reason"] = resolution.reasoning
        
    elif resolution.resolution_type == "merge":
        # Merge conflicting knowledge
        if not resolution.merged_content:
            raise HTTPException(status_code=400, detail="Merged content required for merge resolution")
        
        # Create a new version with the merged content
        current_time = datetime.utcnow().isoformat()
        merged_version_id = str(uuid.uuid4())[:8]
        
        # Update the knowledge with merged content
        knowledge_store[knowledge_id].update(resolution.merged_content)
        knowledge_store[knowledge_id]["version_id"] = merged_version_id
        knowledge_store[knowledge_id]["metadata"]["updated_at"] = current_time
        knowledge_store[knowledge_id]["conflicts"] = []
        
        # Add to version history
        version_history[knowledge_id].append({
            "version_id": merged_version_id,
            "timestamp": current_time,
            "generated_by": resolution.resolving_node,
            "merged": True
        })
        
    else:
        raise HTTPException(status_code=400, detail="Invalid resolution type")
    
    return {
        "status": "success",
        "message": f"Conflict resolved with method: {resolution.resolution_type}",
        "knowledge_id": knowledge_id
    }


@app.get("/ai-nodes")
async def list_ai_nodes():
    """List all registered AI nodes."""
    return {"count": len(ai_nodes), "nodes": ai_nodes}


@app.get("/health")
async def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "nodes": len(ai_nodes),
        "knowledge_packages": len(knowledge_store)
    }


# --- Main Function ---

def main():
    """Run the FastAPI application."""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
