#!/usr/bin/env bash
# Re-clone the surveyed repository heads and print the evidence lines cited in survey_repos.md.
set -u; mkdir -p survey && cd survey
for r in hch-wang/Negative_Knowledge WecoAI/aideml SakanaAI/AI-Scientist-v2 codelion/openevolve google-deepmind/funsearch MineDojo/Voyager SamuelSchmidgall/AgentLaboratory SakanaAI/AI-Scientist; do
  n=$(basename $r); [ -d $n ] || git clone -q --depth 1 https://github.com/$r $n; done
grep -n "is_buggy" aideml/aide/journal.py | head -3; sed -n '172,181p' aideml/aide/agent.py
grep -n "debug_prob\|max_debug_depth" AI-Scientist-v2/bfts_config.yaml
sed -n '96,113p' openevolve/openevolve/prompt/templates.py; sed -n '154,155p' funsearch/implementation/evaluator.py
sed -n '205p' Voyager/voyager/agents/curriculum.py; grep -n "will not replace" AgentLaboratory/mlesolver.py | head -2
sed -n '53,60p' AI-Scientist/ai_scientist/perform_experiments.py
