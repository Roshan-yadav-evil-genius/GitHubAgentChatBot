from github_agent import GitHubAgent
import logging_setup as _

if __name__ == "__main__":
    agent = GitHubAgent()
    agent.run()
    agent.project_hub_agent.invoke(
        "Could you please provide a brief overview of the Auto Database Creator tool?"
    )
    agent.project_hub_agent.invoke(
        "Could you please provide a list of packages i used in Auto Database Creator tool?"
    )
    