import os, json
def batch_retrieve(ids, include_snippets=False):
    results = []
    for i in ids:
        entry = {"id": i, "title": f"Doc {i}"}
        if include_snippets:
            entry["snippet"] = "Lorem ipsum..."
        results.append(entry)
    return results
