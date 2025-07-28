# finalp/1b/semanticAnalyzer.py (FIXED VERSION)

from sentence_transformers import SentenceTransformer, util
from ctransformers import AutoModelForCausalLM
from typing import List, Dict
from datetime import datetime
import os

class SemanticAnalyzer:
    def __init__(self):
        # Base directory where this file is located
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # Define absolute paths for models
        model_path = "/app/models/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
        llm_path = "/app/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model directory not found at {model_path}. Please ensure the model is downloaded."
            )

        self.ranker_model = SentenceTransformer(model_path, local_files_only=True)

        # Load quantized LLM for analysis
        llm_path = os.path.join(
            BASE_DIR,
            "models",
            "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        )
        if not os.path.exists(llm_path):
            raise FileNotFoundError(
                f"LLM model not found at {llm_path}. Please download the model."
            )

        self.llm = AutoModelForCausalLM.from_pretrained(
            llm_path,
            model_type="llama"
        )

    def rank_sections(self, sections: List[Dict], persona: str, job_to_be_done: str) -> List[Dict]:
        """Rank sections by relevance to persona and job-to-be-done."""
        if not sections:
            return []
        
        query = f"Persona: {persona}. Job: {job_to_be_done}"
        section_contents = [section['content'] for section in sections]

        print(f"🔍 Ranking {len(sections)} sections for: {query[:100]}...")

        query_embedding = self.ranker_model.encode(query, convert_to_tensor=True)
        corpus_embeddings = self.ranker_model.encode(section_contents, convert_to_tensor=True)

        cosine_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]

        for i, section in enumerate(sections):
            section['relevance_score'] = cosine_scores[i].item()

        ranked_sections = sorted(sections, key=lambda x: x['relevance_score'], reverse=True)
        for i, section in enumerate(ranked_sections):
            section['importance_rank'] = i + 1

        return ranked_sections

    def analyze_subsection(self, section_content: str, persona: str, job_to_be_done: str) -> str:
        """Generate refined text for a section using the LLM."""
        if not section_content.strip():
            return "No relevant content available."

        # Truncate content for small models (increased limit)
        section_snippet = section_content[:1500] if len(section_content) > 1500 else section_content

        prompt = f"""Analyze the following text for a {persona} who needs to: {job_to_be_done}

Text: {section_snippet}

Provide a concise summary in this format:

Summary:
- Main purpose: [one sentence]
- Key point 1: [brief bullet]  
- Key point 2: [brief bullet]
- Key point 3: [brief bullet]

Relevance: [Why this matters for the job - one sentence]
"""

        try:
            refined_text = self.llm(prompt, max_new_tokens=150, temperature=0.3)
            return refined_text.strip()
        except Exception as e:
            print(f"⚠️ LLM analysis failed: {str(e)}")
            # Fallback to simple content summary
            words = section_content.split()
            summary = " ".join(words[:50]) + "..." if len(words) > 50 else section_content
            return f"Summary: {summary}\n\nRelevance: This section contains information relevant to {job_to_be_done}."

    def generate_output(
        self,
        documents: List[str],
        persona: str,
        job_to_be_done: str,
        ranked_sections: List[Dict],
        top_n: int = 5
    ) -> Dict:
        """Generate the final JSON output with correct field names."""
        output = {
            "metadata": {
                "input_documents": documents,
                "persona": persona,
                "job_to_be_done": job_to_be_done,
                "processing_timestamp": datetime.now().isoformat()
            },
            "extracted_sections": [],
            "subsection_analysis": []  # FIXED: Changed from "sub_section_analysis"
        }

        if not ranked_sections:
            print("⚠️ No ranked sections to analyze.")
            return output

        # Take top N sections
        top_sections = ranked_sections[:top_n]
        print(f"📝 Generating output for top {len(top_sections)} ranked sections")

        for section in top_sections:
            # Add to extracted_sections
            output["extracted_sections"].append({
                "document": section["document"],
                "section_title": section["section_title"],  # FIXED: Use section_title, not page-based title
                "importance_rank": section["importance_rank"],
                "page_number": section["page_number"]
            })

            # Generate refined analysis
            refined_text = self.analyze_subsection(
                section["content"], persona, job_to_be_done
            )
            
            output["subsection_analysis"].append({
                "document": section["document"],
                "refined_text": refined_text,
                "page_number": section["page_number"]
            })

        return output

    def debug_run(self) -> Dict:
        """Test run for debugging without external inputs."""
        test_sections = [{
            "document": "sample_doc.pdf",
            "page_number": 1,
            "section_title": "Introduction to GNNs",
            "content": "Graph neural networks are a type of deep learning model used to operate on graph structures. They are increasingly applied in drug discovery tasks..."
        }]
        persona = "PhD researcher in computational biology"
        job = "Prepare a literature review focusing on methodologies, datasets, and performance benchmarks"

        ranked = self.rank_sections(test_sections, persona, job)
        return self.generate_output(["sample_doc.pdf"], persona, job, ranked)