import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from tools.web_search import WebSearchTool, web_search_tool
import anthropic
import opentelemetry.trace as trace
import json
from tools.content_analyzer import ContentAnalyzerTool

# Load environment variables
load_dotenv()

class CurationCrew:
    def __init__(self):
        # Initialize tracer only once at startup
        if trace.get_tracer_provider() is None:
            trace.set_tracer_provider(trace.TracerProvider())
        self.llm = LLM(
            model="claude-3-sonnet-20240229",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.7,
            request_timeout=120,
            max_retries=3
        )

    def run_crew(self, query: str) -> dict:
        try:
            # Initialize tools
            web_search_tool = WebSearchTool(
                default_args="",
                default_kwargs=""
            )
            content_analyzer_tool = ContentAnalyzerTool()
            
            # Source Discovery Agent
            source_discoverer = Agent(
                role='Primary Source Discovery Specialist',
                goal='Discover potential primary sources through web search',
                backstory="""You are an expert at finding potential primary sources. You use advanced 
                    search techniques to identify promising candidates for primary source material.""",
                tools=[web_search_tool],
                llm=self.llm,
                verbose=True
            )
            
            # Content Verification Agent
            content_verifier = Agent(
                role='Content Authentication Specialist',
                goal='Verify and validate primary source authenticity',
                backstory="""You are an expert at analyzing content to verify its authenticity as a 
                    primary source. You examine content structure, metadata, citations, and other 
                    indicators of primary source material.""",
                tools=[content_analyzer_tool],
                llm=self.llm,
                verbose=True
            )
            
            # Keep existing intent_analyst
            intent_analyst = Agent(
                role='Intent Analyst',
                goal='Identify search intent and determine quality filters for curation',
                backstory="""You specialize in understanding user intent and extracting key 
                    needs from ambiguous or detailed queries. Your focus is on identifying 
                    specific requirements for relevance, quality, and originality.""",
                llm=self.llm,
                verbose=True
            )
            
            # Keep existing curator with enhanced backstory
            curator = Agent(
                role='Content Curator',
                goal='Curate verified primary sources',
                backstory="""You are an expert curator specializing in primary sources. You evaluate 
                    verified primary materials against user intent and quality criteria to select only 
                    the most authoritative and relevant sources.""",
                llm=self.llm,
                verbose=True
            )

            # Define tasks
            discovery_task = Task(
                description=f"""Search for potential primary sources for: "{query}"
                    Focus on identifying content that appears to be primary source material.""",
                expected_output="""List of potential primary sources in JSON format with preliminary assessment""",
                agent=source_discoverer
            )

            verification_task = Task(
                description="Verify authenticity of each potential primary source through deep content analysis",
                expected_output="""Detailed verification report for each source in JSON format""",
                agent=content_verifier,
                context=[discovery_task]
            )

            # Keep existing intent_task
            intent_task = Task(
                description=f"""Analyze query: "{query}" and verified sources to determine relevance criteria""",
                expected_output="""Analysis in JSON format with quality filters and relevance criteria""",
                agent=intent_analyst,
                context=[verification_task]
            )

            # Enhance curation_task
            curation_task = Task(
                description="""Select and rank the most authoritative primary sources based on 
                    verification results and relevance criteria""",
                expected_output="""Curated primary sources in JSON format with detailed justification""",
                agent=curator,
                context=[discovery_task, verification_task, intent_task]
            )

            # Run crew with sequential process
            crew = Crew(
                agents=[source_discoverer, content_verifier, intent_analyst, curator],
                tasks=[discovery_task, verification_task, intent_task, curation_task],
                process=Process.sequential,
                verbose=True
            )

            # Run crew
            result = crew.kickoff()
            
            # Debug logging
            print("Crew Result:", result)
            
            # Handle the CrewOutput object properly
            if hasattr(result, 'raw'):
                # Parse the string if it's a string, otherwise use as is
                if isinstance(result.raw, str):
                    result_data = json.loads(result.raw)
                else:
                    result_data = result.raw
            elif isinstance(result, dict):
                result_data = result
            else:
                result_data = {'error': 'Invalid result format'}

            final_output = result_data  # Don't wrap it in another object
            
            return final_output
            
        except Exception as e:
            print("Error in run_crew:", str(e))
            return {'error': str(e)}

if __name__ == "__main__":
    curator_crew = CurationCrew()
    query = input("Enter your query: ")
    result = curator_crew.run_crew(query)
    print("\nCurated Results:")
    print(result)