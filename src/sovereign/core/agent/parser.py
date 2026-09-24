"""Dependency-free JSON extraction and parsing for agent decisions."""

import json
import re
from sovereign.core.agent.models import AgentDecision

class ModelOutputParser:
    @staticmethod
    def parse_decision(raw_output: str) -> AgentDecision:
        """
        Parses UNTRUSTED model output into a validated AgentDecision.
        Strips markdown ticks if present.
        Raises ValueError if parsing/validation fails.
        """
        text = raw_output.strip()
        
        # Attempt to extract JSON block if wrapped in markdown
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
        else:
            # Maybe it starts with { and ends with }
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and start < end:
                text = text[start:end+1]
                
        # Pre-process triple-quoted strings inside JSON: `"code": """..."""`
        def _sanitize_triple_quotes(s: str) -> str:
            def repl(m):
                inner = m.group(1)
                escaped = json.dumps(inner)
                return f': {escaped}'
            return re.sub(r':\s*"""([\s\S]*?)"""', repl, s)

        text = _sanitize_triple_quotes(text)

        data = None
        try:
            data = json.loads(text, strict=False)
        except json.JSONDecodeError:
            # Attempt string newline escaping
            def _escape_string_newlines(s_input: str) -> str:
                result = []
                in_string = False
                escape = False
                for char in s_input:
                    if char == '"' and not escape:
                        in_string = not in_string
                        result.append(char)
                    elif in_string:
                        if char == '\n':
                            result.append('\\n')
                        elif char == '\r':
                            result.append('\\r')
                        elif char == '\t':
                            result.append('\\t')
                        else:
                            result.append(char)
                    else:
                        result.append(char)
                    if char == '\\' and not escape:
                        escape = True
                    else:
                        escape = False
                return "".join(result)

            try:
                sanitized = _escape_string_newlines(text)
                data = json.loads(sanitized, strict=False)
            except Exception:
                # Attempt code block repair
                start_idx = text.find('"code"')
                if start_idx != -1:
                    val_start = text.find(':', start_idx) + 1
                    while val_start < len(text) and text[val_start] in ' \t\r\n':
                        val_start += 1
                    if val_start < len(text) and text[val_start] in ('"', "'"):
                        quote_char = text[val_start]
                        val_start += 1
                        if text[val_start:val_start+2] == quote_char * 2:
                            val_start += 2
                        
                        next_prop_match = re.search(r',\s*"[a-zA-Z0-9_]+"\s*:', text[val_start:])
                        close_brace_match = re.search(r'\s*\}', text[val_start:])
                        
                        if next_prop_match:
                            end_pos = val_start + next_prop_match.start()
                        elif close_brace_match:
                            end_pos = val_start + close_brace_match.start()
                        else:
                            end_pos = None

                        if end_pos is not None:
                            code_content = text[val_start:end_pos].rstrip(' \t\r\n')
                            if code_content.endswith('"""') or code_content.endswith("'''"):
                                code_content = code_content[:-3]
                            elif code_content.endswith('"') or code_content.endswith("'"):
                                code_content = code_content[:-1]
                            escaped_code = json.dumps(code_content.strip())
                            repaired = text[:text.find(':', start_idx) + 1] + " " + escaped_code + text[end_pos:]
                            try:
                                data = json.loads(repaired, strict=False)
                            except Exception:
                                pass
            
        if data is None:
            try:
                data = json.loads(text)
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed JSON: {e}")
            
        try:
            decision = AgentDecision(**data)
            if decision.arguments and isinstance(decision.arguments, dict) and "code" in decision.arguments:
                code_val = decision.arguments["code"]
                if isinstance(code_val, str):
                    code_val = code_val.replace('\\"', '"').replace("\\'", "'")
                    if "\n" not in code_val and "\\n" in code_val:
                        code_val = code_val.replace("\\n", "\n").replace("\\t", "\t")
                    # Repair unclosed single line quotes
                    lines = code_val.split("\n")
                    fixed_lines = []
                    for line in lines:
                        stripped = line.rstrip()
                        if stripped.count('"""') % 2 == 0 and stripped.count("'''") % 2 == 0:
                            if stripped.count('"') % 2 == 1:
                                line = line + '"'
                            elif stripped.count("'") % 2 == 1:
                                line = line + "'"
                        fixed_lines.append(line)
                    decision.arguments["code"] = "\n".join(fixed_lines)
            return decision
        except Exception as e:
            raise ValueError(f"AgentDecision schema validation failed: {e}")
