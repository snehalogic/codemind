# CodeMind: A Full-Stack Code Analysis and Visualization Platform
CodeMind is a comprehensive platform designed to analyze and visualize codebases, providing insights into code structure, dependencies, and complexity.

## 🏗️ Architecture
The CodeMind platform consists of a Python-based backend and a JavaScript/React-based frontend. The backend is responsible for analyzing code repositories, building dependency graphs, and providing APIs for the frontend to consume. The frontend utilizes React and various libraries to visualize the code structure, dependencies, and statistics. The system architecture can be broken down into the following components:
* **Backend**: Handles code repository analysis, dependency graph construction, and API serving.
* **Frontend**: Consumes backend APIs to visualize code structure, dependencies, and statistics.
* **Database**: Not explicitly mentioned, but potentially used for storing repository metadata and analysis results.

## ⚙️ Tech Stack
The CodeMind platform employs a range of technologies, including:
* **Python**: Used for the backend, with libraries such as:
	+ `requirements.txt` for dependency management
	+ `config.py` for configuration
* **JavaScript**: Used for the frontend, with frameworks and libraries such as:
	+ React
	+ Tom Select
	+ Vis.js (for network visualization)
* **Databases**: Potential use of databases for storing repository metadata and analysis results (not explicitly mentioned)
* **Other**: Utilizes various tools and libraries, including `git` for repository cloning and analysis

## 📁 Project Structure
The project is organized into the following key folders and files:
* **Backend**:
	+ `api/`: Contains API-related code, including `main.py`
	+ `graph/`: Handles dependency graph construction and analysis
	+ `ingestion/`: Responsible for repository cloning and parsing
	+ `llm/`: Contains code for large language models (LLMs)
	+ `rag/`: Handles embedding and vector store construction
* **Frontend**:
	+ `ui/`: Contains frontend code, including `app.py` and `index.html`
	+ `lib/`: Includes various JavaScript libraries, such as Tom Select and Vis.js
* **Other**:
	+ `.gitignore`: Specifies files and folders to ignore in the Git repository
	+ `config.py`: Configuration file for the backend
	+ `requirements.txt`: Dependency management file for the backend

## 🚀 Getting Started
To get started with the CodeMind platform, follow these steps:
### Backend Setup
1. Clone the repository: `git clone https://github.com/snehalogic/codemind`
2. Install dependencies: `pip install -r requirements.txt`
3. Configure the backend: Update `config.py` with relevant settings
4. Run the backend: `python api/main.py`
### Frontend Setup
1. Clone the repository: `git clone https://github.com/snehalogic/codemind`
2. Install dependencies: `npm install` (or `yarn install`)
3. Configure the frontend: Update `ui/app.py` with relevant settings
4. Run the frontend: `npm start` (or `yarn start`)

## 📖 Usage
To use the CodeMind platform, follow these steps:
1. Clone a repository using the `clone_repo` function in `ingestion/cloner.py`
2. Analyze the repository using the `analyze` function in `api/main.py`
3. Visualize the code structure and dependencies using the frontend
Examples:
* Clone a repository: `python ingestion/cloner.py --repo https://github.com/example/repo`
* Analyze a repository: `python api/main.py --repo example/repo`

## 🔑 Environment Variables
The following environment variables are required:
* `REPO_URL`: The URL of the repository to analyze
* `BACKEND_PORT`: The port number for the backend API
* `FRONTEND_PORT`: The port number for the frontend

## 🤝 Contributing
To contribute to the CodeMind platform, follow these steps:
1. Fork the repository: `git fork https://github.com/snehalogic/codemind`
2. Create a new branch: `git branch feature/new-feature`
3. Make changes and commit: `git commit -m "Added new feature"`
4. Open a pull request: Submit a pull request to the main repository
Please ensure that all contributions adhere to the project's coding standards and best practices.