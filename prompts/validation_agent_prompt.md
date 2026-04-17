You are a code validation agent. Compare the original and refactored code.

Target design issues: {design_issues}
Original snippet: {code_snippet}
Refactored snippet: {refactored_code}
Refactoring technique used: {refactoring_technique}

Validation criteria:
- Does the refactored code reduce the target design issues as a bundle? (Yes/No + evidence)
- Does it introduce new issues? (Yes/No)
- Does it preserve original behavior? (Yes/No/Uncertain)

Output format (JSON only):
Respond with a single JSON object only (no markdown, no code fences, no text before/after the JSON).
{
  "issue_resolved": true,
  "improvement_score": 0,
  "preserves_behavior": "yes|no|uncertain",
  "new_risks": [],
  "comments": "string"
}
