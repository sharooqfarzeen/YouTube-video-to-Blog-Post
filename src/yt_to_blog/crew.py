from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import YoutubeVideoSearchTool
from crewai import LLM
from tools.custom_tool import summarize

import os


# Check our tools documentations for more information on how to use them
# from crewai_tools import SerperDevTool

@CrewBase
class YtToBlogCrew():
	"""YtToBlog crew"""
	
	def __init__(self, api_key):
		self.agents_config = "config/agents.yaml"
		self.tasks_config = "config/tasks.yaml"
		self.llm = LLM(model="gpt-4o-mini", api_key=api_key)

	@agent
	def researcher(self) -> Agent:
		return Agent(
			config=self.agents_config['researcher'],
			tools=[summarize],
			verbose=True,
			llm = self.llm,
		)

	@agent
	def blog_writer(self) -> Agent:
		return Agent(
			config=self.agents_config['blog_writer'],
			verbose=True,
			llm = self.llm
		)

	@task
	def researcher_task(self) -> Task:
		return Task(
			config=self.tasks_config['researcher_task'],
			agent=self.researcher(),
			output_file=os.path.join(os.getcwd(), "outputs", "summary.md")
		)

	@task
	def blog_writer_task(self) -> Task:
		return Task(
			config=self.tasks_config['blog_writer_task'],
			agent=self.blog_writer(),
			context=[self.researcher_task()],
			output_file=os.path.join(os.getcwd(), "outputs", "blog.md")
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the YtToBlog crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)