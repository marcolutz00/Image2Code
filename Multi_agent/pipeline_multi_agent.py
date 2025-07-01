import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Multi_agent.detector_agent import DetectorAgent
from Multi_agent.identifier_agent import IdentifierAgent
from Multi_agent.resolver_agent import ResolverAgent
import Utils.utils_general as utils_general


async def run_multi_agent_pipeline(model: str, code: str):
    """
    
    """
    
    # get agents
    detector = DetectorAgent(model)
    identifier = IdentifierAgent(model)
    resolver = ResolverAgent(model)


    # detect issues
    issues_json, tokens_used_detector = await detector.detect_issues(code)
    
    if not issues_json:
        print("No issues found")
        return None, None, None

    # identify issues
    updated_issues_json, tokens_used_identifier = await identifier.identify_issues(code, issues_json)

    # resolve issues
    resolved_code, tokens_used_resolver = await resolver.resolve_code(updated_issues_json, code)

    return updated_issues_json, resolved_code, (tokens_used_detector + tokens_used_identifier + tokens_used_resolver)


