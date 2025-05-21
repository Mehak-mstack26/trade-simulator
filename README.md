# Trade Simulator

Welcome to the Trade Simulator! This application allows you to simulate trading activities. It consists of a Node.js frontend and a Python backend.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Git:** [https://git-scm.com/](https://git-scm.com/)
*   **Node.js and npm:** [https://nodejs.org/](https://nodejs.org/) (LTS version recommended)
*   **Python:** [https://www.python.org/](https://www.python.org/) (Version 3.7+ recommended)
*   **Google Chrome Browser:** [https://www.google.com/chrome/](https://www.google.com/chrome/)
*   **A Free VPN Chrome Extension:** You will need to install a VPN extension from the Chrome Web Store.

## Setup and Installation

Follow these steps carefully to get the application running:

### 1. VPN Configuration (Crucial First Step)

1.  Open Google Chrome.
2.  Go to the Chrome Web Store and search for a "Free VPN" extension.
3.  Install an extension of your choice.
4.  **Connect the VPN.** Ensure it is active and connected before proceeding to the next steps.
    *   *Note: The requirement for a VPN suggests the application might be accessing geo-restricted APIs or services.*

### 2. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL_HERE>
cd trade-simulator

Replace <YOUR_REPOSITORY_URL_HERE> with the actual URL of your Git repository.
```

### 3. Frontend Setup

Open your first terminal window.

1. Navigate to the project's root directory (you should already be in trade-simulator after cloning):

```bash
# If you're not in the directory already:
# cd path/to/trade-simulator
```

2. Install the Node.js dependencies:

```bash
npm install 
or 
npm i 
```

Keep this terminal open. You will use it to run the frontend development server.

### 4. Backend Setup

Open a second (new) terminal window.

1. Navigate to the Python backend directory within the project:

```bash 
cd python
```

(Assuming your Python code is in a subdirectory named python inside trade-simulator)

2. Create a Python virtual environment. This helps manage dependencies for the project separately.

```bash 
# For macOS/Linux:
python3 -m venv venv

# For Windows:
python -m venv venv
```

(This creates a directory named venv for the virtual environment.)

3. Activate the virtual environment:

```bash 
# For macOS/Linux:
source venv/bin/activate

# For Windows:
venv\Scripts\activate
```

You should see (venv) at the beginning of your terminal prompt, indicating the environment is active.

4. Install Python dependencies (assuming you have a requirements.txt file):

```bash 
pip install -r requirements.txt
```

Keep this second terminal open. You will use it to run the Python server.

### Running the Application

Ensure your VPN is still connected.

1. Start the Python Backend Server:

    In your second terminal (where the Python virtual environment (venv) is active and you are in the trade-simulator/python directory):

```bash 
python server.py
```

Leave this terminal running. You should see output indicating the server has started (e.g., listening on a specific port like http://127.0.0.1:5000 or http://127.0.0.1:8000).

2. Start the Frontend Development Server:

    In your first terminal (where you ran npm install, in the trade-simulator root directory):

```bash 
npm run dev
```

This will typically start a development server, often on http://localhost:3000 or a similar port. The terminal will usually display the URL.

3. Access the Application:

Open your Google Chrome browser (with the VPN active) and navigate to the URL provided by the npm run dev command (e.g., http://localhost:3000).
