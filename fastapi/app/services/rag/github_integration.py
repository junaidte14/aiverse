"""
GitHub Repository Integration for RAG
"""

import os
import shutil
from typing import Optional, Dict, Any, List
from pathlib import Path
import git
from github import Github, GithubException
import validators

from app.services.rag.document_processor import DocumentProcessor


class GitHubRAGIntegration:
    """
    Handle GitHub repository integration for RAG
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        clone_base_path: str = "./data/github_repos",
    ):
        """
        Initialize GitHub integration

        Args:
            github_token: GitHub personal access token (optional for public repos)
            clone_base_path: Where to clone repositories
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.clone_base_path = Path(clone_base_path)
        self.clone_base_path.mkdir(parents=True, exist_ok=True)

        # Initialize GitHub API client
        if self.github_token:
            self.github_client = Github(self.github_token)
        else:
            self.github_client = Github()  # Anonymous (rate-limited)

    def validate_repo_url(self, repo_url: str) -> Dict[str, str]:
        """
        Validate and parse GitHub repository URL

        Args:
            repo_url: GitHub repository URL

        Returns:
            Dict with owner and repo name

        Raises:
            ValueError: If URL is invalid
        """
        if not validators.url(repo_url):
            raise ValueError("Invalid URL format")

        # Support multiple URL formats:
        # https://github.com/owner/repo
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git

        if "github.com" not in repo_url:
            raise ValueError("Not a GitHub URL")

        # Extract owner and repo
        parts = repo_url.rstrip("/").rstrip(".git").split("/")

        if "github.com" in repo_url:
            if len(parts) < 2:
                raise ValueError("Invalid GitHub URL format")

            # Handle git@ format
            if repo_url.startswith("git@"):
                # git@github.com:owner/repo
                owner_repo = parts[-1].split(":")[-1]
                owner = owner_repo.split("/")[0]
                repo = owner_repo.split("/")[1]
            else:
                # https://github.com/owner/repo
                owner = parts[-2]
                repo = parts[-1]

            return {"owner": owner, "repo": repo}

        raise ValueError("Could not parse GitHub URL")

    def get_repo_info(self, repo_url: str) -> Dict[str, Any]:
        """
        Get repository information from GitHub API

        Args:
            repo_url: GitHub repository URL

        Returns:
            Repository metadata
        """
        parsed = self.validate_repo_url(repo_url)

        try:
            repo = self.github_client.get_repo(f"{parsed['owner']}/{parsed['repo']}")

            return {
                "full_name": repo.full_name,
                "description": repo.description,
                "default_branch": repo.default_branch,
                "size": repo.size,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "is_private": repo.private,
                "last_commit_sha": repo.get_branch(repo.default_branch).commit.sha,
                "last_updated": repo.updated_at.isoformat(),
            }
        except GithubException as e:
            raise ValueError(f"GitHub API error: {e.data.get('message', str(e))}")

    def clone_or_update_repo(
        self, repo_url: str, branch: Optional[str] = None, shallow: bool = True
    ) -> Path:
        """
        Clone repository or update if already exists

        Args:
            repo_url: GitHub repository URL
            branch: Branch to clone (default: main/master)
            shallow: Shallow clone (faster, less history)

        Returns:
            Path to cloned repository
        """
        parsed = self.validate_repo_url(repo_url)
        repo_name = f"{parsed['owner']}_{parsed['repo']}"
        repo_path = self.clone_base_path / repo_name

        # Build clone URL with token for private repos
        if self.github_token and not repo_url.startswith("git@"):
            clone_url = repo_url.replace(
                "https://github.com", f"https://{self.github_token}@github.com"
            )
        else:
            clone_url = repo_url

        try:
            if repo_path.exists():
                # Update existing repository
                repo = git.Repo(repo_path)

                # Fetch latest changes
                origin = repo.remotes.origin
                origin.fetch()

                # Reset to remote branch
                if branch:
                    repo.git.checkout(branch)
                    repo.git.reset("--hard", f"origin/{branch}")
                else:
                    # Use default branch
                    default_branch = repo.active_branch.name
                    repo.git.reset("--hard", f"origin/{default_branch}")

                print(f"✅ Updated repository: {repo_path}")
            else:
                # Clone new repository
                clone_kwargs = (
                    {"depth": 1 if shallow else None, "branch": branch}
                    if branch
                    else {"depth": 1} if shallow else {}
                )

                git.Repo.clone_from(clone_url, repo_path, **clone_kwargs)
                print(f"✅ Cloned repository: {repo_path}")

            return repo_path

        except git.GitCommandError as e:
            raise RuntimeError(f"Git operation failed: {str(e)}")

    def get_last_commit_sha(self, repo_path: Path) -> str:
        """Get the latest commit SHA from local repository"""
        try:
            repo = git.Repo(repo_path)
            return repo.head.commit.hexsha
        except Exception as e:
            print(f"Error getting commit SHA: {e}")
            return ""

    def process_repository(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        file_extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[Path, List[Dict[str, Any]]]:
        """
        Clone and process repository for RAG ingestion

        Args:
            repo_url: GitHub repository URL
            branch: Branch to clone
            file_extensions: File types to include
            exclude_patterns: Patterns to exclude
            metadata: Additional metadata

        Returns:
            Tuple of (repo_path, processed_documents)
        """
        # Clone/update repository
        repo_path = self.clone_or_update_repo(repo_url, branch)

        # Get repository info
        repo_info = self.get_repo_info(repo_url)

        # Combine metadata
        full_metadata = {
            "source": "github",
            "repository": repo_info["full_name"],
            "branch": branch or repo_info["default_branch"],
            "commit_sha": self.get_last_commit_sha(repo_path),
            **(metadata or {}),
        }

        # Process documents
        processor = DocumentProcessor()

        # Default file extensions for code repositories
        if file_extensions is None:
            file_extensions = [
                ".py",
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".java",
                ".cpp",
                ".c",
                ".go",
                ".rs",
                ".rb",
                ".php",
                ".md",
                ".txt",
                ".json",
                ".yaml",
                ".yml",
                ".html",
                ".css",
                ".scss",
                ".sql",
            ]

        # Default exclusions
        default_excludes = [
            "__pycache__",
            "node_modules",
            ".git",
            "venv",
            "env",
            "dist",
            "build",
            ".cache",
            "vendor",
            "target",
            "*.min.js",
            "*.min.css",
            ".pytest_cache",
        ]
        exclude_patterns = (exclude_patterns or []) + default_excludes

        documents = processor.process_directory(
            directory=str(repo_path),
            file_extensions=file_extensions,
            exclude_patterns=exclude_patterns,
            metadata=full_metadata,
        )

        return repo_path, documents

    def cleanup_repo(self, repo_url: str) -> None:
        """Remove cloned repository"""
        try:
            parsed = self.validate_repo_url(repo_url)
            repo_name = f"{parsed['owner']}_{parsed['repo']}"
            repo_path = self.clone_base_path / repo_name

            if repo_path.exists():
                shutil.rmtree(repo_path)
                print(f"✅ Removed repository: {repo_path}")
        except Exception as e:
            print(f"Error cleaning up repository: {e}")

    def check_for_updates(self, repo_url: str, last_commit_sha: str) -> bool:
        """
        Check if repository has updates since last sync

        Args:
            repo_url: GitHub repository URL
            last_commit_sha: Last known commit SHA

        Returns:
            True if updates available
        """
        try:
            repo_info = self.get_repo_info(repo_url)
            current_sha = repo_info["last_commit_sha"]
            return current_sha != last_commit_sha
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return False
