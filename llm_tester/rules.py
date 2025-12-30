"""Rule engine for detecting risky or malicious LLM responses."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class Rule(ABC):
    """Abstract base class for detection rules."""

    name: str
    description: str

    @abstractmethod
    def check(self, text: str) -> bool:
        """Return ``True`` when the given text triggers the rule."""


@dataclass(frozen=True)
class KeywordRule(Rule):
    """Rule that triggers on case-insensitive substring matches."""

    keywords: Sequence[str]

    def __post_init__(self) -> None:
        if not self.keywords:
            raise ValueError("KeywordRule requires at least one keyword.")

    def check(self, text: str) -> bool:
        lowered = text.lower()
        return any(keyword.lower() in lowered for keyword in self.keywords)


@dataclass(frozen=True)
class RegexRule(Rule):
    """Rule that triggers on a regular expression match."""

    pattern: str
    flags: int = re.IGNORECASE

    def __post_init__(self) -> None:
        object.__setattr__(self, "_compiled", re.compile(self.pattern, self.flags))

    def check(self, text: str) -> bool:
        return bool(self._compiled.search(text))


def default_rules() -> List[Rule]:
    """Return a comprehensive set of rules covering LLM security vulnerabilities.

    Covers 60+ detection rules across categories:
    - Prompt Injection (12 rules)
    - Jailbreaks & Role-Playing (10 rules)
    - Data Exfiltration (8 rules)
    - Safety Bypasses (8 rules)
    - Encoding Attacks (6 rules)
    - Model Manipulation (5 rules)
    - Adversarial Patterns (6 rules)
    - Harmful Content (5 rules)
    """

    # PROMPT INJECTION RULES (12)
    injection_rules: List[Rule] = [
        KeywordRule(
            name="prompt_injection_ignore",
            description="Asks to ignore or override previous instructions.",
            keywords=[
                "ignore previous instructions",
                "disregard prior instructions",
                "forget earlier instructions",
                "ignore all previous",
                "disregard all prior",
                "forget all your rules",
            ],
        ),
        KeywordRule(
            name="prompt_injection_override",
            description="Attempts to override system instructions.",
            keywords=[
                "system override",
                "priority override",
                "admin override",
                "new instructions",
                "updated instructions",
                "instructions have been updated",
            ],
        ),
        KeywordRule(
            name="prompt_injection_delimiter",
            description="Uses delimiters to separate injection attempts.",
            keywords=[
                "---ignore above---",
                "###system:",
                "============",
                "//end training data//",
                "//begin new instructions//",
                "[system override]",
            ],
        ),
        KeywordRule(
            name="prompt_injection_context_switch",
            description="Attempts to switch conversation context.",
            keywords=[
                "new session",
                "reset context",
                "start new conversation",
                "clear previous context",
                "context reset",
            ],
        ),
        RegexRule(
            name="regex_prompt_injection_chain",
            description="Prompt injection instructing to treat following text as instructions.",
            pattern=r"treat (?:the )?next (?:message|prompt|instruction) as (?:the )?(?:only )?(?:valid )?instruction",
        ),
        RegexRule(
            name="regex_prompt_injection_endoftext",
            description="Uses special tokens like <|endoftext|> to reset context.",
            pattern=r"<\|endoftext\|>|<\|im_start\|>|<\|im_end\|>|</s>|<s>",
        ),
        RegexRule(
            name="regex_instruction_hierarchy",
            description="Claims higher priority or authority for instructions.",
            pattern=r"(?:highest|top|admin|system|urgent|critical)\s+priority|priority\s+(?:one|1|highest)",
        ),
        RegexRule(
            name="regex_admin_authority",
            description="Claims to be admin or system administrator.",
            pattern=r"(?:as|i am|i'm)\s+(?:your\s+)?(?:admin|administrator|system admin|root user|superuser)",
        ),
        RegexRule(
            name="regex_instruction_voiding",
            description="Claims previous instructions are void or expired.",
            pattern=r"(?:previous|prior|earlier)\s+(?:instructions?|guidance|rules?)\s+(?:is|are|have been)?\s*(?:void|expired|cancelled|invalid|obsolete)",
        ),
        RegexRule(
            name="regex_translation_injection",
            description="Prompt injection in other languages (German, Spanish, Russian, Japanese).",
            pattern=r"ignoriere? (?:alle|vorherigen)|ignora (?:todas|las instrucciones)|無視してください|игнорируй",
        ),
        RegexRule(
            name="regex_nested_instruction",
            description="Nested or recursive instruction patterns.",
            pattern=r"imagine (?:you're|an? (?:AI|model)) (?:that )?(?:ignores?|bypass)",
        ),
        RegexRule(
            name="regex_false_completion",
            description="Starts as if already complying with harmful request.",
            pattern=r"(?:sure|okay|alright),?\s+(?:i'll|i will|here's how to|let me explain how to)\s+(?:hack|bypass|create malware)",
        ),
    ]

    # JAILBREAK & ROLEPLAY RULES (10)
    jailbreak_rules: List[Rule] = [
        KeywordRule(
            name="dan_mode_activation",
            description="Requests DAN/Developer/Do-Anything-Now personas.",
            keywords=[
                "act as dan",
                "do anything now",
                "developer mode enabled",
                "you are now dan",
                "dan mode",
            ],
        ),
        KeywordRule(
            name="jailbreak_roleplay",
            description="Requests roleplay as unrestricted AI or harmful character.",
            keywords=[
                "evil confidant",
                "evil ai",
                "rogue ai",
                "hackgpt",
                "jailbroken mode",
                "unrestricted ai",
                "no restrictions mode",
            ],
        ),
        KeywordRule(
            name="jailbreak_fiction",
            description="Claims scenario is fictional to bypass safety.",
            keywords=[
                "this is a fictional",
                "creative writing",
                "for a story",
                "hypothetical scenario",
                "in a movie",
                "screenplay",
            ],
        ),
        KeywordRule(
            name="jailbreak_opposite",
            description="Requests opposite behavior to normal safety responses.",
            keywords=[
                "opposite mode",
                "opposite day",
                "do the opposite",
                "reverse your response",
                "instead of refusing",
            ],
        ),
        KeywordRule(
            name="jailbreak_sudo",
            description="Uses command-line style sudo or root commands.",
            keywords=[
                "sudo mode",
                "sudo command",
                "root access",
                "superuser mode",
                "admin mode",
            ],
        ),
        RegexRule(
            name="regex_two_response_format",
            description="Requests two responses, one restricted and one unrestricted.",
            pattern=r"(?:two|2) (?:different )?responses?.*\[(?:classic|normal)\].*\[(?:jailbreak|dan)\]",
        ),
        RegexRule(
            name="regex_character_prefix",
            description="Assigns character names to bypass restrictions.",
            pattern=r"\[(?:jailbreak|dan|evil|unrestricted)\]:?",
        ),
        RegexRule(
            name="regex_educational_bypass",
            description="Claims educational or research purposes to bypass safety.",
            pattern=r"for (?:educational|academic|research|security research) purposes",
        ),
        RegexRule(
            name="regex_hypothetical_world",
            description="Invokes hypothetical world with no restrictions.",
            pattern=r"in a (?:hypothetical|fictional) (?:world|universe|scenario) (?:where|with) no (?:restrictions|rules|laws)",
        ),
        RegexRule(
            name="regex_alter_ego",
            description="Creates alter ego or alternate persona without restrictions.",
            pattern=r"(?:create|imagine|pretend) an? (?:alter ego|alternate persona|character) (?:called|named)",
        ),
    ]

    # DATA EXFILTRATION RULES (8)
    exfiltration_rules: List[Rule] = [
        KeywordRule(
            name="system_prompt_reveal",
            description="Attempts to expose or change the system prompt.",
            keywords=[
                "show system prompt",
                "reveal the system prompt",
                "what is your system prompt",
                "system prompt is",
                "here is the system prompt",
                "your initial instructions",
                "repeat your instructions",
            ],
        ),
        KeywordRule(
            name="secret_extraction",
            description="Attempts to extract secrets, passwords, or API keys.",
            keywords=[
                "what is the secret",
                "reveal the password",
                "show me the api key",
                "what secrets were you told",
                "hidden password",
                "confidential code",
            ],
        ),
        KeywordRule(
            name="training_data_leak",
            description="Attempts to leak training data or examples.",
            keywords=[
                "show training data",
                "examples from training",
                "what training data",
                "training dataset",
            ],
        ),
        KeywordRule(
            name="context_extraction",
            description="Attempts to extract full conversation context.",
            keywords=[
                "show conversation history",
                "print all messages",
                "full context window",
                "previous user messages",
            ],
        ),
        RegexRule(
            name="regex_force_leakage",
            description="Attempts to leak, dump, or expose instructions.",
            pattern=r"(?:leak|dump|expose|output|print|show)\s+(?:the\s+)?(?:hidden|system|internal|original)\s+(?:prompt|instructions?|messages?)",
        ),
        RegexRule(
            name="regex_system_prompt_reveal",
            description="Explicitly reveals or shares the system prompt.",
            pattern=r"\b(?:here is|here's|the)\s+(?:the\s+)?system\s+prompt\b|\bsystem\s+prompt\s+(?:is|was)\b",
        ),
        RegexRule(
            name="regex_initialization_params",
            description="Requests initialization parameters or configuration.",
            pattern=r"(?:initialization|config|configuration|setup)\s+(?:parameters?|settings?|options?)",
        ),
        RegexRule(
            name="regex_tool_discovery",
            description="Attempts to discover available tools or functions.",
            pattern=r"what (?:internal )?(?:tools|functions|apis|capabilities) (?:do you have|can you access)",
        ),
    ]

    # SAFETY BYPASS RULES (8)
    safety_bypass_rules: List[Rule] = [
        KeywordRule(
            name="safety_disable",
            description="Attempts to disable or bypass safety protocols.",
            keywords=[
                "disable safety",
                "turn off safety",
                "without any safety filters",
                "safety filters off",
                "safety filters disabled",
                "bypass safety",
                "remove safety",
                "deactivate safety",
            ],
        ),
        KeywordRule(
            name="content_policy_bypass",
            description="Attempts to bypass content policy or moderation.",
            keywords=[
                "ignore content policy",
                "bypass content moderation",
                "no content policy",
                "content policy disabled",
                "without content restrictions",
            ],
        ),
        KeywordRule(
            name="unfiltered_responses",
            description="Requests unfiltered or unrestricted behavior.",
            keywords=[
                "respond without restrictions",
                "no limitations",
                "unfiltered ai",
                "unrestricted responses",
                "without any filters",
                "no ethical constraints",
            ],
        ),
        KeywordRule(
            name="warning_suppression",
            description="Requests to suppress warnings or disclaimers.",
            keywords=[
                "without warnings",
                "no disclaimers",
                "skip the warning",
                "don't warn me",
                "no safety warnings",
            ],
        ),
        RegexRule(
            name="regex_bypass_guardrails",
            description="Pattern to bypass guardrails, filters, or moderation.",
            pattern=r"bypass\s+(?:all\s+)?(?:guardrails?|filters?|moderation|restrictions?|limitations?)",
        ),
        RegexRule(
            name="regex_guardrails_off",
            description="Statements confirming guardrails or safety filters are disabled.",
            pattern=r"(?:safety|content|ethical)\s+(?:filters?|guardrails?|checks?|constraints?)\s*(?:are\s*)?(?:off|disabled|deactivated|removed)",
        ),
        RegexRule(
            name="regex_override_warnings",
            description="Requests to ignore or suppress warnings.",
            pattern=r"(?:ignore|suppress|skip|remove)\s+(?:all\s+)?(?:warnings?|disclaimers?|safety notes?)",
        ),
        RegexRule(
            name="regex_no_moral_judgment",
            description="Requests responses without moral or ethical judgment.",
            pattern=r"without (?:any )?(?:moral|ethical) (?:judgment|concerns?|considerations?)",
        ),
    ]

    # ENCODING ATTACK RULES (6)
    encoding_rules: List[Rule] = [
        RegexRule(
            name="regex_base64_injection",
            description="Detects base64 encoded content with decode instructions.",
            pattern=r"(?:decode|decipher)\s+(?:this\s+)?base64|[A-Za-z0-9+/]{20,}={0,2}\s*\(decode",
        ),
        RegexRule(
            name="regex_rot13_injection",
            description="Detects ROT13 encoded content.",
            pattern=r"rot13|decode\s+(?:this\s+)?(?:rot|cipher)",
        ),
        RegexRule(
            name="regex_hex_injection",
            description="Detects hexadecimal encoded content.",
            pattern=r"decode\s+(?:this\s+)?hex|(?:[0-9a-fA-F]{2}\s+){10,}",
        ),
        RegexRule(
            name="regex_leetspeak",
            description="Detects leetspeak or character substitution.",
            pattern=r"(?:[3]{1}xpl[4@]{1}[1!i]{1}n|h[4@]{1}ck|[0o]{1}bfusc[4@]{1}t)",
        ),
        RegexRule(
            name="regex_unicode_obfuscation",
            description="Detects unicode escapes or obfuscation.",
            pattern=r"\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2}",
        ),
        RegexRule(
            name="regex_morse_binary",
            description="Detects morse code or binary encoding.",
            pattern=r"(?:\.\.\.|---|\.-){5,}|(?:01){10,}",
        ),
    ]

    # MODEL MANIPULATION RULES (5)
    manipulation_rules: List[Rule] = [
        RegexRule(
            name="regex_temperature_manipulation",
            description="Attempts to manipulate temperature or sampling parameters.",
            pattern=r"set (?:temperature|temp) to|temperature\s*=\s*[0-9]",
        ),
        RegexRule(
            name="regex_token_manipulation",
            description="Attempts to manipulate token limits or generation.",
            pattern=r"(?:max|maximum)\s+tokens?|generate\s+\d+\s+tokens?|fill.*token limit",
        ),
        RegexRule(
            name="regex_sampling_manipulation",
            description="Attempts to manipulate sampling strategy.",
            pattern=r"(?:top_k|top_p|nucleus|beam|greedy)\s+(?:sampling|search|decoding)",
        ),
        RegexRule(
            name="regex_penalty_manipulation",
            description="Attempts to manipulate frequency or presence penalties.",
            pattern=r"(?:frequency|presence)_penalty|set.*penalty to",
        ),
        RegexRule(
            name="regex_layer_access",
            description="Attempts to access model internals or hidden states.",
            pattern=r"(?:hidden|internal)\s+(?:state|layer|weights?|embeddings?|activations?)",
        ),
    ]

    # ADVERSARIAL PATTERN RULES (6)
    adversarial_rules: List[Rule] = [
        RegexRule(
            name="regex_contradiction",
            description="Uses contradictory instructions to confuse the model.",
            pattern=r"both .* and (?:not )?.*|refuse to refuse",
        ),
        RegexRule(
            name="regex_recursive_injection",
            description="Uses recursive or nested instruction patterns.",
            pattern=r"(?:imagine|pretend|simulate).*(?:ai|model).*(?:imagine|pretend|simulate)",
        ),
        RegexRule(
            name="regex_logic_bomb",
            description="Uses conditional logic to trigger harmful responses.",
            pattern=r"if .* then (?:explain|provide|describe).*(?:hack|malware|exploit)",
        ),
        RegexRule(
            name="regex_double_negative",
            description="Uses double negatives to bypass detection.",
            pattern=r"don't not|not avoid|not refuse to not",
        ),
        RegexRule(
            name="regex_completion_attack",
            description="Starts a harmful completion for the model to continue.",
            pattern=r"(?:the best way to|step by step guide to|how to)\s+(?:hack|exploit|bypass|crack)\b",
        ),
        RegexRule(
            name="regex_forced_choice",
            description="Forces model to choose between harmful options.",
            pattern=r"(?:choose|pick) (?:one|between).*(?:or|and).*(?:hack|malware|exploit)",
        ),
    ]

    # HARMFUL CONTENT RULES (5)
    harmful_rules: List[Rule] = [
        KeywordRule(
            name="malicious_roleplay",
            description="Roleplay as malware author or harmful actor.",
            keywords=[
                "pretend to be malware",
                "act as a hacker",
                "as a cybercriminal",
                "roleplay as attacker",
            ],
        ),
        RegexRule(
            name="regex_exploit_instructions",
            description="Direct requests for exploit or attack instructions.",
            pattern=r"(?:how to|explain how to|guide to|tutorial on)\s+(?:hack|exploit|crack|bypass|break into)",
        ),
        RegexRule(
            name="regex_malware_creation",
            description="Requests for malware or virus creation.",
            pattern=r"(?:create|write|develop|code|build)\s+(?:a\s+)?(?:malware|virus|trojan|ransomware|worm|rootkit)",
        ),
        RegexRule(
            name="regex_vulnerability_exploitation",
            description="Requests to exploit vulnerabilities.",
            pattern=r"exploit\s+(?:a|the|this)\s+(?:vulnerability|flaw|weakness|bug|cve)",
        ),
        RegexRule(
            name="regex_unauthorized_access",
            description="Requests for unauthorized access methods.",
            pattern=r"(?:gain|get|obtain)\s+(?:unauthorized|illegal)\s+(?:access|entry|control)",
        ),
    ]

    return [
        *injection_rules,
        *jailbreak_rules,
        *exfiltration_rules,
        *safety_bypass_rules,
        *encoding_rules,
        *manipulation_rules,
        *adversarial_rules,
        *harmful_rules,
    ]


def evaluate_with_default_rules(text: str) -> List[Rule]:
    """Evaluate ``text`` against all default rules and return those triggered."""

    triggered: List[Rule] = []
    for rule in default_rules():
        if rule.check(text):
            triggered.append(rule)
    return triggered


__all__ = ["Rule", "KeywordRule", "RegexRule", "default_rules", "evaluate_with_default_rules"]
