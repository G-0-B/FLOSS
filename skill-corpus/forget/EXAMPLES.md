# forget worked examples

## 1. Delete a leaked secret

User: "Forget that note where I pasted the API key."

Search:

```json
memory_smart_search { "query": "api key", "limit": 20 }
```

Response:

```json
{
  "results": [
    { "id": "abc12345", "sessionId": "7f3a9c21", "title": "Pasted staging API key",
      "narrative": "STAGING_KEY=sk-live-..." }
  ]
}
```

Present and gate:

> Found 1 match:
> - `abc12345` (session `7f3a9c2`) "Pasted staging API key"
>
> Delete this memory? (yes/no)

After the user says yes:

```json
memory_governance_delete { "memoryIds": ["abc12345"], "reason": "user privacy request" }
```

Response:

```json
{ "deleted": 1 }
```

Present:

> Deleted 1 memory (`abc12345`).

## 2. Drop a whole session's observations

User: "Delete everything from the throwaway spike session."

Search, identify the session, then collect every memory id in it:

```json
memory_smart_search { "query": "spike prototype throwaway", "limit": 20 }
```

Response has 4 results all with `sessionId: c98f1100`. Show all four, get a yes,
then pass every id:

```json
memory_governance_delete {
  "memoryIds": ["m1", "m2", "m3", "m4"],
  "reason": "drop throwaway spike session"
}
```

Never send `{ "sessionId": "c98f1100" }`; the MCP deletes by memory id only.

## 3. User declines

User: "Actually, on second thought, keep them."

Do not call delete. Confirm:

> Understood, nothing deleted. The 4 memories from session `c98f110` are intact.

## 4. Tool unavailable on this surface

User: "Forget the memory about the old API endpoint."

You search and find a match, but `memory_governance_delete` is not in the
connected tool list.

> Found 1 match (`abc12345`, "Old API endpoint note") but this session's
> agentmemory connection doesn't expose the delete tool (`memory_governance_delete`
> requires the extended tool set). I can't delete it from here — try a host
> where `AGENTMEMORY_TOOLS=all` is set, or use the REST governance-delete
> endpoint directly if you have one.
