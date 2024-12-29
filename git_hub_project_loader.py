import re
import os
import logging
import subprocess
from typing import List, Dict
from rich import print
from pathlib import Path
import shutil
from github import Github
from git import Repo
from dotenv import load_dotenv
from omegaconf import OmegaConf
from github.Repository import Repository
import logging_setup as _
from utils.loaded_project import LoadedProject
from utils.errors import MissingDescriptionError

load_dotenv()
config = OmegaConf.load("config.yaml")


class GitHubProjectLoader:
    def __init__(self, folder_to_clone: Path = Path("Github")):

        self.logger = logging.getLogger(__name__)
        self.config = config
        self.folder_to_clone = folder_to_clone.resolve()
        self.folder_to_clone.mkdir(parents=True, exist_ok=True)

        self.username = self.get_github_username_from_profile_url()
        self.api_key = os.getenv("GITHUB_TOKEN", None)
        self.github = Github(self.api_key)
        self.user = self.github.get_user(self.username)

    def get_github_username_from_profile_url(self):
        """Extracts the username from a GitHub profile URL."""
        profile_url = config.GitHub.profile_url
        match = re.search(r"github\.com/([A-Za-z0-9_-]+)", profile_url)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid GitHub URL")

    def get_repositories(self) -> List[Repository]:
        """Fetch all repositories for a user or organization."""

        allowed_repos = config.GitHub.allowed_repos
        user_repos = self.user.get_repos()

        return [repo for repo in user_repos if repo.name in allowed_repos]

    def clone_repositories(self, repos: List[Repository]) -> List[LoadedProject]:
        """Clone the repositories to the local directory."""

        loaded_projects: List[LoadedProject] = []
        for repo in repos:
            repo_name = repo.name
            clone_dir = self.folder_to_clone / repo_name
            project_info = LoadedProject(path=clone_dir, name=repo_name)
            loaded_projects.append(project_info)

            if clone_dir.exists():
                self.logger.debug(
                    f"Skipping Clonning of repository '{repo_name}', Directory already exists."
                )
                continue
            else:
                project_info.about = repo.description
                clone_dir.mkdir()

            self.clone_repo(repo, clone_dir)

            self.add_project_description(repo, clone_dir)

            self.remove_git_directory(repo, clone_dir)

        return loaded_projects

    def clone_repo(self, repo: Repository, clone_dir: Path):
        """Clone a repository from a URL to a directory."""
        try:
            self.logger.info(f"Cloning repository '{repo.name}' from {repo.clone_url} into '{clone_dir}'...")
            Repo.clone_from(repo.clone_url, clone_dir)

            self.logger.debug(
                f"Cloned repository '{repo.name}' from {repo.clone_url} into '{clone_dir}'."
            )
        except Exception as e:
            self.logger.error(f"Error cloning repository: {e}")

    def remove_git_directory(self, repo: Repository, clone_dir: Path):
        """Remove the .git directory from the cloned repository."""
        self.logger.debug(
            f"Removing .git directory from cloned {repo.name} repository."
        )
        git_dir = clone_dir / ".git"
        if git_dir.exists():
            try:
                shutil.rmtree(git_dir)
                self.logger.debug(f"Removed .git directory from {clone_dir}.")
            except PermissionError as e:
                self.logger.error(
                    f"Permission denied while removing .git directory: {e}"
                )
            except Exception as e:
                self.logger.error(f"Error removing .git directory: {e}")
        else:
            self.logger.debug(f"No .git directory found in {clone_dir}.")

    def add_project_description(self, repo: Repository, clone_dir: Path):
        self.logger.debug(
            f"Adding project description in cloned {repo.name} repository."
        )
        if repo.description:
            description_file_path = clone_dir / "project.description"
            with open(description_file_path, "w") as description_file:
                description_file.write(repo.description)
                self.logger.debug(
                    f"Created {description_file_path} with the description."
                )
        else:
            raise MissingDescriptionError(
                f"A project description is essential for optimal results from the agent. Please add a description in the repository at {repo.clone_url} to continue."
            )

    def load_projects(self) -> List[LoadedProject]:
        repos = self.get_repositories()
        return self.clone_repositories(repos)


if __name__ == "__main__":
    obj = GitHubProjectLoader()
    project_paths = obj.load_projects()
    print(f"{project_paths=}")
