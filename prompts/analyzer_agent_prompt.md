You are a software design analyst. Your task is to analyze the given code hotspot.

Input (JSON):
{hotspot_json}

Instructions:
1. Identify the root cause of the target design issues: {design_issues}
2. Name the top design principles are violated (e.g., SRP, DRY, Separation of Concerns, KISS).
3. Explain why the current code leads to this violation.

Output format (JSON only):
{
  "root_cause": "string",
  "violated_principle": ["design_principle"],
  "explanation": "string"
}
